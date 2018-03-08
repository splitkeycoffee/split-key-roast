"""
Initialize the application and import all the blueprints.

This file will initialize all of the global variables used within the rest of
the application. Anything needed for the app context will be done within the
`create_app` function and returned back to the caller handler.
"""
from flask import current_app as app
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from .models.const import creatives
from .models.user import User
from .libs.utils import now_date
from pyhottop.pyhottop import Hottop
# from libs.hottop_thread import Hottop
import copy
import eventlet
import logging
import os
import random
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

# Must import post monkey patching to avoid issues with requests library
import twitter


def tweet_hook(func):
    """Decorate to run tweets if the integration is enabled."""
    def wrapper(*args, **kwargs):
        results = func(*args, **kwargs)
        c = mongo.db[app.config['USERS_COLLECTION']]
        user = c.find_one({"username": current_user.get_id()})
        integrations = user.get('integrations')

        bot = integrations.get('twitter_bot')
        if not bot.get('status'):
            return results
        # if app.config['SIMULATE_ROAST']:
        #     return results

        creative_ref = copy.deepcopy(creatives)
        action = func.__name__
        base = creative_ref.get(func.__name__)
        creative = None
        media = None
        if action == 'on_start_monitor' and bot.get('tweet_roast_begin'):
            state = results['state']
            creative = base[random.randint(0, len(base) - 1)]
            creative += " %s grams of %s " % (
                state['input_weight'], state['coffee'])
        if action == 'on_stop_monitor' and bot.get('tweet_roast_complete'):
            state = results['state']
            creative = base[random.randint(0, len(base) - 1)]
            creative += " Total time: %s " % (state['duration'])
        if (action in ['on_first_crack', 'on_second_crack', 'on_drop']) \
                and (bot.get('tweet_roast_progress')):
            state = results['state']
            last = state['last']
            creative = base[random.randint(0, len(base) - 1)]
            creative += " State: ET %d, BT %d, Time %s " % (
                last['environment_temp'], last['bean_temp'],
                results['state']['duration'])
        if (action == 'on_shutdown' and bot.get('tweet_roast_complete')):
            creative = base[random.randint(0, len(base) - 1)]
            creative += " "
            media_path = os.path.dirname(__file__) + "/resources/tmp/"
            media = media_path + now_date(str=True) + "-roast.png"

        if not creative:
            # Didn't trigger any of the actions or they weren't enabled
            return results

        tags = 0
        tag_count = random.randint(2, 8)
        hashtags = creative_ref.get('hash_tags')
        while len(creative) <= 250:
            if tags == tag_count:
                break
            hashtag = hashtags[random.randint(0, len(hashtags) - 1)]
            creative += hashtag + " "
            hashtags.remove(hashtag)
            tags += 1

        # Tweeting code
        api = twitter.Api(consumer_key=str(bot.get('consumer_key')),
                          consumer_secret=str(bot.get('consumer_secret')),
                          access_token_key=str(bot.get('access_token_key')),
                          access_token_secret=str(bot.get('access_token_secret')))

        try:
            creative = unicode(creative, "utf-8")
        except:
            creative = str(creative)

        try:
            if not media:
                api.PostUpdate(creative)
            else:
                api.PostUpdate(creative, media=open(media, 'rb'))
        except Exception as e:
            logger.error(str(e))
        return results
    return wrapper


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


def create_app(debug=False, simulate=False):
    """Create an application context with blueprints."""
    app = Flask(__name__, static_folder='./resources')
    app.config['SECRET_KEY'] = 'iqR2cYJp93PuuO8VbK1Z'
    app.config['MONGO_DBNAME'] = 'cloud_cafe'
    app.config['BREWS_COLLECTION'] = 'brews'
    app.config['HISTORY_COLLECTION'] = 'history'
    app.config['INVENTORY_COLLECTION'] = 'inventory'
    app.config['PROFILE_COLLECTION'] = 'profiles'
    app.config['USERS_COLLECTION'] = 'accounts'
    app.config['SIMULATE_ROAST'] = simulate
    login_manager.init_app(app)
    mongo.init_app(app)
    sio.init_app(app)

    from .core import core as core_blueprint
    app.register_blueprint(core_blueprint)

    if simulate:
        ht.set_simulate(True)

    return app
