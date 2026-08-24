import os
import uuid
from flask import request
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, PasswordField, URLField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional, ValidationError
from PIL import Image

# Initialize limiter instance (unattached)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def init_security(app):
    # Rate Limiting
    limiter.init_app(app)

    # Content Security Policy
    csp = {
        'default-src': "'self'",
        'base-uri': "'self'",
        'form-action': "'self'",
        'frame-ancestors': "'self'",
        'img-src': ["'self'", 'data:', 'https:'],
        'script-src': ["'self'", 'https://cdn.tailwindcss.com', "'unsafe-inline'"],
        'style-src': ["'self'", 'https://cdnjs.cloudflare.com', 'https://fonts.googleapis.com', "'unsafe-inline'"],
        'font-src': ["'self'", 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com'],
        'frame-src': [
            'https://www.google.com',
            'https://maps.google.com',
            'https://google.com',
            'https://api.razorpay.com',
            'https://checkout.razorpay.com'
        ],
        'connect-src': ["'self'", 'https://api.razorpay.com'],
    }

    # Security Headers via Talisman
    # REMOVED: content_type_nosniff=True (Talisman applies this by default)
    Talisman(
        app,
        content_security_policy=csp,
        force_https=app.config.get('SESSION_COOKIE_SECURE', False),
        strict_transport_security=app.config.get(
            'SESSION_COOKIE_SECURE', False),
        session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', False),
        session_cookie_http_only=True,
        frame_options='SAMEORIGIN'
    )

# ---------------------------------------------------------------------------
# Server-side Form Input Validation (WTForms)
# ---------------------------------------------------------------------------


class ContactForm(FlaskForm):
    # Enforce minimum and maximum string lengths to prevent buffer/DB overflow
    name = StringField('Name', validators=[
                       DataRequired(), Length(min=2, max=120)])
    # Enforce valid email format
    email = StringField('Email', validators=[DataRequired(), Email(
        message="Invalid email format"), Length(max=200)])
    message = TextAreaField('Message', validators=[
                            DataRequired(), Length(min=10, max=2000)])
    website = StringField('Website', validators=[
                          Optional(), Length(max=0)])  # Honeypot

    def validate_website(self, field):
        if field.data:
            raise ValidationError('Bot detected.')


class DonateForm(FlaskForm):
    donor_name = StringField('Full Name', validators=[
                             DataRequired(), Length(min=2, max=120)])
    donor_email = StringField(
        'Email', validators=[DataRequired(), Email(), Length(max=200)])
    donor_phone = StringField(
        'Phone', validators=[DataRequired(), Length(min=10, max=15)])
    # Enforce strict numeric ranges to prevent negative donations or integer overflows
    donation_amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(
        min=1, max=1_000_000, message="Amount must be between 1 and 1,000,000")])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(max=150)])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(max=200)])


_MAPS_HOST_ALLOWLIST = {'www.google.com', 'maps.google.com', 'google.com'}

# Custom Input Validation for URLs


def validate_map_url(form, field):
    if not field.data:
        return
    from urllib.parse import urlparse
    parsed = urlparse(field.data)

    # Enforce HTTPS
    if parsed.scheme != 'https':
        raise ValidationError('Map URL must start with https://')
    # Prevent arbitrary iframe injections (XSS mitigation)
    if parsed.hostname not in _MAPS_HOST_ALLOWLIST:
        raise ValidationError(
            'Map URL must originate from google.com or maps.google.com')
    if 'embed' not in field.data and 'output=embed' not in field.data:
        raise ValidationError(
            'Map URL must be a valid Google Maps embed link.')


class SettingsForm(FlaskForm):
    address = StringField('Address', validators=[Optional(), Length(max=300)])
    email = StringField('Contact Email', validators=[
                        Optional(), Email(), Length(max=200)])
    footer_text = StringField('Footer Text', validators=[
                              Optional(), Length(max=300)])
    map_url = URLField('Map Embed URL', validators=[
                       Optional(), validate_map_url])


class EventForm(FlaskForm):
    title = StringField('Title', validators=[
                        DataRequired(), Length(min=3, max=150)])
    event_date = StringField(
        'Date', validators=[DataRequired(), Length(min=4, max=100)])
    description = TextAreaField('Description', validators=[
                                DataRequired(), Length(min=10, max=2000)])

# ---------------------------------------------------------------------------
# Strict File Upload Validation & Random File Renaming
# ---------------------------------------------------------------------------


_ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB


def save_uploaded_image(file_storage, upload_dir):
    """
    Validates image header, byte structure, and file size.
    Generates a secure UUID filename to prevent directory traversal and file overwriting.
    """
    if not file_storage or not file_storage.filename:
        return None

    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            'Unsupported file extension. Allowed: JPG, JPEG, PNG, WEBP.')

    # Check file size before processing to prevent DoS via large files
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size > _MAX_UPLOAD_BYTES:
        raise ValueError('File size exceeds the 5MB limit.')
    if size == 0:
        raise ValueError('Uploaded file is empty.')

    # Verify actual image bytes using Pillow (protects against malicious scripts disguised as images)
    try:
        img = Image.open(file_storage)
        img.verify()
        file_storage.seek(0)
    except Exception:
        raise ValueError('Corrupted or invalid image file.')

    # Generate a cryptographically secure random filename
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(upload_dir, safe_filename)
    file_storage.save(dest_path)

    return safe_filename
