"""Provide websocket and admin functions for hottop."""

from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
import eventlet
import logging
import socketio
import sys

from libs.hottop_thread import Hottop
from libs.hottop_thread import SerialConnectionError
from libs.utils import to_bool

eventlet.monkey_patch()
app = Flask(__name__, static_folder='./resources')
app.config['SECRET_KEY'] = 'iqR2cYJp93PuuO8VbK1Z'
app.config['MONGO_DBNAME'] = 'hottop'
mgr = socketio.RedisManager('redis://')
sio = SocketIO(app, client_manager=mgr)
mongo = PyMongo(app)
logger = logging.getLogger("hottop")
logger.setLevel(logging.DEBUG)
shandler = logging.StreamHandler(sys.stdout)
fmt = '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
shandler.setFormatter(logging.Formatter(fmt))
logger.addHandler(shandler)

ht = Hottop()


@app.route('/')
@app.route('/roast')
def root():
    """Render the root."""
    return render_template('roast.html')


@sio.on('connect')
def on_connect():
    """Handle the initial connections and send back current state."""
    logger.debug("Client connected: %s" % request.sid)
    state = ht.get_current_config()
    sio.emit('init', state)


@sio.on('disconnect')
def on_disconnect():
    """Keep track of who disconnects for stats purposes."""
    logger.debug("Client disconnected")


def on_callback(data):
    """Callback handler to stream data into the browser."""
    logger.debug("User callback: %s" % str(data))
    sio.emit('state', data)


@sio.on('mock')
def on_mock():
    """Launch a thread to simulate activity."""
    ht.start(on_callback)


@sio.on('setup')
def on_setup():
    """Establish a connection to the roaster via USB."""
    try:
        ht.connect()
    except SerialConnectionError as e:
        sio.emit('error', {'code': 'SERIAL_CONNECTION_ERROR', 'message': str(e)})
        return
    ht.start(on_callback)


@sio.on('shutdown')
def on_shutdown():
    """End the connection with the roaster."""
    ht.end()


@sio.on('drum-motor')
def on_drum_motor(state):
    """Toggle the drum motor control."""
    logger.debug("Drum Motor: %s" % state)
    state = to_bool(state)
    ht.set_drum_motor(state)
    text = "Turn On" if not state else "Turn Off"
    activity = {'activity': 'DRUM_MOTOR', 'state': state, 'text': text}
    sio.emit('activity', activity)


@sio.on('cooling-motor')
def on_cooling_motor(state):
    """Toggle the cooling motor control."""
    state = to_bool(state)
    ht.set_cooling_motor(state)
    text = "Turn On" if not state else "Turn Off"
    activity = {'activity': 'COOLING_MOTOR', 'state': state, 'text': text}
    sio.emit('activity', activity)


@sio.on('solenoid')
def on_solenoid(state):
    """Toggle the solenoid control."""
    state = to_bool(state)
    ht.set_solenoid(state)
    text = "Turn On" if not state else "Turn Off"
    sio.emit('activity', {'activity': 'SOLENOID', 'state': state, 'text': text})


@sio.on('main-fan')
def on_fan(state):
    """Toggle the fan control."""
    state = int(state)
    ht.set_main_fan(state)
    text = "Fan Level %d" % state
    sio.emit('activity', {'activity': 'MAIN_FAN', 'state': state, 'text': text})


@sio.on('heater')
def on_heater(state):
    """Toggle the fan control."""
    state = int(state)
    ht.set_heater(state)
    text = "Heater Level %d" % state
    sio.emit('activity', {'activity': 'HEATER', 'state': state, 'text': text})

if __name__ == '__main__':
    sio.run(app, host="0.0.0.0", port=80)
