from pathlib import Path

from app.utils.india import normalize_indian_contact, normalize_indian_phone


def test_currency_is_inr_and_displays_rupee(app):
    assert app.config['HOTEL_CURRENCY'] == 'INR'
    assert app.jinja_env.filters['currency'](1500) == '₹1,500.00'


def test_indian_mobile_normalization():
    assert normalize_indian_phone('98765 43210') == '+919876543210'
    assert normalize_indian_phone('09123456789') == '+919123456789'
    assert normalize_indian_phone('+1 555 0100') is None
    assert normalize_indian_contact('+91 80 1234 5678') == '+918012345678'


def test_guest_policy_copy_is_action_specific_and_financial_displays_are_localized():
    root = Path(__file__).resolve().parents[1]
    search = (root / 'app/templates/public/search_results.html').read_text(encoding='utf-8')
    voucher = (root / 'app/templates/reservations/voucher.html').read_text(encoding='utf-8')
    confirmation = (root / 'app/templates/public/confirmation.html').read_text(encoding='utf-8')
    templates = '\n'.join(path.read_text(encoding='utf-8') for path in (root / 'app/templates').rglob('*.html'))
    assert 'I accept the' not in search
    assert 'Cancellation policy:' in search
    assert 'Stay information:' in voucher
    assert 'Cancellation Policy:' in confirmation
    assert 'Terms & Policies' not in templates
    assert 'USD' not in templates
    assert '$' not in templates
