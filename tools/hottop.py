"""Interface with the hottop roaster."""

import glob
import logging
import serial
import sys
import time
from multiprocessing import Process, Manager, Event


class InvalidInput(Exception):
    """Exception to capture invalid input commands."""
    pass


class SerialConnectionError(Exception):
    """Exception to capture serial connection issues."""
    pass


def bool2int(bool):
    """Convert a bool to an int."""
    if bool:
        return 1
    else:
        return 0


class ControlProcess(Process):

    """Primary processor to communicate with the hottop directly."""

    def __init__(self, conn, config, logger):
        """Inherit from the base."""
        super(ControlProcess, self).__init__()
        self._conn = conn
        self._log = logger
        self._config = config

        # Trigger events used in the core loop.
        self.cooldown = Event()
        self.exit = Event()

    def get_config(self):
        """Get the current configuration."""
        config = bytearray([0x00]*36)
        config[0] = 0xA5
        config[1] = 0x96
        config[2] = 0xB0
        config[3] = 0xA0
        config[4] = 0x01
        config[5] = 0x01
        config[6] = 0x24
        config[10] = self._config.get('heater', 0)  # HEATER (0-100)
        config[11] = self._config.get('fan', 0)  # FAN (0-10)
        config[12] = self._config.get('main_fan', 0)  # MAIN_FAN (0-10)
        config[16] = self._config.get('solenoid', 0)  # SOLENOID (0 or 1)
        config[17] = self._config.get('drum_motor', 0)  # DRUM MOTOR (0 or 1)
        config[18] = self._config.get('cooling_motor', 0)  # COOLING MOTOR (0 or 1)
        config[35] = sum([b for b in config[:35]]) & 0xFF  # CHECKSUM
        return bytes(config)

    def send_config(self):
        """Send configuration data to the hottop."""
        serialized = self.get_config()
        self._log.debug("Configuration has been serialized")
        try:
            self._conn.flushInput()
            self._conn.flushOutput()
            self._conn.write(serialized)
            return True
        except Exception as e:
            self._log.error(e)
            raise Exception(e)

    def read_settings():
        """Read the information from the Hottop."""
        return

    def run(self):
        """Run the core loop."""
        while not self.exit.is_set():
            if self.cooldown.is_set():
                self._log.debug("Cool down process triggered")
                self._config['drum_motor'] = 0
                self._config['heater'] = 0
                self._config['solenoid'] = 1
                self._config['cooling_motor'] = 1
                self._config['main_fan'] = 10

            self.send_config()
            self._log.debug(self._config)
            time.sleep(self._config['interval'])

    def drop(self):
        """Drop the coffee for cooling."""
        self._log.debug("Dropping the coffee")
        self.cooldown.set()

    def shutdown(self):
        """Register a shutdown event."""
        self._log.debug("Shutdown initiated")
        self.exit.set()


