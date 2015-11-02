from flask import Blueprint

processing_service = Blueprint('processing_service', __name__)

from . import processing_service
