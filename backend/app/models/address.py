"""
Address-related Pydantic models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class AddressCreate(BaseModel):
    """Model for creating a new address."""

    full_name: str = Field(..., min_length=2, max_length=100, description="Recipient full name")
    phone: str = Field(..., max_length=15, description="Contact phone number")
    address_line1: str = Field(..., min_length=5, max_length=200, description="Street address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Street address line 2")
    landmark: Optional[str] = Field(None, max_length=100, description="Nearby landmark")
    city: str = Field(..., min_length=2, max_length=100, description="City name")
    state: str = Field(..., min_length=2, max_length=100, description="State/Province")
    pincode: str = Field(..., min_length=5, max_length=10, description="ZIP/Postal code")
    country: str = Field("India", max_length=100, description="Country")
    address_type: str = Field("home", description="Address type: home, work, other")
    is_default: bool = Field(False, description="Set as default address")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """Validate pincode format."""
        cleaned = v.strip()
        if not re.match(r"^[\d]{5,10}$", cleaned):
            raise ValueError("Invalid pincode format")
        return cleaned

    @field_validator("address_type")
    @classmethod
    def validate_address_type(cls, v: str) -> str:
        """Validate address type."""
        valid_types = ["home", "work", "other"]
        if v.lower() not in valid_types:
            raise ValueError(f"Address type must be one of: {', '.join(valid_types)}")
        return v.lower()


class AddressUpdate(BaseModel):
    """Model for updating an address."""

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
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?[\d]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = v.strip()
        if not re.match(r"^[\d]{5,10}$", cleaned):
            raise ValueError("Invalid pincode format")
        return cleaned


class AddressResponse(BaseModel):
    """Model for address response."""

    id: str = Field(..., description="Address ID")
    user_id: str = Field(..., description="User ID")
    full_name: str = Field(..., description="Recipient name")
    phone: str = Field(..., description="Contact phone")
    address_line1: str = Field(..., description="Address line 1")
    address_line2: Optional[str] = Field(None, description="Address line 2")
    landmark: Optional[str] = Field(None, description="Landmark")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    pincode: str = Field(..., description="Pincode")
    country: str = Field(..., description="Country")
    address_type: str = Field(..., description="Address type")
    is_default: bool = Field(False, description="Default address flag")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    def get_formatted(self) -> str:
        """Get formatted address string."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.landmark:
            parts.append(f"Near {self.landmark}")
        parts.append(f"{self.city}, {self.state} - {self.pincode}")
        parts.append(self.country)
        return ", ".join(parts)
