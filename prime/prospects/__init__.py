from flask import Blueprint

prospects = Blueprint('prospects', __name__)

from . import views
