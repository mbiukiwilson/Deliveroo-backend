from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from run import db
from app.models import Parcel, ParcelStatusHistory, ParcelLocation

parcels_bp = Blueprint("parcels", __name__)

STATUS_DELIVERED = "delivered"
STATUS_CANCELLED = "cancelled"


def current_user_id():
    return int(get_jwt_identity())


def calculate_price(weight):
    if weight <= 2:
        return 25.0
    if weight <= 5:
        return 45.0
    if weight <= 10:
        return 85.0
    return weight * 8.0


@parcels_bp.get("")
@jwt_required()
def list_parcels():
    user_id = current_user_id()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 10, type=int), 1), 100)

    query = Parcel.query.filter_by(user_id=user_id).order_by(Parcel.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "data": [parcel.to_dict() for parcel in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    })


@parcels_bp.post("")
@jwt_required()
def create_parcel():
    user_id = current_user_id()
    data = request.get_json() or {}

    required = ["pickup_location", "destination", "weight"]
    missing = [field for field in required if data.get(field) in (None, "")]

    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    weight = float(data["weight"])
    if weight <= 0:
        return jsonify({"error": "Weight must be greater than zero"}), 400

    parcel = Parcel(
        user_id=user_id,
        pickup_location=data["pickup_location"],
        destination=data["destination"],
        weight=weight,
        description=data.get("description"),
        pickup_lat=data.get("pickup_lat"),
        pickup_lng=data.get("pickup_lng"),
        destination_lat=data.get("destination_lat"),
        destination_lng=data.get("destination_lng"),
        status="pending",
        current_location=data["pickup_location"],
        price=calculate_price(weight),
    )

    db.session.add(parcel)
    db.session.flush()

    db.session.add(ParcelStatusHistory(
        parcel_id=parcel.id,
        status="pending",
        location=parcel.pickup_location,
        changed_by=user_id,
    ))

    db.session.commit()

    return jsonify(parcel.to_dict()), 201


@parcels_bp.get("/<int:parcel_id>")
@jwt_required()
def get_parcel(parcel_id):
    parcel = Parcel.query.filter_by(
        id=parcel_id,
        user_id=current_user_id(),
    ).first()

    if not parcel:
        return jsonify({"error": "Parcel not found"}), 404

    return jsonify(parcel.to_dict())


@parcels_bp.patch("/<int:parcel_id>/destination")
@jwt_required()
def update_destination(parcel_id):
    parcel = Parcel.query.filter_by(
        id=parcel_id,
        user_id=current_user_id(),
    ).first()

    if not parcel:
        return jsonify({"error": "Parcel not found"}), 404

    if parcel.status in {STATUS_DELIVERED, STATUS_CANCELLED}:
        return jsonify({"error": "Destination can no longer be changed"}), 400

    destination = (request.get_json() or {}).get("destination", "").strip()

    if not destination:
        return jsonify({"error": "Destination is required"}), 400

    parcel.destination = destination
    db.session.commit()

    return jsonify(parcel.to_dict())


@parcels_bp.patch("/<int:parcel_id>/cancel")
@jwt_required()
def cancel_parcel(parcel_id):
    user_id = current_user_id()
    parcel = Parcel.query.filter_by(id=parcel_id, user_id=user_id).first()

    if not parcel:
        return jsonify({"error": "Parcel not found"}), 404

    if parcel.status in {STATUS_DELIVERED, STATUS_CANCELLED}:
        return jsonify({"error": "Parcel cannot be cancelled"}), 400

    parcel.status = STATUS_CANCELLED

    db.session.add(ParcelStatusHistory(
        parcel_id=parcel.id,
        status=STATUS_CANCELLED,
        location=parcel.current_location,
        changed_by=user_id,
    ))

    db.session.commit()

    return jsonify(parcel.to_dict())
