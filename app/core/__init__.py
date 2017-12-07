"""Initialize the blueprint with the global context.

Despite it appearing useless, this file is needed in order to import all of
the routes, so the parent context understands what we have defined.
"""
from flask import Blueprint

core = Blueprint('core', __name__)

from . import (
    auth,
    brews,
    events,
    forms,
    generic,
    history,
    integrations,
    inventory,
    profiles,
    roast
)

from ..models import user
