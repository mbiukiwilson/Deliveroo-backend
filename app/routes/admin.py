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

@admin_bp.patch("/parcels/<int:parcel_id>/status")
@jwt_required()
def update_status(parcel_id):
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Admin access required"}), 403

    parcel = Parcel.query.get_or_404(parcel_id)
    status = (request.get_json() or {}).get("status")

    allowed = {"pending", "in_transit", "delivered", "cancelled"}
    if status not in allowed:
        return jsonify({"error": "Invalid status"}), 400

    if status == "in_transit" and parcel.payment_status != "paid":
        return jsonify({
            "error": "Payment is required before a parcel can be marked as in transit."
        }), 402

    parcel.status = status

    db.session.add(ParcelStatusHistory(
        parcel_id=parcel.id,
        status=status,
        location=parcel.current_location,
        changed_by=admin.id,
    ))

    db.session.commit()
    return jsonify(parcel.to_dict())