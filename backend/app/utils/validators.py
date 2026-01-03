"""
==============================================================================
Validation Utilities (validators.py)
==============================================================================

PURPOSE:
--------
This module provides reusable validation functions for user input.
These are standalone functions that can be used anywhere in the app.

WHY SEPARATE VALIDATORS?
------------------------
1. Reusability: Same validation logic used in multiple places
2. Consistency: All phone validation uses same rules
3. Testing: Easy to unit test validation functions
4. Flexibility: Can be used outside Pydantic models

VALIDATION PATTERN:
-------------------
All validators return a Tuple[bool, str]:
- (True, cleaned_value) on success
- (False, error_message) on failure

This allows callers to get both validation status and cleaned/error value.

Example:
    is_valid, result = validate_phone("  987-654-3210  ")
    if is_valid:
        phone = result  # "9876543210"
    else:
        error = result  # "Phone number must be..."

NOTE ON PYDANTIC:
-----------------
These validators are COMPLEMENTARY to Pydantic validation:
- Pydantic field_validators are used in models
- These functions can be used in routes or services
- Pydantic EmailStr handles email - validate_email here is optional

INDIAN FORMATS:
---------------
- Phone: 10 digits (mobile), with optional +91 country code
- Pincode: 6 digits (we accept 5-10 for international)
"""

import re
from typing import Tuple


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate and normalize phone number format.

    Accepts:
    - 9876543210 (10 digits)
    - +91 9876543210 (with country code)
    - 987-654-3210 (with dashes)
    - (98) 7654-3210 (with parentheses)

    Process:
    1. Remove spaces, dashes, parentheses
    2. Check for 10-15 digits (optional + prefix)
    3. Return cleaned number

    Args:
        phone: Phone number string (any format)

    Returns:
        (True, cleaned_phone) - on success
        (False, error_message) - on failure

    Examples:
        validate_phone("987-654-3210") -> (True, "9876543210")
        validate_phone("123") -> (False, "Phone number must be 10-15 digits")
    """
    # Remove formatting characters
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)

    # Validate: 10-15 digits with optional + prefix
    if not re.match(r"^\+?[\d]{10,15}$", cleaned):
        return False, "Phone number must be 10-15 digits"

    return True, cleaned


def validate_pincode(pincode: str) -> Tuple[bool, str]:
    """
    Validate postal code / pincode format.

    Indian pincodes are 6 digits.
    We accept 5-10 digits to support international formats.

    Args:
        pincode: Postal code string

    Returns:
        (True, cleaned_pincode) - on success
        (False, error_message) - on failure

    Examples:
        validate_pincode("400001") -> (True, "400001")
        validate_pincode("12") -> (False, "Pincode must be 5-10 digits")
    """
    cleaned = pincode.strip()

    if not re.match(r"^[\d]{5,10}$", cleaned):
        return False, "Pincode must be 5-10 digits"

    return True, cleaned


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    Uses a standard email regex pattern.
    For production, consider using email-validator library.

    Note: Pydantic's EmailStr does this better.
    This is here for use outside Pydantic models.

    Args:
        email: Email string

    Returns:
        (True, lowercase_email) - on success
        (False, error_message) - on failure

    Examples:
        validate_email("User@Example.COM") -> (True, "user@example.com")
        validate_email("invalid") -> (False, "Invalid email format")
    """
    # Standard email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False, "Invalid email format"

    # Return lowercase for consistency
    return True, email.lower()


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets strength requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)

    These rules balance security with usability.
    Consider adding special character requirement for higher security.

    Args:
        password: Password string

    Returns:
        (True, "") - on success (empty string, no error)
        (False, error_message) - on failure

    Examples:
        validate_password_strength("SecurePass123") -> (True, "")
        validate_password_strength("weak") -> (False, "Password must be at least 8 characters")
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

    Use this for user-provided text that will be stored or displayed.
    Prevents excessively long inputs from causing issues.

    Args:
        text: Input string (can be None)
        max_length: Maximum allowed length (default 500)

    Returns:
        Sanitized string (stripped and truncated)

    Examples:
        sanitize_string("  Hello World  ") -> "Hello World"
        sanitize_string("x" * 1000, max_length=10) -> "xxxxxxxxxx"
        sanitize_string(None) -> ""

    Note:
        This does NOT sanitize for HTML/XSS.
        Use proper HTML escaping when rendering user content.
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    cleaned = text.strip()

    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned
