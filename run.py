import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # =========================
    # DATABASE
    # =========================
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///sendit.db",
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # =========================
    # JWT
    # =========================
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-change-this-to-a-long-random-key",
    )

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    # =========================
    # CORS
    # =========================
    # Allow the Vercel frontend to communicate
    # with the Render backend.
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "*"
            }
        }
    )

    # =========================
    # INITIALIZE EXTENSIONS
    # =========================
    db.init_app(app)
    jwt.init_app(app)

    # =========================
    # ROUTES
    # =========================
    from app.routes.auth import auth_bp
    from app.routes.parcels import parcels_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(
        parcels_bp,
        url_prefix="/api/parcels"
    )

    app.register_blueprint(
        admin_bp,
        url_prefix="/api/admin"
    )

    # =========================
    # HEALTH CHECK
    # =========================
    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "sendit-api"
        })

    # =========================
    # DATABASE INITIALIZATION
    # =========================
    @app.cli.command("db-init")
    def db_init():
        from app.models import (
            User,
            Parcel,
            ParcelStatusHistory,
            ParcelLocation,
        )

        with app.app_context():
            db.create_all()
            print("Database tables created.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)