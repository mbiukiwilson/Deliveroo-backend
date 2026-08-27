from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from run import db
from app.models import User, Parcel, ParcelStatusHistory, ParcelLocation

admin_bp = Blueprint("admin", __name__)

def admin_user():
    return User.query.get(int(get_jwt_identity()))


def require_admin():
    user = admin_user()
    return user if user and user.role == "admin" else None

@admin_bp.get("/parcels")
@jwt_required()
def list_all_parcels():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 10, type=int), 1), 100)

    pagination = Parcel.query.order_by(Parcel.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return jsonify({
        "data": [p.to_dict() for p in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })