from flask import Blueprint

manager = Blueprint('managers', __name__)

from . import models
from . import views
