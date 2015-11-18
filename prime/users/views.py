from flask import Flask
import datetime
import requests
import json
import urllib
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask.ext.login import current_user

from . import users
from prime.prospects.models import Prospect, Job, Education, Company, School, \
Industry
from prime.users.models import User, ClientProspect
from prime.prospects.prospect_list import ProspectList
from prime import db, csrf

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast

from prime.prospects.helper import LinkedinResults

session = db.session

##############
##  VIEWS  ##
#############

