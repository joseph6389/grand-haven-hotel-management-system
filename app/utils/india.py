import re


def normalize_indian_phone(value: str) -> str | None:
    """Normalize a ten-digit Indian mobile to +91 E.164-like display form."""
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10 or digits[0] not in '6789':
        return None
    return f'+91{digits}'


def normalize_indian_contact(value: str) -> str | None:
    """Normalize a ten-digit Indian mobile or landline contact to +91 form."""
    mobile = normalize_indian_phone(value)
    if mobile:
        return mobile
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in '12345':
        return f'+91{digits}'
    return None
