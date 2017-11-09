"""Simple test harness to test hottop functions."""

import binascii
import logging
import serial
import sys
import time


USB_PORT = "/dev/tty.usbserial-DA01PEYC"
USB_PORT = "/dev/cu.usbserial-DA01PEYC"
BAUDRATE = 115200
BYTE_SIZE = 8
PARITY = "N"
STOPBITS = 1
TIMEOUT = 1

BEAN_TEMP = -1
DRUM_TEMP = -1,
HEATER = -1
FAN = -1
MAIN_FAN = -1
SOLENOID = -1
DRUM_MOTOR = -1
COOLING_MOTOR = -1
CHAFF_TRAY = -1

BEAN_TEMP_CUTOFF = 220

STATE = bytearray([0x00]*36)
STATE[0] = 0xA5
STATE[1] = 0x96
STATE[2] = 0xB0
STATE[3] = 0xA0
STATE[4] = 0x01
STATE[5] = 0x01
STATE[6] = 0x24
STATE[10] = 0  # HEATER (0-100)
STATE[11] = 0  # FAN (0-10)
STATE[12] = 0  # MAIN_FAN (0-10)
STATE[16] = 0  # SOLENOID (0 or 1)
STATE[17] = 0  # DRUM MOTOR (0 or 1)
STATE[18] = 0  # COOLING MOTOR (0 or 1)
STATE[35] = sum([b for b in STATE[:35]]) & 0xFF  # CHECKSUM


LOGGER = logging.getLogger("HOTTOP")
LOGGER.setLevel(logging.DEBUG)
shandler = logging.StreamHandler(sys.stdout)
fmt = '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
shandler.setFormatter(logging.Formatter(fmt))
LOGGER.addHandler(shandler)


def bool2int(bool):
    """Convert a bool to an int."""
    if bool:
        return 1
    else:
        return 0


def connect():
    """Connect to the USB for the hottop."""
    conn = serial.Serial(USB_PORT, baudrate=BAUDRATE, bytesize=BYTE_SIZE,
                         parity=PARITY, stopbits=STOPBITS, timeout=TIMEOUT)
    LOGGER.debug("Serial connection set")
    if not conn.isOpen():
        conn.open()
        LOGGER.debug("Serial connection opened")
    return conn


def send_config(conn):
    """Send configuration data to the hottop."""
    serialized = bytes(STATE)
    LOGGER.debug("Configuration has been serialized")
    try:
        conn.flushInput()
        LOGGER.debug("Serial input is flushed")
        conn.flushOutput()
        LOGGER.debug("Serial output is flushed")
        conn.write(serialized)
        LOGGER.debug("Serial configuration was written")
        return True
    except Exception as e:
        LOGGER.error(e)
        raise Exception(e)


def set_fan_speed(speed):
    """Set the fan speed of the hottop."""
    if type(speed) != int and speed not in range(0, 11):
        raise Exception("Fan speed must be an integer between 0-10")
    STATE[11] = speed
    return True


def set_main_fan_speed(speed):
    """Set the main fan speed of the hottop."""
    if type(speed) != int and speed not in range(0, 11):
        raise Exception("Main fan speed must be an integer between 0-10")
    STATE[12] = speed
    return True


def set_drum_state(state):
    """Set the state of the drum."""
    if type(state) != bool:
        raise Exception("Drum state must be of type bool")
    STATE[17] = bool2int(state)


def main():
    """Run the code."""
    conn = connect()
    set_drum_state(True)
    send_config(conn)


if __name__ == "__main__":
    main()
