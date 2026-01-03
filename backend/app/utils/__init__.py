"""
==============================================================================
Utils Package (utils/__init__.py)
==============================================================================

PURPOSE:
--------
This package contains utility functions for the ShopEase app.
These are reusable, pure functions with no side effects.

AVAILABLE UTILITIES:
--------------------
1. validators.py - Input validation functions
   - validate_phone: Validate and normalize phone numbers
   - validate_pincode: Validate postal codes
   - validate_email: Validate email format
   - validate_password_strength: Check password requirements
   - sanitize_string: Clean and truncate strings

USAGE:
------
    from app.utils import validate_phone, validate_pincode

    is_valid, result = validate_phone("987-654-3210")
    if is_valid:
        phone = result  # Cleaned phone number
    else:
        error = result  # Error message

NOTE:
-----
Most validation in this app is done by Pydantic models.
These utilities are for cases where you need validation
outside of Pydantic, or want consistent standalone functions.
"""

from .validators import validate_phone, validate_pincode

# Public exports for "from app.utils import ..."
__all__ = ["validate_phone", "validate_pincode"]
