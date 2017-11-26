from . import core
from .. import mongo
from ..libs.utils import paranoid_clean
from .forms import (
    InventoryForm, AccountSettingsForm, ChangePasswordForm, ProfileForm
)
from bson.objectid import ObjectId
from flask import (
    render_template, redirect, url_for, jsonify, request, Response
)
from flask import current_app as app
from flask_login import login_required, current_user


@core.route('/history')
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


@core.route('/history/remove-item', methods=['POST'])
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
