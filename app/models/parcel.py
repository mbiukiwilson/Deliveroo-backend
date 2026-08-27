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
    currency = db.Column(db.String(3), nullable=False, default="KES")
    payment_status = db.Column(db.String(20), nullable=False, default="pending")
    payment_reference = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime)

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