from flask import Flask, render_template
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf
from app.utils.datetime_utils import utcnow, format_india_datetime, format_india_date
from app.routes import (
    public_bp,
    auth_bp,
    dashboard_bp,
    rooms_bp,
    guests_bp,
    reservations_bp,
    payments_bp,
    reports_bp,
    admin_bp,
    api_bp,
    account_bp,
)


def create_app(config_name='development'):
    """Application factory for Grand Haven Hotel Reservation Management System."""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    cfg = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(cfg)
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if config_name != 'testing' and not (database_uri or '').startswith('mysql+'):
        raise RuntimeError(
            'Set DATABASE_URL to a MySQL connection string before starting the application.'
        )
    if config_name == 'production' and not app.config.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY must be set before starting in production.')
    if app.config.get('HOTEL_CURRENCY') != 'INR':
        raise RuntimeError('This India-localized hotel application requires HOTEL_CURRENCY=INR.')
    if app.config.get('HOTEL_TIMEZONE') != 'Asia/Kolkata':
        raise RuntimeError('This India-localized hotel application requires HOTEL_TIMEZONE=Asia/Kolkata.')
    app.url_map.strict_slashes = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)



    # Register blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(guests_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(account_bp)

    # Register Jinja template global filters & variables
    @app.context_processor
    def inject_global_data():
        return {
            'hotel_name': app.config.get('HOTEL_NAME', 'Grand Haven Hotel'),
            'hotel_email': app.config.get('HOTEL_EMAIL', 'reservations@grandhavenhotel.com'),
            'hotel_phone': app.config.get('HOTEL_PHONE', ''),
            'hotel_address': app.config.get('HOTEL_ADDRESS', ''),
            'hotel_currency': app.config.get('HOTEL_CURRENCY', 'INR'),
            'hotel_currency_symbol': app.config.get('HOTEL_CURRENCY_SYMBOL', '₹'),
            'current_year': utcnow().year
        }

    @app.template_filter('currency')
    def currency_filter(val):
        try:
            symbol = app.config.get('HOTEL_CURRENCY_SYMBOL', '₹')
            return f"{symbol}{float(val):,.2f}"
        except (ValueError, TypeError):
            return f"{app.config.get('HOTEL_CURRENCY_SYMBOL', '₹')}0.00"

    app.add_template_filter(format_india_datetime, 'india_datetime')
    app.add_template_filter(format_india_date, 'india_date')

    @app.template_filter('status_badge')
    def status_badge_filter(status):
        badges = {
            'confirmed': 'bg-success text-white',
            'checked_in': 'bg-primary text-white',
            'checked_out': 'bg-secondary text-white',
            'cancelled': 'bg-danger text-white',
            'pending': 'bg-warning text-dark',
            'operational': 'bg-success text-white',
            'maintenance': 'bg-warning text-dark',
            'out_of_order': 'bg-danger text-white',
            'paid': 'bg-success text-white',
            'partially_paid': 'bg-warning text-dark',
            'unpaid': 'bg-danger text-white',
            'refunded': 'bg-info text-dark',
        }
        return badges.get(str(status).lower(), 'bg-secondary text-white')

    # Centralized error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app
