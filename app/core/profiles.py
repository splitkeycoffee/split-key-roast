from . import core
from .. import mongo, logger
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


@core.route('/profiles')
@login_required
def profiles():
    """Render the profiles page."""
    c = mongo.db[app.config['PROFILE_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    output = list()
    for x in items:
        x['id'] = str(x['_id'])
        output.append(x)
    output.sort(key=lambda x: x['datetime'], reverse=True)
    return render_template('profiles.html', profiles=output)


@core.route('/profiles/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    """Render the index page."""
    form = ProfileForm(request.form)
    if form.validate():
        if 'profile_id' not in request.form:
            return jsonify({'success': False, 'error': 'ID not found in edit!'})
        edit_id = paranoid_clean(request.form.get('profile_id'))
        c = mongo.db[app.config['PROFILE_COLLECTION']]
        item = {'coffee': form.coffee.data, 'roast': form.roast.data,
                'drop_temp': form.drop_temp.data, 'notes': form.notes.data,
                'brew_methods': form.brew_methods.data}
        c.update({'_id': ObjectId(edit_id)}, {'$set': item})
        return redirect(url_for('core.profiles'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@core.route('/profiles/remove-item', methods=['POST'])
@login_required
def remove_profile():
    """Render the index page."""
    args = request.get_json()
    if 'id' not in args:
        return jsonify({'success': False, 'error': 'ID not found in request!'})
    c = mongo.db[app.config['PROFILE_COLLECTION']]
    remove_id = paranoid_clean(args.get('id'))
    c.remove({'_id': ObjectId(remove_id)})
    return jsonify({'success': True})