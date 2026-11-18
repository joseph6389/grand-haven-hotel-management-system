from datetime import date, datetime, timedelta
from decimal import Decimal
from app.extensions import db
from app.models.user import User, Role
from app.models.room import Room, RoomType, Amenity
from app.models.guest import Guest
from app.models.reservation import Reservation, ReservationRoom, ReservationStatusHistory
from app.models.payment import Payment
from app.models.service import Service, ReservationService
from app.models.audit import AuditLog
from app.models.setting import HotelSetting


def seed_database():
    """Populate database with rich, realistic synthetic hotel dataset."""
    print("Beginning database seeding for Grand Haven Hotel...")

    # 1. ROLES
    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        admin_role = Role(name='Admin', description='Complete property administration and financial access')
        db.session.add(admin_role)

    rec_role = Role.query.filter_by(name='Receptionist').first()
    if not rec_role:
        rec_role = Role(name='Receptionist', description='Front desk operations, guest check-in/out, and reservations')
        db.session.add(rec_role)

    guest_role = Role.query.filter_by(name='Guest').first()
    if not guest_role:
        guest_role = Role(name='Guest', description='Guest reservation and profile self-service')
        db.session.add(guest_role)

    db.session.commit()

    # 2. USERS
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@grandhavenhotel.com',
            full_name='Alexander Vance',
            phone='+91 9876500001',
            role_id=admin_role.id,
            is_active=True
        )
        admin_user.set_password('Admin@123')
        db.session.add(admin_user)

    rec_user = User.query.filter_by(username='receptionist').first()
    if not rec_user:
        rec_user = User(
            username='receptionist',
            email='reception@grandhavenhotel.com',
            full_name='Elena Rostova',
            phone='+91 9876500002',
            role_id=rec_role.id,
            is_active=True
        )
        rec_user.set_password('Reception@123')
        db.session.add(rec_user)

    db.session.commit()

    # 3. AMENITIES
    amenities_data = [
        ('Oceanfront Balcony', 'bi-water', 'View'),
        ('King Featherbed', 'bi-moon-stars', 'Comfort'),
        ('High-Speed Fiber Wi-Fi', 'bi-wifi', 'Technology'),
        ('Marble Jacuzzi Tub', 'bi-droplet', 'Bathroom'),
        ('Nespresso Artisan Bar', 'bi-cup-hot', 'Refreshment'),
        ('65" 4K OLED Screen', 'bi-tv', 'Entertainment'),
        ('Dedicated Butler Service', 'bi-bell', 'Service'),
        ('Smart Climate Control', 'bi-snow', 'Comfort'),
        ('Rainfall Shower', 'bi-cloud-rain', 'Bathroom'),
        ('Mini Bar & Wine Cellar', 'bi-cup-straw', 'Refreshment'),
    ]
    amenity_objs = {}
    for name, icon, cat in amenities_data:
        am = Amenity.query.filter_by(name=name).first()
        if not am:
            am = Amenity(name=name, icon=icon, category=cat)
            db.session.add(am)
            db.session.flush()
        amenity_objs[name] = am

    db.session.commit()

    # 4. ROOM TYPES
    types_data = [
        {
            'code': 'STD',
            'name': 'Classic King Sanctuary',
            'description': 'A serene refuge featuring an imported king featherbed, warm walnut finishes, custom acoustic soundproofing, and a spa-inspired rainfall bath.',
            'base_price': Decimal('180.00'),
            'default_capacity': 2,
            'max_capacity': 2,
            'bed_type': '1 King Bed',
            'image_url': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80',
            'amenities': ['King Featherbed', 'High-Speed Fiber Wi-Fi', 'Rainfall Shower', 'Nespresso Artisan Bar', 'Smart Climate Control']
        },
        {
            'code': 'DLX',
            'name': 'Deluxe Oceanfront Haven',
            'description': 'Panoramic floor-to-ceiling coastal vistas overlooking the Atlantic breakers. Features private terrace, oversized marble bathroom, and artisan bar.',
            'base_price': Decimal('260.00'),
            'default_capacity': 2,
            'max_capacity': 3,
            'bed_type': '1 King Bed + Daybed',
            'image_url': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80',
            'amenities': ['Oceanfront Balcony', 'King Featherbed', 'High-Speed Fiber Wi-Fi', 'Marble Jacuzzi Tub', '65" 4K OLED Screen', 'Nespresso Artisan Bar']
        },
        {
            'code': 'STE',
            'name': 'Grand Harbor Executive Suite',
            'description': 'Expansive residential luxury featuring separated entertaining salon, master bedroom suite, dual vanity dressing room, and bespoke hospitality lounge.',
            'base_price': Decimal('420.00'),
            'default_capacity': 3,
            'max_capacity': 4,
            'bed_type': '1 King + Living Sofa Bed',
            'image_url': 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80',
            'amenities': ['Oceanfront Balcony', 'King Featherbed', 'High-Speed Fiber Wi-Fi', 'Marble Jacuzzi Tub', '65" 4K OLED Screen', 'Dedicated Butler Service', 'Mini Bar & Wine Cellar']
        },
        {
            'code': 'PRE',
            'name': 'Presidential Panorama Penthouse',
            'description': 'The pinnacle of Grand Haven hospitality. Private rooftop glass terrace, 360-degree ocean views, dining parlor for eight, and private butler service.',
            'base_price': Decimal('850.00'),
            'default_capacity': 4,
            'max_capacity': 6,
            'bed_type': '2 King Beds + Master Parlor',
            'image_url': 'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=1000&q=80',
            'amenities': ['Oceanfront Balcony', 'King Featherbed', 'High-Speed Fiber Wi-Fi', 'Marble Jacuzzi Tub', '65" 4K OLED Screen', 'Dedicated Butler Service', 'Mini Bar & Wine Cellar', 'Smart Climate Control']
        }
    ]

    type_objs = {}
    for td in types_data:
        rt = RoomType.query.filter_by(code=td['code']).first()
        if not rt:
            rt = RoomType(
                code=td['code'],
                name=td['name'],
                description=td['description'],
                base_price=td['base_price'],
                default_capacity=td['default_capacity'],
                max_capacity=td['max_capacity'],
                bed_type=td['bed_type'],
                image_url=td['image_url']
            )
            db.session.add(rt)
            db.session.flush()
        type_objs[td['code']] = rt

    db.session.commit()

    # 5. PHYSICAL ROOMS (16 rooms across floors 1-4)
    rooms_seed = [
        # Floor 1
        ('101', 'STD', 1, 2, 'operational', 'Quiet garden facing room'),
        ('102', 'STD', 1, 2, 'operational', 'Convenient ground level access'),
        ('103', 'DLX', 1, 3, 'operational', 'Direct beach access terrace'),
        ('104', 'DLX', 1, 3, 'operational', 'Garden and ocean horizon blend'),
        # Floor 2
        ('201', 'STD', 2, 2, 'operational', 'Elevated ocean breeze view'),
        ('202', 'STD', 2, 2, 'operational', 'Contemporary interior finish'),
        ('203', 'DLX', 2, 3, 'operational', 'Full unobstructed oceanfront view'),
        ('204', 'DLX', 2, 3, 'maintenance', 'Scheduled plumbing overhaul (demo maintenance filter)'),
        # Floor 3
        ('301', 'DLX', 3, 3, 'operational', 'Panoramic sea vista'),
        ('302', 'DLX', 3, 3, 'operational', 'Corner suite perspective'),
        ('303', 'STE', 3, 4, 'operational', 'Executive corner suite with dual wrap balcony'),
        ('304', 'STE', 3, 4, 'operational', 'Luxury living parlor suite'),
        # Floor 4
        ('401', 'STE', 4, 4, 'operational', 'Top-floor harbor executive suite'),
        ('402', 'STE', 4, 4, 'operational', 'High-ceiling master salon suite'),
        ('403', 'PRE', 4, 6, 'operational', 'The Grand Haven Presidential Penthouse'),
        ('404', 'PRE', 4, 6, 'operational', 'The Royal Ocean Pavilion Penthouse'),
    ]

    room_map = {}
    for r_num, t_code, flr, cap, op_stat, notes in rooms_seed:
        rm = Room.query.filter_by(room_number=r_num).first()
        if not rm:
            rm = Room(
                room_number=r_num,
                room_type_id=type_objs[t_code].id,
                floor=flr,
                capacity=cap,
                operational_status=op_stat,
                is_active=True,
                notes=notes
            )
            # Assign amenities
            req_amenities = types_data[[d['code'] for d in types_data].index(t_code)]['amenities']
            rm.amenities = [amenity_objs[a] for a in req_amenities if a in amenity_objs]
            db.session.add(rm)
            db.session.flush()
        room_map[r_num] = rm

    db.session.commit()

    # 6. GUESTS
    guests_seed = [
        ('Julian', 'Thorne', 'julian.thorne@example.com', '+91 9876500011', '12 Example Residency', 'Bengaluru', 'India', 'Passport', 'P9841203A'),
        ('Vivienne', 'St. Claire', 'vivienne.stclaire@example.com', '+91 9876500012', '24 Lake View Road', 'Mysuru', 'India', 'Passport', 'P7739102B'),
        ('Marcus', 'Sterling', 'marcus.sterling@example.com', '+91 9876500013', '8 Market Street', 'Kochi', 'India', 'Passport', 'GB8821901'),
        ('Sophia', 'Chen', 'sophia.chen@example.com', '+91 9876500014', '16 Garden Lane', 'Chennai', 'India', 'Driver License', 'BC-4491029'),
        ('Liam', 'Gallagher', 'liam.gallagher@example.com', '+91 9876500015', '31 Residency Road', 'Bengaluru', 'India', 'Passport', 'IE5512903'),
        ('Dr. Aris', 'Vanderbilt', 'aris.vanderbilt@example.com', '+91 9876500016', '5 Hill View', 'Pune', 'India', 'Passport', 'P1298402X'),
        ('Camille', 'Dupont', 'camille.dupont@example.com', '+91 9876500017', '19 Riverside Avenue', 'Kochi', 'India', 'Passport', 'FR9021482'),
        ('Hiroshi', 'Tanaka', 'hiroshi.tanaka@example.com', '+91 9876500018', '42 Park Street', 'Kolkata', 'India', 'Passport', 'JP7749102')
    ]

    guest_objs = []
    indian_states = {
        'Bengaluru': 'Karnataka', 'Mysuru': 'Karnataka', 'Kochi': 'Kerala',
        'Chennai': 'Tamil Nadu', 'Pune': 'Maharashtra', 'Kolkata': 'West Bengal',
    }
    for fn, ln, em, ph, addr, city, ctry, id_t, id_n in guests_seed:
        g = Guest.query.filter_by(email=em).first()
        if not g:
            g = Guest(
                first_name=fn,
                last_name=ln,
                email=em,
                phone=ph,
                address=addr,
                city=city,
                state=indian_states.get(city),
                country=ctry,
                identification_type=id_t,
                identification_number=id_n
            )
            db.session.add(g)
            db.session.flush()
        guest_objs.append(g)

    db.session.commit()

    # 7. EXTRA SERVICES
    services_seed = [
        ('Airport Luxury Chauffeur', 'Private Mercedes S-Class transfer between airport and hotel', Decimal('85.00')),
        ('Couples Ocean Spa Ritual', '90-minute aromatherapy massage overlooking the sea', Decimal('190.00')),
        ('Champagne Breakfast Buffet', 'Artisan bakery, caviar station, and vintage champagne service', Decimal('45.00')),
        ('Valet Parking Service', 'Secured 24-hour underground valet parking', Decimal('30.00')),
        ('Private Yacht Sunset Charter', '2-hour private yacht cruise along the coastline', Decimal('450.00'))
    ]
    for s_name, s_desc, s_price in services_seed:
        s = Service.query.filter_by(name=s_name).first()
        if not s:
            s = Service(name=s_name, description=s_desc, unit_price=s_price, is_active=True)
            db.session.add(s)

    db.session.commit()

    # 8. RESERVATIONS & PAYMENTS (Synthetic historical & active reservations)
    from app.utils.datetime_utils import india_today
    today = india_today()
    reservations_data = [
        # Past Completed 1
        {
            'conf': 'GH-20260901-7A1C',
            'guest': guest_objs[0],
            'room': room_map['101'],
            'check_in': today - timedelta(days=25),
            'check_out': today - timedelta(days=21),
            'adults': 2,
            'children': 0,
            'status': 'checked_out',
            'paid_full': True,
            'requests': 'High floor preferred, late arrival.'
        },
        # Past Completed 2
        {
            'conf': 'GH-20260910-3F8E',
            'guest': guest_objs[1],
            'room': room_map['303'],
            'check_in': today - timedelta(days=15),
            'check_out': today - timedelta(days=12),
            'adults': 2,
            'children': 1,
            'status': 'checked_out',
            'paid_full': True,
            'requests': 'Celebrating wedding anniversary. Chilled champagne in suite.'
        },
        # Currently Checked-In (Active today)
        {
            'conf': 'GH-20261014-9B2D',
            'guest': guest_objs[2],
            'room': room_map['203'],
            'check_in': today - timedelta(days=2),
            'check_out': today + timedelta(days=2),
            'adults': 2,
            'children': 0,
            'status': 'checked_in',
            'paid_full': True,
            'requests': 'Extra feather pillows requested.'
        },
        # Currently Checked-In (Active today)
        {
            'conf': 'GH-20261015-4E1A',
            'guest': guest_objs[3],
            'room': room_map['403'],
            'check_in': today - timedelta(days=1),
            'check_out': today + timedelta(days=3),
            'adults': 4,
            'children': 0,
            'status': 'checked_in',
            'paid_full': True,
            'requests': 'Presidential butler orientation requested.'
        },
        # Future Confirmed 1 (Arrival in 2 days)
        {
            'conf': 'GH-20261018-8A3F',
            'guest': guest_objs[4],
            'room': room_map['103'],
            'check_in': today + timedelta(days=2),
            'check_out': today + timedelta(days=6),
            'adults': 2,
            'children': 0,
            'status': 'confirmed',
            'paid_full': True,
            'requests': 'Airport transfer booking required.'
        },
        # Future Confirmed 2 (Arrival in 4 days)
        {
            'conf': 'GH-20261020-5C2B',
            'guest': guest_objs[5],
            'room': room_map['304'],
            'check_in': today + timedelta(days=4),
            'check_out': today + timedelta(days=8),
            'adults': 3,
            'children': 1,
            'status': 'confirmed',
            'paid_full': False,  # Partially paid (50% deposit)
            'requests': 'Child cot and baby highchair required.'
        },
        # Cancelled Reservation (Demonstrates cancellation audit and free availability)
        {
            'conf': 'GH-20261016-1D9X',
            'guest': guest_objs[6],
            'room': room_map['201'],
            'check_in': today + timedelta(days=1),
            'check_out': today + timedelta(days=4),
            'adults': 2,
            'children': 0,
            'status': 'cancelled',
            'paid_full': False,
            'requests': 'Flight cancelled due to storm.'
        }
    ]

    tax_rate = Decimal('0.12')

    for rdata in reservations_data:
        res = Reservation.query.filter_by(confirmation_number=rdata['conf']).first()
        if not res:
            nights = (rdata['check_out'] - rdata['check_in']).days
            rate = Decimal(str(rdata['room'].price_per_night))
            room_charges = rate * Decimal(nights)
            tax_amt = (room_charges * tax_rate).quantize(Decimal('0.01'))
            total_amt = room_charges + tax_amt

            if rdata['paid_full']:
                paid_amt = total_amt
            elif rdata['status'] == 'cancelled':
                paid_amt = Decimal('0.00')
            else:
                paid_amt = (total_amt / 2).quantize(Decimal('0.01'))

            res = Reservation(
                confirmation_number=rdata['conf'],
                guest_id=rdata['guest'].id,
                check_in_date=rdata['check_in'],
                check_out_date=rdata['check_out'],
                adults_count=rdata['adults'],
                children_count=rdata['children'],
                tax_amount=tax_amt,
                discount_amount=Decimal('0.00'),
                status=rdata['status'],
                special_requests=rdata['requests'],
                created_by_id=admin_user.id
            )
            db.session.add(res)
            db.session.flush()

            # Room Allocation
            alloc = ReservationRoom(
                reservation_id=res.id,
                room_id=rdata['room'].id,
                nightly_rate=rate,
                nights=nights,
            )
            db.session.add(alloc)

            # History
            hist = ReservationStatusHistory(
                reservation_id=res.id,
                previous_status=None,
                new_status=rdata['status'],
                changed_by_id=admin_user.id,
                reason="Synthetic initial population"
            )
            db.session.add(hist)

            # Payment
            if paid_amt > Decimal('0.00'):
                pay = Payment(
                    reservation_id=res.id,
                    payment_reference=f"PAY-{res.confirmation_number.replace('GH-', '')}-1",
                    amount=paid_amt,
                    currency='INR',
                    payment_method='credit_card',
                    payment_status='paid',
                    transaction_reference=f"SIM-TXN-SEED-{res.id}",
                    notes="Synthetic seed payment transaction",
                    processed_by_id=admin_user.id
                )
                db.session.add(pay)

    db.session.commit()

    # 9. HOTEL SETTINGS
    HotelSetting.set_val('HOTEL_NAME', 'Grand Haven Hotel', 'string', 'Hotel property brand name')
    HotelSetting.set_val('HOTEL_EMAIL', 'reservations@grandhavenhotel.com', 'string', 'Contact email')
    HotelSetting.set_val('HOTEL_PHONE', '', 'string', 'Front desk phone (configure the verified hotel contact)')
    HotelSetting.set_val('HOTEL_CURRENCY', 'INR', 'string', 'Currency code (ISO 4217)')
    HotelSetting.set_val('HOTEL_TAX_RATE', 0.12, 'float', 'Default lodging tax rate')
    HotelSetting.set_val('DEFAULT_CHECKIN_TIME', '15:00', 'string', 'Check-in time')
    HotelSetting.set_val('DEFAULT_CHECKOUT_TIME', '11:00', 'string', 'Check-out time')
    HotelSetting.set_val('CANCELLATION_POLICY', 'Full refund available if cancelled 48 hours before check-in date.', 'string', 'Terms')
    db.session.commit()

    print("Database seeding completed successfully!")
