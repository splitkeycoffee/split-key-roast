"""Generic calls within the application."""
from . import core
from .. import mongo, logger
from ..libs.utils import paranoid_clean, now_date, load_date
from .forms import AccountSettingsForm, ChangePasswordForm
from bson.objectid import ObjectId
from flask import current_app as app
from flask import (
    render_template, redirect, url_for, jsonify, request, Response
)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import json


@core.route('/debug')
def debug():
    """Render the index page."""
    return render_template('debug.html')


@core.route('/')
@login_required
def root():
    """Render the index page."""
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    history = list()
    for x in items:
        x['id'] = str(x['_id'])
        x['rest_days'] = (now_date(False) - load_date(x['date'])).days
        history.append(x)
    history.sort(key=lambda x: x['end_time'], reverse=True)

    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    inventory = list()
    for x in items:
        x['id'] = str(x['_id'])
        inventory.append(x)
    inventory.sort(key=lambda x: x['stock'], reverse=False)

    return render_template('index.html', history=history, inventory=inventory)


@core.route('/settings')
@login_required
def settings():
    """Render the settings page."""
    c = mongo.db[app.config['USERS_COLLECTION']]
    user = c.find_one({'username': current_user.get_id()})
    if not user:
        return render_template()
    user['id'] = str(user['_id'])
    user.pop('_id', None)
    return render_template('settings.html', user=user)


@core.route('/account/settings/update', methods=['POST'])
@login_required
def update_account():
    """Update account settings."""
    form = AccountSettingsForm(request.form)
    if form.validate():
        if 'user_id' not in request.form:
            return jsonify({'success': False,
                            'error': 'ID not found in edit!'})
        edit_id = paranoid_clean(request.form.get('user_id'))
        c = mongo.db[app.config['USERS_COLLECTION']]
        item = {'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'email': form.email.data}
        c.update({'_id': ObjectId(edit_id)}, {'$set': item})
        return redirect(url_for('core.settings'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@core.route('/account/settings/change-password', methods=['POST'])
@login_required
def account_change_password():
    """Update account password."""
    form = ChangePasswordForm(request.form)
    if form.validate():
        if 'user_id' not in request.form:
            return jsonify({'success': False,
                            'error': 'ID not found in edit!'})
        edit_id = paranoid_clean(request.form.get('user_id'))
        c = mongo.db[app.config['USERS_COLLECTION']]
        item = {'password': generate_password_hash(form.password.data)}
        c.update({'_id': ObjectId(edit_id)}, {'$set': item})
        return redirect(url_for('core.settings'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@core.route('/export')
@login_required
def export_roast():
    """Export a roast log."""
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    roast_id = request.args.get('id')
    roast_id = paranoid_clean(roast_id)
    item = c.find_one({'_id': ObjectId(roast_id)}, {'_id': 0})
    if not item:
        return jsonify({'success': False, 'message': 'No such roast.'})
    cleaned = list()
    for i in item.get('events', list()):
        if not i.get('config', dict()).get('valid'):
            continue
        cleaned.append(i)
    item['events'] = cleaned
    content = json.dumps(item, indent=4, sort_keys=True)
    coffee = item['coffee'].replace(',', ' ').replace(' ', '-')
    f = "{0}-{1}-{2}.log".format(item['date'], coffee, roast_id)
    headers = {'Content-Disposition': 'attachment;filename=%s' % f}
    return Response(content, mimetype='application/json', headers=headers)
