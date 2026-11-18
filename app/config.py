import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')



class Config:
    """Base application configuration."""

    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Local development uses HTTP



    # Normal application operation must use explicitly configured MySQL.
    # Tests override this with an isolated in-memory SQLite database below.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Hotel Business Settings Defaults
    HOTEL_NAME = os.environ.get('HOTEL_NAME', 'Grand Haven Hotel')
    HOTEL_EMAIL = os.environ.get('HOTEL_EMAIL', 'reservations@grandhavenhotel.com')
    HOTEL_PHONE = os.environ.get('HOTEL_PHONE', '')
    HOTEL_ADDRESS = os.environ.get('HOTEL_ADDRESS', '')
    HOTEL_TIMEZONE = os.environ.get('HOTEL_TIMEZONE', 'Asia/Kolkata').strip()
    HOTEL_CURRENCY = os.environ.get('HOTEL_CURRENCY', 'INR').strip().upper()
    HOTEL_CURRENCY_SYMBOL = '₹'
    HOTEL_TAX_RATE = float(os.environ.get('HOTEL_TAX_RATE', 0.12))  # 12% default tax
    DEFAULT_CHECKIN_TIME = os.environ.get('DEFAULT_CHECKIN_TIME', '15:00')
    DEFAULT_CHECKOUT_TIME = os.environ.get('DEFAULT_CHECKOUT_TIME', '11:00')
    CANCELLATION_DEADLINE_DAYS = int(os.environ.get('CANCELLATION_DEADLINE_DAYS', 2))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration with in-memory or isolated test database."""
    TESTING = True
    DEBUG = False
    # Tests must run without depending on a developer's ignored .env file.
    SECRET_KEY = 'isolated-test-secret-key-not-for-deployment'
    HOTEL_CURRENCY = 'INR'
    HOTEL_TIMEZONE = 'Asia/Kolkata'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False



class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    # Validated in create_app so importing the module remains safe for tooling.







config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
