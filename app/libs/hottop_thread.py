#!/usr/bin/env python
"""
Interface with the hottop roaster through the serial port.

This module is split into two pieces, a controlling thread for monitoring
data from the serial interface and a user-facing object to adjust settings or
read content back out. It's NOT recommended to conduct roasting with this
interface alone. Instead, it should be paired with a visual interface to avoid
running the risk of fire, or damage. This code is provided as-is and the
author is not responsible for any negative consequences for using the module.

Marko Luther is listed in the credits here for his amazing work on Artisan. His
application originally inspired the creation of this module and was helpful for
understanding how to interface with the Hottop roaster serial interface.
"""
__author__ = "Brandon Dixon"
__copyright__ = "Copyright, Split Key Coffee"
__credits__ = ["Brandon Dixon", "Marko Luther"]
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = "Brandon Dixon (brandon@splitkeycoffee.com)"
__email__ = "info@splitkeycoffee.com"
__status__ = "BETA"

import binascii
import copy
import datetime
import glob
import logging
import serial
import sys
import time

from .mock import MockProcess

py2 = sys.version[0] == '2'

if py2:
    from Queue import Queue
else:
    from queue import Queue

from threading import Thread, Event


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


def hex2int(value):
    """Convert hex to an int."""
    return int(binascii.hexlify(value), 16)


def celsius2fahrenheit(c):
    """Convert temperatures."""
    return (c * 1.8) + 32


def now_time(str=False):
    """Get the current time."""
    if str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now()


def now_date(str=False):
    """Get the current date."""
    if str:
        return datetime.datetime.now().strftime("%Y-%m-%d")
    return datetime.date.today()


def load_time(str_time):
    """Convert the date string to a real datetime."""
    return datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")


def timedelta2millisecond(td):
    """Get milliseconds from a timedelta."""
    milliseconds = td.days * 24 * 60 * 60 * 1000
    milliseconds += td.seconds * 1000
    milliseconds += td.microseconds / 1000
    return milliseconds


def timedelta2period(duration):
    """Convert timedelta to different formats."""
    seconds = duration.seconds
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return '{0:0>2}:{1:0>2}'.format(minutes, seconds)


