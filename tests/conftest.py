import pytest
from datetime import date, timedelta
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models.user import User, Role
from app.models.room import Room, RoomType, Amenity
from app.models.guest import Guest
from app.models.reservation import Reservation, ReservationRoom
from app.models.payment import Payment
from app.models.setting import HotelSetting


@pytest.fixture
def app():
    """Create and configure a clean testing app instance with an isolated database."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        # Seed roles
        admin_role = Role(name='Admin', description='Administrator')
        rec_role = Role(name='Receptionist', description='Receptionist')
        db.session.add_all([admin_role, rec_role])
        db.session.commit()

        # Seed users
        admin = User(
            username='admin_test',
            email='admin_test@grandhavenhotel.com',
            full_name='Test Admin',
            role_id=admin_role.id,
            is_active=True
        )
        admin.set_password('AdminTest@123')

        receptionist = User(
            username='rec_test',
            email='rec_test@grandhavenhotel.com',
            full_name='Test Receptionist',
            role_id=rec_role.id,
            is_active=True
        )
        receptionist.set_password('RecTest@123')

        inactive_user = User(
            username='inactive_test',
            email='inactive@grandhavenhotel.com',
            full_name='Inactive Staff',
            role_id=rec_role.id,
            is_active=False
        )
        inactive_user.set_password('Inactive@123')

        db.session.add_all([admin, receptionist, inactive_user])

        # Seed room types
        rt_std = RoomType(
            code='STD',
            name='Classic King Sanctuary',
            description='Test standard room',
            base_price=Decimal('150.00'),
            default_capacity=2,
            max_capacity=2,
            bed_type='1 King Bed'
        )
        rt_dlx = RoomType(
            code='DLX',
            name='Deluxe Oceanfront Haven',
            description='Test deluxe room',
            base_price=Decimal('250.00'),
            default_capacity=2,
            max_capacity=3,
            bed_type='1 King Bed + Daybed'
        )
        db.session.add_all([rt_std, rt_dlx])
        db.session.commit()

        # Seed rooms
        r101 = Room(room_number='101', room_type_id=rt_std.id, floor=1, capacity=2, operational_status='operational', is_active=True)
        r102 = Room(room_number='102', room_type_id=rt_std.id, floor=1, capacity=2, operational_status='operational', is_active=True)
        r201 = Room(room_number='201', room_type_id=rt_dlx.id, floor=2, capacity=3, operational_status='operational', is_active=True)
        r204 = Room(room_number='204', room_type_id=rt_dlx.id, floor=2, capacity=3, operational_status='maintenance', is_active=True)
        db.session.add_all([r101, r102, r201, r204])

        # Seed guest
        guest1 = Guest(
            first_name='Julian',
            last_name='Thorne',
            email='julian@test.com',
            phone='+91 9876543212',
            city='Bengaluru',
            state='Karnataka',
            country='India'
        )
        db.session.add(guest1)
        db.session.commit()

        # Seed settings
        HotelSetting.set_val('HOTEL_TAX_RATE', 0.12, 'float')
        HotelSetting.set_val('HOTEL_NAME', 'Grand Haven Hotel', 'string')
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()




class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='admin_test', password='AdminTest@123', next_page=None):
        url = '/login'
        if next_page is not None:
            from urllib.parse import urlencode
            url = f'{url}?{urlencode({"next": next_page})}'

        return self._client.post(
            url,
            data={'username': username, 'password': password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.post('/logout', follow_redirects=True)



@pytest.fixture
def auth(client):
    return AuthActions(client)



def login(self, username='admin_test', password='AdminTest@123', next_page=None):
    url = '/login'
    if next_page is not None:
        from urllib.parse import urlencode
        url = f'{url}?{urlencode({"next": next_page})}'

    return self._client.post(
        url,
        data={'username': username, 'password': password},
        follow_redirects=True
    )


    def logout(self):
        return self._client.get('/logout', follow_redirects=True)


@pytest.fixture
def auth(client):
    return AuthActions(client)
