from .. import logger, sio, ht, mongo
from ..libs.utils import to_bool, now_time, paranoid_clean
from bson.objectid import ObjectId
from flask import current_app as app
from flask import jsonify, request
from flask_login import current_user


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
    # logger.debug("User callback: %s" % str(data))
    sio.emit('state', data)


@sio.on('mock')
def on_mock():
    """Launch a thread to simulate activity."""
    ht.start(on_callback)
    activity = {'activity': 'ROAST_START'}
    sio.emit('activity', activity)


@sio.on('roaster-setup')
def on_setup():
    """Establish a connection to the roaster via USB."""
    # try:
    #     ht.connect()
    # except SerialConnectionError as e:
    #     sio.emit('error', {'code': 'SERIAL_CONNECTION_ERROR', 'message': str(e)})
    #     return
    ht.start(on_callback)
    activity = {'activity': 'ROAST_START'}
    sio.emit('activity', activity)


@sio.on('roaster-shutdown')
def on_shutdown():
    """End the connection with the roaster."""
    ht.end()
    activity = {'activity': 'ROAST_SHUTDOWN', 'state': None}
    sio.emit('activity', activity)


@sio.on('start-monitor')
def on_start_monitor():
    """Start the monitoring process."""
    state = ht.set_monitor(True)
    activity = {'activity': 'START_MONITOR', 'state': state}
    sio.emit('activity', activity)


@sio.on('stop-monitor')
def on_stop_monitor():
    """Stop the monitoring process."""
    state = ht.set_monitor(False)
    state = ht.get_roast_properties()
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    state['user'] = current_user.get_id()
    c.insert(state)
    state.pop('_id', None)  # Removes the injected mongo ID
    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    _update = c.update({'label': state.get('coffee').split(' - ')[1]},
                       {'$inc': {'stock': -int(state.get('input_weight'))}})
    activity = {'activity': 'STOP_MONITOR', 'state': state}
    sio.emit('activity', activity)


@sio.on('drop')
def on_drop():
    """Drop the coffee and begin the cool-down."""
    ht.drop()
    state = ht.add_roast_event({'event': 'Drop Coffee'})
    activity = {'activity': 'DROP_COFFEE', 'state': state}
    sio.emit('activity', activity)


@sio.on('reset')
def on_reset():
    """Reset the connection with the roaster."""
    ht.reset()
    state = ht.get_roast_properties()
    activity = {'activity': 'ROAST_RESET', 'state': state}
    sio.emit('activity', activity)


@sio.on('first-crack')
def on_first_crack():
    """Register the first crack event."""
    logger.debug("First crack")
    state = ht.add_roast_event({'event': 'First Crack'})
    activity = {'activity': 'FIRST_CRACK', 'state': state}
    sio.emit('activity', activity)


@sio.on('second-crack')
def on_second_crack():
    """Register the second crack event."""
    logger.debug("Second crack")
    state = ht.add_roast_event({'event': 'Second Crack'})
    activity = {'activity': 'SECOND_CRACK', 'state': state}
    sio.emit('activity', activity)


@sio.on('roast-properties')
def on_roast_properties(state):
    """Update the roast properties."""
    logger.debug("Roast Properties: %s" % state)
    ht.set_roast_properties(state)
    activity = {'activity': 'ROAST_PROPERTIES', 'state': state}
    sio.emit('activity', activity)


@sio.on('update-roast-properties')
def on_update_roast_properties(state):
    """Update the roast properties."""
    logger.debug("Updated Roast Properties: %s" % state)
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    roast_id = paranoid_clean(state.get('id'))
    item = c.find_one({'_id': ObjectId(roast_id)}, {'_id': 0})
    if not item:
        return jsonify({'success': False, 'message': 'No such roast.'})
    item = {'notes': state.get('notes'),
            'input_weight': state.get('input_weight'),
            'output_weight': state.get('output_weight')}
    c.update({'_id': ObjectId(roast_id)}, {'$set': item})
    return jsonify({'success': True})


@sio.on('save-profile')
def on_save_profile(state):
    """Save the roast profile."""
    logger.debug("Roast Profile: %s" % state)
    c = mongo.db[app.config['PROFILE_COLLECTION']]
    item = {'coffee': state.get('coffee'), 'roast': state.get('roast'),
            'drop_temp': state.get('drop_temp'),
            'brew_methods': state.get('brew_methods'),
            'notes': state.get('notes'), 'datetime': now_time(),
            'user': current_user.get_id()}
    _id = c.insert(item)
    return jsonify({'success': True})


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