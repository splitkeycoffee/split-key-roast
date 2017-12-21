"""Calls related to roasting."""
from . import core
from .. import logger, mongo
from ..libs.utils import paranoid_clean, now_time
from bson.objectid import ObjectId
from flask import current_app as app
from flask import render_template, jsonify, request
from flask_login import login_required, current_user


@core.route('/roast')
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


@core.route('/roast/<roast_id>')
@login_required
def historic_roast(roast_id):
    """Render a previous roast page."""
    # Collect the roast history data
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    roast_id = paranoid_clean(roast_id)
    item = c.find_one({'_id': ObjectId(roast_id)})
    if not item:
        return jsonify({'success': False, 'message': 'No such roast.'})
    item['id'] = str(item['_id'])
    derived = {'s1': list(), 's2': list(), 's3': list(), 's4': list(),
               'flags': list()}
    for p in item['events']:
        if 'event' in p:
            label = "%s (%d, %d)" % (p['event'],
                                     int(p['config']['environment_temp']),
                                     int(p['config']['bean_temp']))
            derived['flags'].append({'x': p['time'], 'title': str(label)})
            continue
        if not p['config'].get('valid', True):
            continue
        derived['s1'].append([p['time'], p['config']['environment_temp']])
        derived['s2'].append([p['time'], p['config']['bean_temp']])
        derived['s3'].append([p['time'], p['config']['main_fan'] * 10])
        derived['s4'].append([p['time'], p['config']['heater']])

    # Collect the inventory data
    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    inventory = list()
    for x in items:
        x['id'] = str(x['_id'])
        inventory.append(x)
    inventory.sort(key=lambda x: x['datetime'], reverse=True)

    # Collect the cupping data
    cuppings = list()

    # Collect the brew data
    c = mongo.db[app.config['BREWS_COLLECTION']]
    items = c.find({'user': current_user.get_id(), 'roast_id': roast_id})
    brews = list()
    for x in items:
        x['id'] = str(x['_id'])
        brews.append(x)
    brews.sort(key=lambda x: x['datetime'], reverse=True)

    return render_template('historic_roast.html', roast=item,
                           inventory=inventory, derived=derived,
                           cuppings=cuppings, brews=brews)


@core.route('/roast/update-properties', methods=['POST'])
@login_required
def update_properties():
    """Render the index page."""
    state = request.get_json()
    if 'id' not in state:
        return jsonify({'success': False,
                        'error': 'ID not found in request!'})
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


@core.route('/roast/save-profile', methods=['POST'])
@login_required
def save_profile():
    """Render the index page."""
    state = request.get_json()
    logger.debug("Roast Profile: %s" % state)
    c = mongo.db[app.config['PROFILE_COLLECTION']]
    item = {'coffee': state.get('coffee'), 'roast': state.get('roast'),
            'drop_temp': state.get('drop_temp'),
            'brew_methods': state.get('brew_methods'),
            'notes': state.get('notes'), 'datetime': now_time(),
            'user': current_user.get_id()}
    _id = c.insert(item)
    return jsonify({'success': True})
