"""Calls related to roasting."""
import cairosvg
import math
import os
import random
from . import core
from .. import logger, mongo
from ..libs.utils import paranoid_clean, now_time, search_list, now_date
from bson.objectid import ObjectId
from flask import current_app as app
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from collections import OrderedDict


@core.route('/roast')
@login_required
def active_roast():
    """Render the roast page."""
    c = mongo.db[app.config['INVENTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    output = list()
    for x in items:
        x['id'] = str(x['_id'])
        if int(x['stock']) < 100:
            continue
        if app.config['SIMULATE_ROAST'] and x['label'] != 'Test Beans':
            continue
        output.append(x)
    output.sort(key=lambda x: x['datetime'], reverse=True)
    return render_template('roast.html', inventory=output)


@core.route('/roast/send-svg', methods=['POST'])
@login_required
def send_svg():
    """Render the roast page."""
    state = request.get_json()
    path = os.path.dirname(__file__).replace('core', 'resources/tmp')
    filename = path + "/" + now_date(str=True) + "-roast.png"
    cairosvg.svg2png(bytestring=state['svg'], write_to=filename)
    return jsonify({'success': True})


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
    item['notes'] = item['notes'].replace('\n', ' ')
    derived = {'s1': list(), 's2': list(), 's3': list(), 's4': list(),
               's5': list(), 's6': list(), 'flags': list(),
               'observations': list(), 'periods': {'tp2dry': None,
               'dry2fc': None, 'fc2sc': None, 'sc2end': None, 'fc2end': None}}
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

    details = OrderedDict({'state': {'last': -1, 'previous': None}})
    for idx, p in enumerate(item['events']):
        if not p['config'].get('valid', True):
            continue

        round_time = int(p['time'])
        config = p['config']
        config['bean_temp_str'] = ("%.2f" % config['bean_temp'])
        config['environment_temp_str'] = ("%.2f" % config['environment_temp'])

        if 'event' in p:
            derived['observations'].append(p)
            continue

        if round_time not in details:
            details[round_time] = dict()
            details[round_time]['first'] = config
            if round_time == 1:
                details[round_time - 1]['last'] = details['state']['previous']
                last = details[round_time - 1]['last']['bean_temp']
                first = details[round_time - 1]['first']['bean_temp']
                details[round_time - 1]['delta'] = (last - first)
                total = int(((last - first) / float(first)) * 100)
                details[round_time - 1]['percent'] = total

        if round_time > details['state']['last']:
            if round_time > 0:
                details[round_time - 1]['last'] = details['state']['previous']
                last = details[round_time - 1]['last']['bean_temp']
                first = details[round_time - 1]['first']['bean_temp']
                details[round_time - 1]['delta'] = (last - first)
                last = details[round_time - 1]['last']['environment_temp']
                first = details[round_time - 1]['first']['environment_temp']
                derived['s5'].append([p['time'], details[round_time - 1]['delta']])
                derived['s6'].append([p['time'], last - first])
                total = int(((last - first) / float(first)) * 100)
                details[round_time - 1]['percent'] = total
            details['state']['last'] = round_time

        if (idx == len(item['events']) - 1):
            details[round_time]['last'] = config

        details['state']['previous'] = config

    del details['state']

    tp = search_list(derived['observations'], 'event', 'Turning Point')
    dry = search_list(derived['observations'], 'event', 'Dry End')
    fc = search_list(derived['observations'], 'event', 'First Crack')
    sc = search_list(derived['observations'], 'event', 'Second Crack')
    drop = search_list(derived['observations'], 'event', 'Drop')
    tp2dry = "<b>Drying</b><br>"
    tp2dry += str(int((dry['time'] - tp['time']) / drop['time'] * 100)) + "%"
    derived['periods']['tp2dry'] = {'from': tp['time'], 'to': dry['time'],
                                    'label': {'text': tp2dry},
                                    'color': '#fcf1dd7d'}
    dry2fc = "<b>Roasting</b><br>"
    dry2fc += str(int((fc['time'] - dry['time']) / drop['time'] * 100)) + "%"
    derived['periods']['dry2fc'] = {'from': dry['time'], 'to': fc['time'],
                                    'label': {'text': dry2fc, 'z-index': 99},
                                    'color': '#d9b59496'}
    if sc:
        sc2end = "<b>Development</b><br>"
        sc2end += str(int((drop['time'] - fc['time']) / drop['time'] * 100)) + "%"
        derived['periods']['sc2end'] = {'from': fc['time'], 'to': drop['time'],
                                        'label': {'text': sc2end},
                                        'color': '#fff52247'}
    fc2end = "<b>Development</b><br>"
    fc2end += str(int((drop['time'] - fc['time']) / drop['time'] * 100)) + "%"
    derived['periods']['fc2end'] = {'from': fc['time'], 'to': drop['time'],
                                    'label': {'text': fc2end},
                                        'color': '#fff52247'}

    return render_template('historic_roast.html', roast=item,
                           inventory=inventory, derived=derived,
                           cuppings=cuppings, brews=brews, details=details)


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
