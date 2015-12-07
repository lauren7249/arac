from flask import Blueprint

crawlera = Blueprint('crawlera', __name__)

from . import views
