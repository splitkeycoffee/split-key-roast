"""
Initialize the application and import all the blueprints.

This file will initialize all of the global variables used within the rest of
the application. Anything needed for the app context will be done within the
`create_app` function and returned back to the caller handler.
"""
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from pyhottop.pyhottop import Hottop
from models.user import User
import eventlet
import logging
import socketio
import sys

mgr = socketio.RedisManager('redis://')
sio = SocketIO(client_manager=mgr)
login_manager = LoginManager()
mongo = PyMongo()
ht = Hottop()

logger = logging.getLogger("cloud_cafe")
logger.setLevel(logging.DEBUG)
shandler = logging.StreamHandler(sys.stdout)
fmt = '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
shandler.setFormatter(logging.Formatter(fmt))
logger.addHandler(shandler)

eventlet.monkey_patch()


@login_manager.user_loader
def load_user(username):
    """Create a manager to reload sessions.

    :param username: Username of the logged in user
    :type username: str
    :returns: User
    """
    from flask import current_app as app
    c = mongo.db[app.config['USERS_COLLECTION']]
    u = c.find_one({"username": username})
    if not u:
        return None
    return User(u)


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to the login page."""
    return redirect(url_for('core.login'))


def create_app(debug=False):
    """Create an application context with blueprints."""
    app = Flask(__name__, static_folder='./resources')
    app.config['SECRET_KEY'] = 'iqR2cYJp93PuuO8VbK1Z'
    app.config['MONGO_DBNAME'] = 'cloud_cafe'
    app.config['USERS_COLLECTION'] = 'accounts'
    app.config['INVENTORY_COLLECTION'] = 'inventory'
    app.config['HISTORY_COLLECTION'] = 'history'
    app.config['PROFILE_COLLECTION'] = 'profiles'
    login_manager.init_app(app)
    mongo.init_app(app)
    sio.init_app(app)

    from .core import core as core_blueprint
    app.register_blueprint(core_blueprint)

    return app
