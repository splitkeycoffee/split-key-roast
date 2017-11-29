"""Routes related to brews."""
from . import core
from .. import mongo, logger
from ..libs.utils import now_time, paranoid_clean, now_date, load_date
from .forms import BrewForm
from bson.objectid import ObjectId
from flask import (
    render_template, redirect, url_for, jsonify, request
)
from flask import current_app as app
from flask_login import login_required, current_user


@core.route('/brews')
@login_required
def brews():
    """Render the brews page."""
    c = mongo.db[app.config['BREWS_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    brews = list()
    for x in items:
        x['id'] = str(x['_id'])
        brews.append(x)
    brews.sort(key=lambda x: x['datetime'], reverse=True)

    c = mongo.db[app.config['HISTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    roasts = list()
    for x in items:
        x['id'] = str(x['_id'])
        roasts.append(x)
    roasts.sort(key=lambda x: x['date'], reverse=True)
    return render_template('brews.html', brews=brews, roasts=roasts)


@core.route('/brews/new', methods=['GET'])
@login_required
def new_brew():
    """Render the add new brew page."""
    c = mongo.db[app.config['HISTORY_COLLECTION']]
    items = c.find({'user': current_user.get_id()})
    output = list()
    for x in items:
        x['id'] = str(x['_id'])
        output.append(x)
    output.sort(key=lambda x: x['date'], reverse=True)
    return render_template('new_brew.html', roasts=output)


@core.route('/brews/add-brew', methods=['POST'])
@login_required
def add_brew():
    """Render the index page."""
    form = BrewForm(request.form)
    if form.validate():
        c = mongo.db[app.config['HISTORY_COLLECTION']]
        roast_id = paranoid_clean(form.roast_id.data)
        roast = c.find_one({'_id': ObjectId(roast_id)})
        td = now_date(str=False) - load_date(roast['date'])
        c = mongo.db[app.config['BREWS_COLLECTION']]
        item = {'coffee': roast['coffee'],
                'roast_id': form.roast_id.data,
                'brew_method': form.brew_method.data,
                'input_weight': float(form.input_weight.data),
                'output_weight': float(form.output_weight.data),
                'brew_time': form.brew_time.data,
                'dry_smell': form.dry_smell.data,
                'grind_smell': form.grind_smell.data,
                'wet_smell': form.wet_smell.data,
                'tasting_notes': form.tasting_notes.data,
                'tags': list(),
                'datetime': now_time(),
                'user': current_user.get_id(),
                'days_since_roast': td.days}
        c.insert(item)
        return redirect(url_for('core.brews'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@core.route('/brews/edit-brew', methods=['POST'])
@login_required
def edit_brew():
    """Render the index page."""
    form = BrewForm(request.form)
    if form.validate():
        if 'brew_id' not in request.form:
            return jsonify({'success': False,
                            'error': 'ID not found in edit!'})
        edit_id = paranoid_clean(request.form.get('brew_id'))
        c = mongo.db[app.config['HISTORY_COLLECTION']]
        roast_id = paranoid_clean(form.roast_id.data)
        roast = c.find_one({'_id': ObjectId(roast_id)})
        c = mongo.db[app.config['BREWS_COLLECTION']]
        item = {'coffee': roast['coffee'],
                'roast_id': form.roast_id.data,
                'brew_method': form.brew_method.data,
                'input_weight': float(form.input_weight.data),
                'output_weight': float(form.output_weight.data),
                'brew_time': form.brew_time.data,
                'dry_smell': form.dry_smell.data,
                'grind_smell': form.grind_smell.data,
                'wet_smell': form.wet_smell.data,
                'tasting_notes': form.tasting_notes.data}
        c.update({'_id': ObjectId(edit_id)}, {'$set': item})
        return redirect(url_for('core.brews'))
    errors = ','.join([value[0] for value in form.errors.values()])
    return jsonify({'errors': errors})


@core.route('/brews/remove-item', methods=['POST'])
@login_required
def remove_brew():
    """Render the index page."""
    args = request.get_json()
    if 'id' not in args:
        return jsonify({'success': False,
                        'error': 'ID not found in request!'})
    c = mongo.db[app.config['BREWS_COLLECTION']]
    remove_id = paranoid_clean(args.get('id'))
    c.remove({'_id': ObjectId(remove_id)})
    return jsonify({'success': True})
