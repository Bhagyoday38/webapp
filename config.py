import os
from datetime import timedelta
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()


class Config:
    # Security: Ensure SECRET_KEY is set in your .env file in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'sqlite:///sarwatma.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'sqlite:///sarwatma.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # NEW: Database Encryption Key (Generate one using Fernet.generate_key() in production)
    ENCRYPTION_KEY = os.environ.get(
        'ENCRYPTION_KEY') or b'2P-6P2N6y7q2v4B9M_v2X7w7e6c9F2p5B9M_v2X7w7c='

    # Upload Settings
    UPLOAD_FOLDER = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Max 5MB file upload ceiling

    # Secure Cookie Settings
    IS_PROD = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_SECURE = IS_PROD         # Transmit over HTTPS only in production
    # Prevent client-side JS from reading the cookie
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'         # Mitigate CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    REMEMBER_COOKIE_SECURE = IS_PROD
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600             # Valid for 1 hour

    # Razorpay Gateway Keys
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
