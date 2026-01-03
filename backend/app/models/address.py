"""
==============================================================================
Address Models (address.py)
==============================================================================

PURPOSE:
--------
This module defines Pydantic models for shipping address management:
- Creating new addresses
- Updating existing addresses
- Displaying addresses in checkout and profile

ADDRESS ARCHITECTURE:
---------------------
Each user can have multiple addresses stored in Firestore:
    addresses/{address_id}:
        user_id: "user123"
        full_name: "John Doe"
        phone: "9876543210"
        address_line1: "123 Main Street"
        city: "Mumbai"
        state: "Maharashtra"
        pincode: "400001"
        country: "India"
        address_type: "home"
        is_default: true

WHY SEPARATE ADDRESSES?
-----------------------
1. E-commerce apps often ship to addresses different from billing
2. Users may have home, work, and other delivery locations
3. Gift deliveries go to recipient's address
4. "is_default" allows quick checkout with preferred address

INDIAN ADDRESS FORMAT:
----------------------
Indian addresses typically include:
- Address Line 1: House/flat number, building name
- Address Line 2: Street, locality (optional)
- Landmark: Near famous place (common in India for delivery)
- City: City/town name
- State: State/territory name
- Pincode: 6-digit postal code (validated)
- Country: Defaults to India

PINCODE VALIDATION:
-------------------
Indian pincodes are 6 digits:
- First digit: Region (1-9)
- Second digit: Sub-region
- Third digit: Sorting district
- Last 3: Specific post office

We validate 5-10 digits to support international formats too.

DUPLICATE PREVENTION:
---------------------
The AddressRepository normalizes addresses before saving
to prevent duplicates (same address saved multiple times).
Normalization: lowercase, remove extra spaces, normalize phone.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


# ==============================================================================
# ADDRESS CREATE MODEL
# ==============================================================================
class AddressCreate(BaseModel):
    """
    Model for creating a new shipping address.

    Used when user adds a new address in profile or checkout.
    All required fields must be provided for successful delivery.

    Example JSON:
        {
            "full_name": "John Doe",
            "phone": "9876543210",
            "address_line1": "Flat 101, Sunshine Apartments",
            "address_line2": "MG Road",
            "landmark": "Near City Mall",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "country": "India",
            "address_type": "home",
            "is_default": true
        }
    """

    # Recipient info (may differ from user's profile)
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Recipient full name (for delivery label)"
    )
    phone: str = Field(
        ...,
        max_length=15,
        description="Contact phone for delivery updates"
    )

    # Address details
    address_line1: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Primary address (house no, building, street)"
    )
    address_line2: Optional[str] = Field(
        None,
        max_length=200,
        description="Secondary address (locality, area)"
    )
    landmark: Optional[str] = Field(
        None,
        max_length=100,
        description="Nearby landmark (common in India for directions)"
    )

    # Location
    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="City or town name"
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="State or province"
    )
    pincode: str = Field(
        ...,
        min_length=5,
        max_length=10,
        description="Postal/ZIP code (6 digits for India)"
    )
    country: str = Field(
        "India",
        max_length=100,
        description="Country (defaults to India)"
    )

    # Classification
    address_type: str = Field(
        "home",
        description="Type: 'home', 'work', or 'other'"
    )
    is_default: bool = Field(
        False,
        description="Set as default for quick checkout"
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        Validate and normalize phone number.

        Indian mobile numbers:
        - 10 digits starting with 6-9
        - May include +91 prefix

        Process:
        1. Remove spaces and dashes
        2. Check for 10-15 digits (with optional +)
        3. Return cleaned number

        Args:
            v: Phone number string

        Returns:
            Cleaned phone number

        Raises:
            ValueError: If format is invalid
        """
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """
        Validate pincode/postal code format.

        Indian pincodes are exactly 6 digits.
        We allow 5-10 to support international formats.

        Args:
            v: Pincode string

        Returns:
            Trimmed pincode

        Raises:
            ValueError: If format is invalid
        """
        cleaned = v.strip()
        if not re.match(r"^[\d]{5,10}$", cleaned):
            raise ValueError("Invalid pincode format")
        return cleaned

    @field_validator("address_type")
    @classmethod
    def validate_address_type(cls, v: str) -> str:
        """
        Validate and normalize address type.

        Valid types:
        - home: Residential address
        - work: Office/business address
        - other: Any other location

        Args:
            v: Address type string

        Returns:
            Lowercase address type

        Raises:
            ValueError: If type is not valid
        """
        valid_types = ["home", "work", "other"]
        if v.lower() not in valid_types:
            raise ValueError(f"Address type must be one of: {', '.join(valid_types)}")
        return v.lower()


# ==============================================================================
# ADDRESS UPDATE MODEL
# ==============================================================================
class AddressUpdate(BaseModel):
    """
    Model for updating an existing address.

    All fields are optional - only provided fields are updated.
    This allows partial updates without resending all data.

    Example JSON (partial update):
        {
            "phone": "9123456789",
            "is_default": true
        }
    """

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    address_line1: Optional[str] = Field(None, min_length=5, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    landmark: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(None, min_length=5, max_length=10)
    country: Optional[str] = Field(None, max_length=100)
    address_type: Optional[str] = Field(None)
    is_default: Optional[bool] = Field(None)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone if provided (same logic as AddressCreate)."""
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: Optional[str]) -> Optional[str]:
        """Validate pincode if provided (same logic as AddressCreate)."""
        if v is None:
            return v
        cleaned = v.strip()
        if not re.match(r"^[\d]{5,10}$", cleaned):
            raise ValueError("Invalid pincode format")
        return cleaned


# ==============================================================================
# ADDRESS RESPONSE MODEL
# ==============================================================================
class AddressResponse(BaseModel):
    """
    Model for address response.

    Returned when fetching user's addresses.
    Used in profile address list, checkout address selection.

    Example JSON:
        {
            "id": "addr123",
            "user_id": "user456",
            "full_name": "John Doe",
            "phone": "9876543210",
            "address_line1": "Flat 101, Sunshine Apartments",
            "address_line2": "MG Road",
            "landmark": "Near City Mall",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "country": "India",
            "address_type": "home",
            "is_default": true,
            "created_at": "2024-01-15T10:30:00"
        }
    """

    # Identification
    id: str = Field(..., description="Address ID (Firestore document ID)")
    user_id: str = Field(..., description="Owner user ID")

    # Recipient info
    full_name: str = Field(..., description="Recipient name for delivery")
    phone: str = Field(..., description="Contact phone number")

    # Address details
    address_line1: str = Field(..., description="Primary address line")
    address_line2: Optional[str] = Field(None, description="Secondary address line")
    landmark: Optional[str] = Field(None, description="Nearby landmark")

    # Location
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State/province")
    pincode: str = Field(..., description="Postal/ZIP code")
    country: str = Field(..., description="Country")

    # Classification
    address_type: str = Field(..., description="Type: home, work, other")
    is_default: bool = Field(False, description="Default address flag")

    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    def get_formatted(self) -> str:
        """
        Get formatted address string for display.

        Combines all address parts into a single readable string.
        Used for order confirmation, emails, etc.

        Format:
            "Flat 101, MG Road, Near City Mall, Mumbai, Maharashtra - 400001, India"

        Returns:
            Formatted address string
        """
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.landmark:
            parts.append(f"Near {self.landmark}")
        parts.append(f"{self.city}, {self.state} - {self.pincode}")
        parts.append(self.country)
        return ", ".join(parts)
