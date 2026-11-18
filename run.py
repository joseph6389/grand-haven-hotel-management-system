
import os
import click
from dotenv import load_dotenv

load_dotenv()

from app import create_app

from app.extensions import db
from database.seed_data import seed_database

app = create_app(os.environ.get('FLASK_ENV', 'development'))


@app.cli.command('init-db')
def init_db_command():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        click.echo("Initialized database tables successfully.")


@app.cli.command('seed-db')
def seed_db_command():
    """Seed synthetic sample hotel dataset."""
    with app.app_context():
        db.create_all()
        seed_database()
        click.echo("Database seeded successfully with demo records.")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    app.run(host=host, port=port, debug=debug)
