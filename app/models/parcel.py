from run import db


class Parcel(db.Model):
    __tablename__ = "parcels"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    pickup_location = db.Column(db.String(255), nullable=False)
    pickup_lat = db.Column(db.Numeric(10, 7))
    pickup_lng = db.Column(db.Numeric(10, 7))

    destination = db.Column(db.String(255), nullable=False)
    destination_lat = db.Column(db.Numeric(10, 7))
    destination_lng = db.Column(db.Numeric(10, 7))

    weight = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)

    status = db.Column(db.String(30), nullable=False, default="pending")

    current_location = db.Column(db.String(255))
    current_lat = db.Column(db.Numeric(10, 7))
    current_lng = db.Column(db.Numeric(10, 7))

    distance = db.Column(db.Numeric(10, 2))
    duration = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2))

    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    user = db.relationship("User", back_populates="parcels")
    status_history = db.relationship(
        "ParcelStatusHistory",
        back_populates="parcel",
        cascade="all, delete-orphan",
    )
    locations = db.relationship(
        "ParcelLocation",
        back_populates="parcel",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tracking_id": f"SIT-{self.id:06d}",
            "pickup_location": self.pickup_location,
            "pickup_lat": float(self.pickup_lat) if self.pickup_lat is not None else None,
            "pickup_lng": float(self.pickup_lng) if self.pickup_lng is not None else None,
            "destination": self.destination,
            "destination_lat": float(self.destination_lat) if self.destination_lat is not None else None,
            "destination_lng": float(self.destination_lng) if self.destination_lng is not None else None,
            "weight": float(self.weight),
            "description": self.description,
            "status": self.status,
            "current_location": self.current_location,
            "current_lat": float(self.current_lat) if self.current_lat is not None else None,
            "current_lng": float(self.current_lng) if self.current_lng is not None else None,
            "distance": float(self.distance) if self.distance is not None else None,
            "duration": self.duration,
            "price": float(self.price) if self.price is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ParcelStatusHistory(db.Model):
    __tablename__ = "parcel_status_history"

    id = db.Column(db.Integer, primary_key=True)
    parcel_id = db.Column(db.Integer, db.ForeignKey("parcels.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(255))
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    parcel = db.relationship("Parcel", back_populates="status_history")


class ParcelLocation(db.Model):
    __tablename__ = "parcel_locations"

    id = db.Column(db.Integer, primary_key=True)
    parcel_id = db.Column(db.Integer, db.ForeignKey("parcels.id"), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    parcel = db.relationship("Parcel", back_populates="locations")
