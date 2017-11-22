"""Provide websocket and admin functions for hottop."""

from flask import Flask, Response
from flask import render_template, redirect, url_for, jsonify
from flask import request
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId
import eventlet
import json
import logging
import socketio
import sys

from forms import LoginForm, RegisterForm, InventoryForm
from user import User

from libs.hottop_thread import Hottop
from libs.hottop_thread import SerialConnectionError
from libs.utils import to_bool, now_time, paranoid_clean

eventlet.monkey_patch()

app = Flask(__name__, static_folder='./resources')
app.config['SECRET_KEY'] = 'iqR2cYJp93PuuO8VbK1Z'
app.config['MONGO_DBNAME'] = 'cloud_cafe'
app.config['USERS_COLLECTION'] = 'accounts'
app.config['INVENTORY_COLLECTION'] = 'inventory'
app.config['HISTORY_COLLECTION'] = 'history'
login_manager = LoginManager()
login_manager.init_app(app)

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

"""Helper functions."""


@login_manager.user_loader
def load_user(email):
    """Create a manager to reload sessions."""
    c = mongo.db[app.config['USERS_COLLECTION']]
    u = c.find_one({"email": email})
    if not u:
        return None
    return User(u)


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to the login page."""
    return redirect(url_for('login'))


"""Web-based routes to serve the application."""


@app.route('/debug')
def debug():
    """Render the index page."""
    return render_template('debug.html')


@app.route('/')
def root():
    """Render the index page."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle the login process."""
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        c = mongo.db[app.config['USERS_COLLECTION']]
        user = c.find_one({"email": form.email.data})
        logger.debug("User: %s" % user)
        if user and User.validate_login(user['password'], form.password.data):
            user_obj = User(user)
            login_user(user_obj, remember=True)
            # flash("Logged in successfully", category='success')
            next = request.args.get('next')
            return redirect(next or url_for('root'))
    logger.debug("Return")
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Handle the logout process."""
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Render the register page."""
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        c = mongo.db[app.config['USERS_COLLECTION']]
        user = {"email": form.email.data, "first_name": form.first_name.data,
                "last_name": form.last_name.data,
                'password': generate_password_hash(form.password.data)}
        logger.debug("User: %s" % user)
        _id = c.insert(user)
        next = request.args.get('next')
        return redirect(next or url_for('login'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return render_template('register.html', message=errors)


@app.route('/inventory')
@login_required
def inventory():
    """Render the inventory page."""
    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    output = list()
    for x in items:
        x['id'] = str(x['_id'])
        output.append(x)
    output.sort(key=lambda x: x['datetime'], reverse=True)
    return render_template('inventory.html', inventory=output)


@app.route('/inventory/add-inventory', methods=['POST'])
@login_required
def add_inventory():
    """Render the index page."""
    form = InventoryForm(request.form)
    if form.validate():
        c = mongo.db[app.config['INVENTORY_COLLECTION']]
        item = {'label': form.label.data, 'origin': form.origin.data,
                'process': form.method.data, 'stock': int(form.stock.data),
                'datetime': now_time(), 'user': current_user.get_id()}
        _id = c.insert(item)
        return redirect(url_for('inventory'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@app.route('/inventory/edit-inventory', methods=['POST'])
@login_required
def edit_inventory():
    """Render the index page."""
    form = InventoryForm(request.form)
    if form.validate():
        if 'inventory_id' not in request.form:
            return jsonify({'success': False, 'error': 'ID not found in edit!'})
        edit_id = paranoid_clean(request.form.get('inventory_id'))
        c = mongo.db[app.config['INVENTORY_COLLECTION']]
        item = {'label': form.label.data, 'origin': form.origin.data,
                'process': form.method.data, 'stock': form.stock.data}
        c.update({'_id': ObjectId(edit_id)}, {'$set': item})
        return redirect(url_for('inventory'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@app.route('/inventory/remove-item', methods=['POST'])
@login_required
def remove_inventory():
    """Render the index page."""
    args = request.get_json()
    if 'id' not in args:
        return jsonify({'success': False, 'error': 'ID not found in request!'})
    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    remove_id = paranoid_clean(args.get('id'))
    c.remove({'_id': ObjectId(remove_id)})
    return jsonify({'success': True})


@app.route('/settings')
@login_required
def settings():
    """Render the settings page."""
    return render_template('settings.html')


@app.route('/history')
@login_required
def history():
    """Render the history page."""
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    output = list()
    for x in items:
        x['id'] = str(x['_id'])
        output.append(x)
    output.sort(key=lambda x: x['end_time'], reverse=True)
    return render_template('history.html', history=output)


@app.route('/history/remove-item', methods=['POST'])
@login_required
def remove_history():
    """Remove a roast from history."""
    args = request.get_json()
    if 'id' not in args:
        return jsonify({'success': False, 'error': 'ID not found in request!'})
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    remove_id = paranoid_clean(args.get('id'))
    c.remove({'_id': ObjectId(remove_id)})
    return jsonify({'success': True})


@app.route('/profiles')
@login_required
def profiles():
    """Render the profiles page."""
    return render_template('profiles.html')


@app.route('/roast')
@login_required
def active_roast():
    """Render the roast page."""
    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    output = list()
    for x in items:
        x['id'] = str(x['_id'])
        output.append(x)
    output.sort(key=lambda x: x['datetime'], reverse=True)
    return render_template('roast.html', inventory=output)


@app.route('/roast/<roast_id>')
@login_required
def historic_roast(roast_id):
    """Render a previous roast page."""
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    roast_id = paranoid_clean(roast_id)
    item = c.find_one({'_id': ObjectId(roast_id)})
    if not item:
        return jsonify({'success': False, 'message': 'No such roast.'})
    item['id'] = str(item['_id'])

    derived = {'s1': list(), 's2': list(), 's3': list(), 's4': list()}
    for p in item['events']:
        derived['s1'].append([p['time'], p['config']['environment_temp']])
        derived['s2'].append([p['time'], p['config']['bean_temp']])
        derived['s3'].append([p['time'], p['config']['main_fan'] * 10])
        derived['s4'].append([p['time'], p['config']['heater']])

    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    inventory = list()
    for x in items:
        x['id'] = str(x['_id'])
        inventory.append(x)
    inventory.sort(key=lambda x: x['datetime'], reverse=True)

    return render_template('historic_roast.html', roast=item,
                           inventory=inventory, derived=derived)


@app.route('/export')
@login_required
def export_roast():
    """Export a roast log."""
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    roast_id = request.args.get('id')
    roast_id = paranoid_clean(roast_id)
    item = c.find_one({'_id': ObjectId(roast_id)}, {'_id': 0})
    if not item:
        return jsonify({'success': False, 'message': 'No such roast.'})
    content = json.dumps(item, indent=4, sort_keys=True)
    coffee = item['coffee'].replace(' ', '-')
    f = "{0}-{1}-{2}.log".format(item['date'], coffee, roast_id)
    headers = {'Content-Disposition': 'attachment;filename=%s' % f}
    return Response(content, mimetype='application/json', headers=headers)


"""Websocket routes to perform management of the roast."""


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


@sio.on('setup')
def on_setup():
    """Establish a connection to the roaster via USB."""
    try:
        ht.connect()
    except SerialConnectionError as e:
        sio.emit('error', {'code': 'SERIAL_CONNECTION_ERROR', 'message': str(e)})
        return
    ht.start(on_callback)
    activity = {'activity': 'ROAST_START'}
    sio.emit('activity', activity)


@sio.on('shutdown')
def on_shutdown():
    """End the connection with the roaster."""
    ht.end()
    state = ht.get_roast_properties()
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    state['user'] = current_user.get_id()
    c.insert(state)
    state.pop('_id', None)  # Removes the injected mongo ID
    activity = {'activity': 'ROAST_SHUTDOWN', 'state': state}
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

if __name__ == '__main__':
    sio.run(app, host="0.0.0.0", port=80)
