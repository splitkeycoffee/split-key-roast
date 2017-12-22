"""Handle all events from the websocket connections.

For the most part, these socket functions will only be called when performing
a roast. If the roast page is open or we need to pass graph data, we will use
the websocket calls.
"""
from .. import logger, sio, ht, mongo, tweet_hook
from ..libs.utils import to_bool, now_time, paranoid_clean
from bson.objectid import ObjectId
from flask import current_app as app
from flask import jsonify, request
from flask_login import current_user
from pyhottop.pyhottop import SerialConnectionError


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
    """Callback handler to stream data into the browser.

    Despite not being decorated, this function will still be able to send data
    back through socketio via the redis manager.
    """
    # logger.debug("User callback: %s" % str(data))
    sio.emit('state', data)
    return data


@sio.on('mock')
def on_mock():
    """Launch a thread to simulate activity."""
    ht.start(on_callback)
    activity = {'activity': 'ROAST_START'}
    sio.emit('activity', activity)


@sio.on('roaster-setup')
def on_setup():
    """Establish a connection to the roaster via USB."""
    try:
        ht.connect()
    except SerialConnectionError as e:
        sio.emit('error', {'code': 'SERIAL_CONNECTION_ERROR',
                           'message': str(e)})
        return False
    ht.start(on_callback)
    activity = {'activity': 'ROAST_START'}
    sio.emit('activity', activity)
    return activity


@sio.on('roaster-shutdown')
def on_shutdown():
    """End the connection with the roaster."""
    ht.end()
    activity = {'activity': 'ROAST_SHUTDOWN', 'state': None}
    sio.emit('activity', activity)


@sio.on('start-monitor')
@tweet_hook
def on_start_monitor():
    """Start the monitoring process."""
    state = ht.set_monitor(True)
    activity = {'activity': 'START_MONITOR', 'state': state}
    sio.emit('activity', activity)
    return activity


@sio.on('stop-monitor')
@tweet_hook
def on_stop_monitor():
    """Stop the monitoring process."""
    state = ht.set_monitor(False)
    state = ht.get_roast_properties()
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    state['user'] = current_user.get_id()
    c.insert(state)
    state.pop('_id', None)  # Removes the injected mongo ID
    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    _id = c.update({'label': state.get('coffee').split(' - ')[1]},
                   {'$inc': {'stock': -int(state.get('input_weight'))}})
    activity = {'activity': 'STOP_MONITOR', 'state': state}
    sio.emit('activity', activity)
    return activity


@sio.on('drop')
@tweet_hook
def on_drop():
    """Drop the coffee and begin the cool-down."""
    ht.drop()
    state = ht.add_roast_event({'event': 'Drop'})
    activity = {'activity': 'DROP_COFFEE', 'state': state}
    sio.emit('activity', activity)
    return activity


@sio.on('reset')
def on_reset():
    """Reset the connection with the roaster."""
    ht.reset()
    state = ht.get_roast_properties()
    activity = {'activity': 'ROAST_RESET', 'state': state}
    sio.emit('activity', activity)


@sio.on('dry-end')
def on_dry_end():
    """Register the dry end event."""
    logger.debug("Dry End")
    state = ht.add_roast_event({'event': 'Dry End'})
    activity = {'activity': 'DRY_END', 'state': state}
    sio.emit('activity', activity)
    return activity


@sio.on('first-crack')
@tweet_hook
def on_first_crack():
    """Register the first crack event."""
    logger.debug("First crack")
    state = ht.add_roast_event({'event': 'First Crack'})
    activity = {'activity': 'FIRST_CRACK', 'state': state}
    sio.emit('activity', activity)
    return activity


@sio.on('second-crack')
@tweet_hook
def on_second_crack():
    """Register the second crack event."""
    logger.debug("Second crack")
    state = ht.add_roast_event({'event': 'Second Crack'})
    activity = {'activity': 'SECOND_CRACK', 'state': state}
    sio.emit('activity', activity)
    return activity


@sio.on('roast-properties')
def on_roast_properties(state):
    """Update the roast properties."""
    logger.debug("Roast Properties: %s" % state)
    ht.reset()
    ht.set_roast_properties(state)
    activity = {'activity': 'ROAST_PROPERTIES', 'state': state}
    sio.emit('activity', activity)
    return activity


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
    activity = {'activity': 'SOLENOID', 'state': state, 'text': text}
    sio.emit('activity', activity)


@sio.on('main-fan')
def on_fan(state):
    """Toggle the fan control."""
    state = int(state)
    ht.set_main_fan(state)
    text = "Fan Level %d" % state
    activity = {'activity': 'MAIN_FAN', 'state': state, 'text': text}
    sio.emit('activity', activity)


@sio.on('heater')
def on_heater(state):
    """Toggle the fan control."""
    state = int(state)
    ht.set_heater(state)
    text = "Heater Level %d" % state
    activity = {'activity': 'HEATER', 'state': state, 'text': text}
    sio.emit('activity', activity)
