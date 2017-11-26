from . import core
from .. import mongo
from ..libs.utils import now_time, paranoid_clean
from .forms import (
    InventoryForm, AccountSettingsForm, ChangePasswordForm, ProfileForm
)
from bson.objectid import ObjectId
from flask import (
    render_template, redirect, url_for, jsonify, request, Response
)
from flask import current_app as app
from flask_login import login_required, current_user


@core.route('/inventory')
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


@core.route('/inventory/add-inventory', methods=['POST'])
@login_required
def add_inventory():
    """Render the index page."""
    form = InventoryForm(request.form)
    if form.validate():
        c = mongo.db[app.config['INVENTORY_COLLECTION']]
        item = {'label': form.label.data, 'origin': form.origin.data,
                'process': form.method.data, 'stock': int(form.stock.data),
                'organic': form.organic.data,
                'fair_trade': form.fair_trade.data, 'tags': list(),
                'datetime': now_time(), 'user': current_user.get_id()}
        _id = c.insert(item)
        return redirect(url_for('core.inventory'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@core.route('/inventory/edit-inventory', methods=['POST'])
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
                'process': form.method.data, 'stock': form.stock.data,
                'organic': form.organic.data,
                'fair_trade': form.fair_trade.data, 'tags': list(),
                }
        c.update({'_id': ObjectId(edit_id)}, {'$set': item})
        return redirect(url_for('core.inventory'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@core.route('/inventory/remove-item', methods=['POST'])
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