class ControlProcess(Thread):

    """Primary processor to communicate with the hottop directly.

    :param conn: Established serial connection to the Hottop
    :type conn: Serial instance
    :param config: Initial configurations settings
    :type config: dict
    :param q: Shared queue to interact with the user interface
    :type q: Queue instance
    :param logger: Shared logger to keep continuity
    :type logger: Logging instance
    :param callback: Optional callback function to stream results
    :type callback: function
    :returns: ControlProces instance
    """

    def __init__(self, conn, config, q, logger, callback=None):
        """Extend threads to support more control logic."""
        Thread.__init__(self)
        self._conn = conn
        self._log = logger
        self._config = config
        self._q = q
        self._cb = callback
        self._retry_count = 0

        # Trigger events used in the core loop.
        self.cooldown = Event()
        self.exit = Event()

    def _generate_config(self):
        """Generate a configuration that can be sent to the Hottop roaster.

        Configuration settings need to be represented inside of a byte array
        that is then written to the serial interface. Much of the configuration
        is static, but control settings are also included and pulled from the
        shared dictionary.

        :returns: Byte array of the prepared configuration.
        """
        config = bytearray([0x00]*36)
        config[0] = 0xA5
        config[1] = 0x96
        config[2] = 0xB0
        config[3] = 0xA0
        config[4] = 0x01
        config[5] = 0x01
        config[6] = 0x24
        config[10] = self._config.get('heater', 0)
        config[11] = self._config.get('fan', 0)
        config[12] = self._config.get('main_fan', 0)
        config[16] = self._config.get('solenoid', 0)
        config[17] = self._config.get('drum_motor', 0)
        config[18] = self._config.get('cooling_motor', 0)
        config[35] = sum([b for b in config[:35]]) & 0xFF
        return bytes(config)

    def _send_config(self):
        """Send configuration data to the hottop.

        :returns: bool
        :raises: Generic exceptions if an error is identified.
        """
        serialized = self._generate_config()
        self._log.debug("Configuration has been serialized")
        try:
            self._conn.flushInput()
            self._conn.flushOutput()
            self._conn.write(serialized)
            return True
        except Exception as e:
            self._log.error(e)
            raise Exception(e)

    def _validate_checksum(self, buffer):
        """Validate the buffer response against the checksum.

        When reading the serial interface, data will come back in a raw format
        with an included checksum process.

        :returns: bool
        """
        self._log.debug("Validating the buffer")
        if len(buffer) == 0:
            self._log.debug("Buffer was empty")
            if self._conn.isOpen():
                self._log.debug('Closing connection')
                self._conn.close()
            return False
        p0 = hex2int(buffer[0])
        p1 = hex2int(buffer[1])
        checksum = sum([hex2int(c) for c in buffer[:35]]) & 0xFF
        p35 = hex2int(buffer[35])
        if p0 != 165 or p1 != 150 or p35 != checksum:
            self._log.debug("Buffer checksum was not valid")
            return False
        return True

    def _read_settings(self, retry=True):
        """Read the information from the Hottop.

        Read the settings from the serial interface and convert them into a
        human-readable format that can be shared back to the end-user. Reading
        from the serial interface will occasionally produce strange results or
        blank reads, so a retry process has been built into the function as a
        recursive check.

        :returns: dict
        """
        if not self._conn.isOpen():
            self._log.debug("Reopening connection")
            self._conn.open()
        self._conn.flushInput()
        self._conn.flushOutput()
        buffer = self._conn.read(36)
        if len(buffer) != 36:
            self._log('Buffer length did not match 36')
            if self._conn.isOpen():
                self._log.debug('Closing connection')
                self._conn.close()
                self._read_settings(retry=True)

        check = self._validate_checksum(buffer)
        if not check and (retry and self._retry_count <= 3):
            if self._retry_count == 3:
                self._log.debug('Retry count reached on buffer check')
                self._read_settings(retry=False)
            else:
                self._retry_count += 1
                self._read_settings(retry=True)

        settings = dict()
        settings['heater'] = hex2int(buffer[10])
        settings['fan'] = hex2int(buffer[11])
        settings['main_fan'] = hex2int(buffer[12])
        et = hex2int(buffer[23] + buffer[24])
        settings['environment_temp'] = celsius2fahrenheit(et)
        bt = hex2int(buffer[25] + buffer[26])
        settings['bean_temp'] = celsius2fahrenheit(bt)
        settings['solenoid'] = hex2int(buffer[16])
        settings['drum_motor'] = hex2int(buffer[17])
        settings['cooling_motor'] = hex2int(buffer[18])
        settings['chaff_tray'] = hex2int(buffer[19])
        self._retry_count = 0
        return settings

    def _wake_up(self):
        """Wake the machine up to avoid race conditions.

        When first interacting with the Hottop, the machine may not wake up
        right away which can put our reader into a death loop. This wake up
        routine ensures we prime the roaster with some data before starting
        our main loops to read/write data.

        :returns: None
        """
        for range in (0, 10):
            self._send_config()
            time.sleep(self._config['interval'])

    def run(self):
        """Run the core loop of reading and writing configurations.

        This is where all the roaster magic occurs. On the initial run, we
        prime the roaster with some data to wake it up. Once awoke, we check
        our shared queue to identify if the user has passed any updated
        configuration. Once checked, start to read and write to the Hottop
        roaster as long as the exit signal has not been set. All steps are
        repeated after waiting for a specific time interval.

        There are also specialized routines built into this function that are
        controlled via events. These events are unique to the roasting process
        and pre-configure the system with a configuration, so the user doesn't
        need to do it themselves.

        :returns: None
        """
        self._wake_up()

        while not self._q.empty():
            self._config = self._q.get()

        while not self.exit.is_set():
            settings = self._read_settings()
            self._cb(settings)

            if self.cooldown.is_set():
                self._log.debug("Cool down process triggered")
                self._config['drum_motor'] = 0
                self._config['heater'] = 0
                self._config['solenoid'] = 1
                self._config['cooling_motor'] = 1
                self._config['main_fan'] = 10

            self._send_config()
            time.sleep(self._config['interval'])

    def drop(self):
        """Register a drop event to begin the cool-down process.

        :returns: None
        """
        self._log.debug("Dropping the coffee")
        self.cooldown.set()

    def shutdown(self):
        """Register a shutdown event to stop interacting with the Hottop.

        :returns: None
        """
        self._log.debug("Shutdown initiated")
        self.exit.set()


