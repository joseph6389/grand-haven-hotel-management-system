from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Configure login view and message
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access the management portal.'
login_manager.login_message_category = 'warning'
