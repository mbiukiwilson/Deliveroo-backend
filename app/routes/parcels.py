from datetime import datetime, timezone

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
        currency=(data.get("currency") or "KES").upper(),
        payment_status="pending",
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

    data = request.get_json() or {}
    destination = data.get("destination", "").strip()

    if not destination:
        return jsonify({"error": "Destination is required"}), 400

    parcel.destination = destination
    if "destination_lat" in data:
        parcel.destination_lat = data.get("destination_lat")
    if "destination_lng" in data:
        parcel.destination_lng = data.get("destination_lng")
    if "distance" in data:
        parcel.distance = data.get("distance")
    if "duration" in data:
        parcel.duration = data.get("duration")
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


@parcels_bp.post("/<int:parcel_id>/pay")
@jwt_required()
def pay_parcel(parcel_id):
    user_id = current_user_id()
    parcel = Parcel.query.filter_by(id=parcel_id, user_id=user_id).first()

    if not parcel:
        return jsonify({"error": "Parcel not found"}), 404
    if parcel.status == STATUS_CANCELLED:
        return jsonify({"error": "Cancelled parcels cannot be paid"}), 400
    if parcel.payment_status == "paid":
        return jsonify(parcel.to_dict())

    # Demo payment confirmation. Replace this endpoint with M-Pesa/Stripe webhook
    # confirmation when real payment credentials are configured.
    parcel.payment_status = "paid"
    parcel.payment_reference = f"DEMO-{parcel.id}-{int(datetime.now(timezone.utc).timestamp())}"
    parcel.paid_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(parcel.to_dict())


@parcels_bp.get("/<int:parcel_id>/locations")
@jwt_required()
def parcel_locations(parcel_id):
    parcel = Parcel.query.filter_by(id=parcel_id, user_id=current_user_id()).first()
    if not parcel:
        return jsonify({"error": "Parcel not found"}), 404

    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    pagination = ParcelLocation.query.filter_by(parcel_id=parcel.id).order_by(
        ParcelLocation.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "data": [{
            "id": item.id,
            "location": item.location,
            "latitude": float(item.latitude) if item.latitude is not None else None,
            "longitude": float(item.longitude) if item.longitude is not None else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        } for item in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })
