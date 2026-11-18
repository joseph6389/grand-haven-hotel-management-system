import pytest

from app import create_app
from app.config import DevelopmentConfig


def test_normal_app_requires_explicit_mysql_url(monkeypatch):
    monkeypatch.setattr(DevelopmentConfig, 'SQLALCHEMY_DATABASE_URI', None)

    with pytest.raises(RuntimeError, match='DATABASE_URL.*MySQL'):
        create_app('development')


def test_test_app_uses_isolated_sqlite_database():
    app = create_app('testing')

    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    assert app.config['SECRET_KEY'] == 'isolated-test-secret-key-not-for-deployment'
