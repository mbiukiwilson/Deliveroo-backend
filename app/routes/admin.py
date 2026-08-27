from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from run import db
from app.models import User, Parcel, ParcelStatusHistory, ParcelLocation

admin_bp = Blueprint("admin", __name__)
