"""
Validation utilities.
"""
import re
from typing import Tuple


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number format.

    Args:
        phone: Phone number string

    Returns:
        Tuple of (is_valid, cleaned_phone_or_error_message)
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)

    if not re.match(r"^\+?[\d]{10,15}$", cleaned):
        return False, "Phone number must be 10-15 digits"

    return True, cleaned


def validate_pincode(pincode: str) -> Tuple[bool, str]:
    """
    Validate pincode format.

    Args:
        pincode: Postal code string

    Returns:
        Tuple of (is_valid, cleaned_pincode_or_error_message)
    """
    cleaned = pincode.strip()

    if not re.match(r"^[\d]{5,10}$", cleaned):
        return False, "Pincode must be 5-10 digits"

    return True, cleaned


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email string

    Returns:
        Tuple of (is_valid, cleaned_email_or_error_message)
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, email.lower()


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password string

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    return True, ""


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Sanitize string input by stripping whitespace and limiting length.

    Args:
        text: Input string
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not text:
        return ""

    # Strip whitespace
    cleaned = text.strip()

    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned
