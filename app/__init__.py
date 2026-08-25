import os
import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from app.security import init_security

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    template_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'templates'
    )
    static_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'static'
    )

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize Core Extensions
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'admin_bp.login'
    login_manager.session_protection = 'strong'

    csrf.init_app(app)

    # Initialize Security: Limiter & Talisman
    init_security(app)

    # Context Processor for Global Settings
    @app.context_processor
    def inject_settings():
        from .models import Setting

        try:
            settings_data = {
                s.key: s.value
                for s in Setting.query.all()
            }
        except Exception:
            settings_data = {}

        return dict(settings=settings_data)

    # Register Blueprints
    from app.routes import public_bp
    from app.admin import admin_bp
    from app.payments import payment_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payment_bp, url_prefix='/payment')

    with app.app_context():
        db.create_all()

    # --------------------------------------------------
    # Flask CLI command: create/set admin password
    # --------------------------------------------------
    @app.cli.command("set-admin-password")
    @click.option(
        "--username",
        default="admin@gmail.com",
        help="Admin username/email."
    )
    def set_admin_password(username):
        """Create an admin or change an existing admin password."""

        from app.models import AdminUser

        admin = AdminUser.query.filter_by(username=username).first()

        if not admin:
            admin = AdminUser(username=username)
            db.session.add(admin)

            click.echo(f"Creating admin account: {username}")

        else:
            click.echo(f"Changing password for: {username}")

        password = click.prompt(
            "Enter password",
            hide_input=True,
            confirmation_prompt=True
        )

        if len(password) < 8:
            click.echo("Password must be at least 8 characters.")
            return

        admin.set_password(password)

        db.session.commit()

        click.echo(f"Admin password successfully set for {username}.")

    return app
