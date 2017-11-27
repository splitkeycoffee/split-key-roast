"""Integration calls within the application."""
from . import core
from .. import logger, mongo
from .forms import IntegrationTwitterbot
from bson.objectid import ObjectId
from flask import current_app as app
from flask import (
    render_template, redirect, url_for, jsonify, request, Response
)
from flask_login import login_required, current_user


@core.route('/integrations')
@login_required
def integrations():
    """Render the integrations page."""
    c = mongo.db[app.config['USERS_COLLECTION']]
    user = c.find_one({"username": current_user.get_id()})
    integrations = user.get('integrations')
    twitter = integrations.get('twitter_bot')
    return render_template('integrations.html', twitter=twitter)


@core.route('/integrations/twitter-bot', methods=['POST'])
@login_required
def integration_twitter_bot():
    """Render the integrations page."""
    form = IntegrationTwitterbot(request.form)
    if form.validate():
        obj = {'status': form.status.data,
               'consumer_key': form.consumer_key.data,
               'consumer_secret': form.consumer_secret.data,
               'access_token_key': form.access_token_key.data,
               'access_token_secret': form.access_token_secret.data,
               'tweet_roast_begin': form.tweet_roast_begin.data,
               'tweet_roast_progress': form.tweet_roast_progress.data,
               'tweet_roast_complete': form.tweet_roast_complete.data}
        c = mongo.db[app.config['USERS_COLLECTION']]
        c.update({'username': current_user.get_id()},
                 {'$set': {'integrations.twitter_bot': obj}})
        return redirect(url_for('core.integrations'))
    return render_template('integrations.html')
