from flask import Blueprint

core = Blueprint('core', __name__)

from . import (
    generic, forms, user, events, auth, inventory, history, profiles, roast
)
from .. import mongo