class Hottop:

    """Object to interact and control the hottop roaster."""

    NAME = "HOTTOP"
    USB_PORT = "/dev/cu.usbserial-DA01PEYC"
    BAUDRATE = 115200
    BYTE_SIZE = 8
    PARITY = "N"
    STOPBITS = 1
    TIMEOUT = 1
    LOG_LEVEL = logging.DEBUG
    INTERVAL = 0.5

    def __init__(self):
        """Start of the hottop."""
        self._log = self._logger()
        self._conn = self._connect()
        self._manager = Manager()
        self._init_controls()

    def _logger(self):
        """Build a logger to use inside of the class."""
        logger = logging.getLogger(self.NAME)
        logger.setLevel(self.LOG_LEVEL)
        shandler = logging.StreamHandler(sys.stdout)
        fmt = '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
        fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
        shandler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(shandler)
        return logger

    def _autodiscover_usb(self):
        """Try and find the serial adapter for the hottop."""
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/cu.*')
        else:
            raise EnvironmentError('Unsupported platform')

        match = None
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                if (port.find("/dev/cu.usbserial-") > -1 and
                        port.find('bluetooth') == -1):
                    self.USB_PORT = port
                    match = port
                    break
            except (OSError, serial.SerialException):
                pass
        return match

    def _connect(self):
        """Connect to the USB for the hottop."""
        match = self._autodiscover_usb()
        self._log.debug("Auto-discovered USB port: %s" % match)
        try:
            conn = serial.Serial(self.USB_PORT, baudrate=self.BAUDRATE,
                                 bytesize=self.BYTE_SIZE, parity=self.PARITY,
                                 stopbits=self.STOPBITS, timeout=self.TIMEOUT)
        except serial.serialutil.SerialException as e:
            raise SerialConnectionError(str(e))

        self._log.debug("Serial connection set")
        if not conn.isOpen():
            conn.open()
            self._log.debug("Serial connection opened")
        return conn

    def _init_controls(self):
        """Establish a set of base controls the user can influence."""
        self._config = self._manager.dict()
        self._config['heater'] = 0
        self._config['fan'] = 0
        self._config['main_fan'] = 0
        self._config['drum_motor'] = 0
        self._config['solenoid'] = 0
        self._config['cooling_motor'] = 0
        self._config['interval'] = self.INTERVAL

    def start(self):
        """Start the roaster process."""
        self._process = ControlProcess(self._conn, self._config, self._log)
        self._process.start()

    def end(self):
        """End the roaster process."""
        self._process.shutdown()

    def drop(self):
        """Preset call to drop coffee from the roaster."""
        self._process.drop()

    def set_interval(self, interval):
        """Set the polling interval for the process thread."""
        if type(interval) != float or type(interval) != int:
            raise InvalidInput("Interval value must be of float or int")
        self._config['interval']

    def get_heater(self):
        """Get the heater config."""
        return self._config['heater']

    def set_heater(self, heater):
        """Set the heater config."""
        if type(heater) != int and heater not in range(0, 101):
            raise InvalidInput("Heater value must be int between 0-100")
        self._config['heater'] = heater

    def get_fan(self):
        """Get the fan config."""
        return self._config['fan']

    def set_fan(self, fan):
        """Set the fan config."""
        if type(fan) != int and fan not in range(0, 11):
            raise InvalidInput("Fan value must be int between 0-10")
        self._config['fan'] = fan

    def get_main_fan(self):
        """Get the main fan config."""
        return self._config['main_fan']

    def set_main_fan(self, main_fan):
        """Set the main fan config."""
        if type(main_fan) != int and main_fan not in range(0, 11):
            raise InvalidInput("Main fan value must be int between 0-10")
        self._config['main_fan'] = main_fan

    def get_drum_motor(self):
        """Get the drum motor config."""
        return self._config['drum_motor']

    def set_drum_motor(self, drum_motor):
        """Set the drum motor config."""
        if type(drum_motor) != bool:
            raise InvalidInput("Drum motor value must be bool")
        self._config['drum_motor'] = bool2int(drum_motor)

    def get_solenoid(self):
        """Get the solenoid config."""
        return self._config['solenoid']

    def set_solenoid(self, solenoid):
        """Set the solenoid config."""
        if type(solenoid) != bool:
            raise InvalidInput("Solenoid value must be bool")
        self._config['solenoid'] = bool2int(solenoid)

    def get_cooling_motor(self):
        """Get the cooling motor config."""
        return self._config['cooling_motor']

    def set_cooling_motor(self, cooling_motor):
        """Set the cooling motor config."""
        if type(cooling_motor) != bool:
            raise InvalidInput("Cooling motor value must be bool")
        self._config['cooling_motor'] = bool2int(cooling_motor)


def main():
    """Test the class."""
    ht = Hottop()
    ht.start()
    time.sleep(3)
    ht.drop()
    time.sleep(5)
    ht.end()

if __name__ == '__main__':
    main()