class Hottop:

    """Object to interact and control the hottop roaster.

    :returns: Hottop instance
    """

    NAME = "HOTTOP"
    USB_PORT = "/dev/cu.usbserial-DA01PEYC"
    BAUDRATE = 115200
    BYTE_SIZE = 8
    PARITY = "N"
    STOPBITS = 1
    TIMEOUT = 1
    LOG_LEVEL = logging.DEBUG
    INTERVAL = 1

    def __init__(self):
        """Start of the hottop."""
        self._log = self._logger()
        self._conn = None
        self._roast = dict()
        self._roasting = False
        self._roast_start = None
        self._roast_end = None
        self._config = dict()
        self._q = Queue()
        self._init_controls()

    def _logger(self):
        """Create a logger to be used between processes.

        :returns: Logging instance.
        """
        logger = logging.getLogger(self.NAME)
        logger.setLevel(self.LOG_LEVEL)
        shandler = logging.StreamHandler(sys.stdout)
        fmt = '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
        fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
        shandler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(shandler)
        return logger

    def _autodiscover_usb(self):
        """Attempt to find the serial adapter for the hottop.

        This will loop over the USB serial interfaces looking for a connection
        that appears to match the naming convention of the Hottop roaster.

        :returns: string
        """
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

    def connect(self, interface=None):
        """Connect to the USB for the hottop.

        Attempt to discover the USB port used for the Hottop and then form a
        connection using the serial library.

        :returns: bool
        :raises SerialConnectionError:
        """
        if not interface:
            match = self._autodiscover_usb()
            self._log.debug("Auto-discovered USB port: %s" % match)
        else:
            self.USB_PORT = interface

        try:
            self._conn = serial.Serial(self.USB_PORT, baudrate=self.BAUDRATE,
                                       bytesize=self.BYTE_SIZE,
                                       parity=self.PARITY,
                                       stopbits=self.STOPBITS,
                                       timeout=self.TIMEOUT)
        except serial.serialutil.SerialException as e:
            raise SerialConnectionError(str(e))

        self._log.debug("Serial connection set")
        if not self._conn.isOpen():
            self._conn.open()
            self._log.debug("Serial connection opened")
        return True

    def _init_controls(self):
        """Establish a set of base controls the user can influence.

        :returns: None
        """
        self._config['heater'] = 0
        self._config['fan'] = 0
        self._config['main_fan'] = 0
        self._config['drum_motor'] = 0
        self._config['solenoid'] = 0
        self._config['cooling_motor'] = 0
        self._config['interval'] = self.INTERVAL
        self._config['environment_temp'] = 0
        self._config['bean_temp'] = 0
        self._config['chaff_tray'] = 1

        self._roast['name'] = None
        self._roast['input_weight'] = -1
        self._roast['output_weight'] = -1
        self._roast['operator'] = None
        self._roast['start_time'] = None
        self._roast['end_time'] = None
        self._roast['duration'] = -1
        self._roast['notes'] = None
        self._roast['events'] = list()
        self._roast['last'] = dict()
        self._roast['record'] = False

    def _callback(self, data):
        """Processor callback to clean-up stream data.

        This function provides a hook into the output stream of data from the
        controller processing thread. Hottop readings are saved into a local
        class variable for later saving. If the user has defined a callback, it
        will be called within this private function.

        :param data: Information from the controller process
        :type data: dict
        :returns: None
        """
        local = copy.deepcopy(data)
        output = dict()
        output['config'] = local
        if self._roast_start:
            td = (now_time() - load_time(self._roast_start))
            # Seconds since starting
            output['time'] = ((td.total_seconds() + 60) / 60) - 1
            self._roast['duration'] = output['time']
            local.update({'time': output['time']})
            ct = load_time(now_time(str=True))
            st = load_time(self._roast['start_time'])
            self._roast['duration'] = timedelta2period(ct - st)

        if self._roast['record']:
            self._roast['events'].append(copy.deepcopy(output))
            self._roast['last'] = local

        if self._user_callback:
            self._log.debug("Passing data back to client handler")
            output['roast'] = self._roast
            output['roasting'] = self._roasting
            self._user_callback(output)

    def start(self, func=None):
        """Start the roaster control process.

        This function will kick off the processing thread for the Hottop and
        register any user-defined callback function. By default, it will not
        begin collecting any reading information or saving it. In order to do
        that users, must issue the monitor/record bit via `set_monitor`.

        :param func: Callback function for Hottop stream data
        :type func: function
        :returns: None
        """
        self._user_callback = func
        # self._process = ControlProcess(self._conn, self._config, self._q,
        #                                self._log, callback=self._callback)
        self._process = MockProcess(self._config, self._q,
                                    self._log, callback=self._callback)
        self._process.start()
        self._roasting = True

    def end(self):
        """End the roaster control process via thread signal.

        This simply sends an exit signal to the thread, and shuts it down. In
        order to stop monitoring, call the `set_monitor` method with false.

        :returns: None
        """
        self._process.shutdown()
        self._roasting = False
        self._roast['date'] = now_date(str=True)

    def drop(self):
        """Preset call to drop coffee from the roaster via thread signal.

        This will set the following configuration on the roaster:
        - drum_motor = 0
        - heater = 0
        - solenoid = 1
        - cooling_motor = 1
        - main_fan = 10

        In order to power-off the roaster after dropping coffee, it's best to
        use the shutdown method. It's assumed that cooling will occur for 5-10
        minutes before shutting down.

        :returns: None
        """
        self._process.drop()

    def reset(self):
        """Reset the internal roast properties.

        :returns: None
        """
        self._roasting = False
        self._roast_start = None
        self._roast_end = None
        self._roast = dict()
        self._init_controls()

    def add_roast_event(self, event):
        """Add an event to the roast log.

        This method should be used for registering events that may be worth
        tracking like first crack, second crack and the dropping of coffee.
        Similar to the standard reading output from the roaster, manually
        created events will include the current configuration reading, time and
        metadata passed in.

        :param event: Details describing what happened
        :type event: dict
        :returns: dict
        """
        event.update({'time': self.get_roast_time(),
                      'config': self.get_roast_properties()['last']})
        self._roast['events'].append(event)
        return self.get_roast_properties()

    def get_roast(self):
        """Get the roast information.

        :returns: list
        """
        return self._roast

    def get_roast_time(self):
        """Get the roast time.

        :returns: float
        """
        td = (now_time() - load_time(self._roast_start))
        return ((td.total_seconds() + 60) / 60) - 1

    def get_serial_state(self):
        """Get the state of the USB connection.

        :returns: dict
        """
        if not self._conn:
            return False
        return self._conn.isOpen()

    def get_current_config(self):
        """Get the current running config and state.

        :returns: dict
        """
        return {
            'state': self.get_serial_state(),
            'settings': dict(self._config)
        }

    def set_interval(self, interval):
        """Set the polling interval for the process thread.

        :param interval: How often to poll the Hottop
        :type interval: int or float
        :returns: None
        :raises: InvalidInput
        """
        if type(interval) != float or type(interval) != int:
            raise InvalidInput("Interval value must be of float or int")
        self._config['interval']

    def get_roast_properties(self):
        """Get the roast properties.

        :returns: dict
        """
        return self._roast

    def set_roast_properties(self, settings):
        """Set the properties of the roast.

        :param settings: General settings for the roast setup
        :type settings: dict
        :returns: None
        :raises: InvalidInput
        """
        if type(settings) != dict:
            raise InvalidInput("Properties value must be of dict")
        valid = ['name', 'input_weight', 'output_weight', 'operator', 'notes',
                 'coffee']
        for key, value in settings.iteritems():
            if key not in valid:
                continue
            self._roast[key] = value

    def get_monitor(self):
        """Get the monitor config.

        :returns: None
        """
        return self._roast['record']

    def set_monitor(self, monitor):
        """Set the monitor config.

        This module assumes that users will connect to the roaster and get
        reading information _before_ they want to begin collecting roast
        details. This method is critical to enabling the collection of roast
        information and ensuring it gets saved in memory.

        :param monitor: Value to set the monitor
        :type monitor: bool
        :returns: None
        :raises: InvalidInput
        """
        if type(monitor) != bool:
            raise InvalidInput("Monitor value must be bool")
        self._roast['record'] = bool2int(monitor)
        self._q.put(self._config)

        if self._roast['record']:
            self._roast_start = now_time(str=True)
            self._roast['start_time'] = self._roast_start
        else:
            self._roast_end = now_time(str=True)
            self._roast['end_time'] = self._roast_end
            self._roast['date'] = now_date(str=True)
            et = load_time(self._roast['end_time'])
            st = load_time(self._roast['start_time'])
            self._roast['duration'] = timedelta2period(et - st)
        return self.get_roast_properties()

    def get_heater(self):
        """Get the heater config.

        :returns: int [0-100]
        """
        return self._config['heater']

    def set_heater(self, heater):
        """Set the heater config.

        :param heater: Value to set the heater
        :type heater: int [0-100]
        :returns: None
        :raises: InvalidInput
        """
        if type(heater) != int and heater not in range(0, 101):
            raise InvalidInput("Heater value must be int between 0-100")
        self._config['heater'] = heater
        self._q.put(self._config)

    def get_fan(self):
        """Get the fan config.

        :returns: int [0-10]
        """
        return self._config['fan']

    def set_fan(self, fan):
        """Set the fan config.

        :param fan: Value to set the fan
        :type fan: int [0-10]
        :returns: None
        :raises: InvalidInput
        """
        if type(fan) != int and fan not in range(0, 11):
            raise InvalidInput("Fan value must be int between 0-10")
        self._config['fan'] = fan
        self._q.put(self._config)

    def get_main_fan(self):
        """Get the main fan config.

        :returns: None
        """
        return self._config['main_fan']

    def set_main_fan(self, main_fan):
        """Set the main fan config.

        :param main_fan: Value to set the main fan
        :type main_fan: int [0-10]
        :returns: None
        :raises: InvalidInput
        """
        if type(main_fan) != int and main_fan not in range(0, 11):
            raise InvalidInput("Main fan value must be int between 0-10")
        self._config['main_fan'] = main_fan
        self._q.put(self._config)

    def get_drum_motor(self):
        """Get the drum motor config.

        :returns: None
        """
        return self._config['drum_motor']

    def set_drum_motor(self, drum_motor):
        """Set the drum motor config.

        :param drum_motor: Value to set the drum motor
        :type drum_motor: bool
        :returns: None
        :raises: InvalidInput
        """
        if type(drum_motor) != bool:
            raise InvalidInput("Drum motor value must be bool")
        self._config['drum_motor'] = bool2int(drum_motor)
        self._log.debug(self._config)
        self._q.put(self._config)

    def get_solenoid(self):
        """Get the solenoid config.

        :returns: None
        """
        return self._config['solenoid']

    def set_solenoid(self, solenoid):
        """Set the solenoid config.

        :param solenoid: Value to set the solenoid
        :type solenoid: bool
        :returns: None
        :raises: InvalidInput
        """
        if type(solenoid) != bool:
            raise InvalidInput("Solenoid value must be bool")
        self._config['solenoid'] = bool2int(solenoid)
        self._q.put(self._config)

    def get_cooling_motor(self):
        """Get the cooling motor config.

        :returns: None
        """
        return self._config['cooling_motor']

    def set_cooling_motor(self, cooling_motor):
        """Set the cooling motor config.

        :param cooling_motor: Value to set the cooling motor
        :type cooling_motor: bool
        :returns: None
        :raises: InvalidInput
        """
        if type(cooling_motor) != bool:
            raise InvalidInput("Cooling motor value must be bool")
        self._config['cooling_motor'] = bool2int(cooling_motor)
        self._q.put(self._config)
