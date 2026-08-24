import os
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Import Encryption tools
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

# Define a 32-byte encryption key (In production, load this from your .env file)
DB_ENCRYPTION_KEY = os.environ.get(
    'DB_ENCRYPTION_KEY', 'default-32-byte-secret-key-12345')


class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        # This securely hashes the password using scrypt
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(100), nullable=False)

    # Store email and phone completely encrypted in the SQLite database
    donor_email = db.Column(StringEncryptedType(
        db.String(255), DB_ENCRYPTION_KEY, AesEngine, 'pkcs5'), nullable=False)
    donor_phone = db.Column(StringEncryptedType(
        db.String(255), DB_ENCRYPTION_KEY, AesEngine, 'pkcs5'), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    payment_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    image_url = db.Column(db.String(300))

# --- NEW: Global Settings (For Addresses, Emails, Footer) ---


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)


class CarouselImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(300))


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))
