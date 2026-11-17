from flask import Flask, session
from .config import Config
from .models import db, ProfilMember, AkunPengunjung, SimulatedEmail


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Template filters
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            return f"Rp {int(value):,}".replace(',', '.')
        except (ValueError, TypeError):
            return "Rp 0"

    @app.template_filter('format_date')
    def format_date_filter(value, fmt='%d %b %Y'):
        if not value:
            return '-'
        return value.strftime(fmt)

    @app.template_filter('format_datetime')
    def format_datetime_filter(value, fmt='%d %b %Y %H:%M'):
        if not value:
            return '-'
        return value.strftime(fmt)

    # Context processor untuk peran demo dan info global
    @app.context_processor
    def inject_global_context():
        current_role = session.get('current_role', 'Calon Penumpang')
        demo_roles = [
            'Manajer HRD',
            'Calon Penumpang',
            'Member Frequent Traveller',
            'Manajer Travel',
            'Pengunjung'
        ]
        unread_emails_count = SimulatedEmail.query.count() if db.session else 0

        # Ambil profil member demo default
        default_member = ProfilMember.query.first()
        # Ambil akun pengunjung demo default
        default_visitor = AkunPengunjung.query.first()

        return dict(
            current_role=current_role,
            demo_roles=demo_roles,
            unread_emails_count=unread_emails_count,
            default_member=default_member,
            default_visitor=default_visitor
        )

    # Register Blueprints
    from .routes.main_routes import main_bp
    from .routes.leave_routes import leave_bp
    from .routes.flight_routes import flight_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(leave_bp, url_prefix='/leave')
    app.register_blueprint(flight_bp, url_prefix='/flight')

    return app
