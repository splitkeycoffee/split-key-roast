"""Provide websocket and admin functions for hottop."""

from flask import Flask
from flask import render_template, redirect, url_for, flash
from flask import request
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash
import eventlet
import logging
import socketio
import sys

from forms import LoginForm, RegisterForm, InventoryForm
from user import User

from libs.hottop_thread import Hottop
from libs.hottop_thread import SerialConnectionError
from libs.utils import to_bool, now_time

eventlet.monkey_patch()

app = Flask(__name__, static_folder='./resources')
app.config['SECRET_KEY'] = 'iqR2cYJp93PuuO8VbK1Z'
app.config['MONGO_DBNAME'] = 'cloudcafe'
app.config['USERS_COLLECTION'] = 'accounts'
app.config['INVENTORY_COLLECTION'] = 'inventory'
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
    c = mongo.db[app.config['USERS_COLLECTION']]
    u = c.find_one({"email": email})
    if not u:
        return None
    return User(u)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


"""Web-based routes to serve the application."""


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
            flash("Logged in successfully", category='success')
            next = request.args.get('next')
            return redirect(next or url_for('root'))
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
        flash("Registration successful", category='success')
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
    items = [x for x in items]
    return render_template('inventory.html', inventory=items)


@app.route('/add-inventory', methods=['POST'])
@login_required
def add_inventory():
    """Render the index page."""
    form = InventoryForm(request.form)
    if form.validate():
        logger.debug("kklklklklklk")
        c = mongo.db[app.config['INVENTORY_COLLECTION']]
        item = {'label': form.label.data, 'origin': form.origin.data,
                'process': form.method.data, 'stock': form.stock.data,
                'datetime': now_time(), 'user': current_user.get_id()}
        _id = c.insert(item)
        return redirect(url_for('inventory'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return {'errors': errors}


@app.route('/settings')
@login_required
def settings():
    """Render the settings page."""
    return render_template('settings.html')


@app.route('/history')
@login_required
def history():
    """Render the history page."""
    return render_template('history.html')


@app.route('/roast')
@login_required
def active_roast():
    """Render the roast page."""
    return render_template('roast.html')


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
