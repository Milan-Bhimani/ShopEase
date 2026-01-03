"""
==============================================================================
Address API Routes (addresses.py)
==============================================================================

PURPOSE:
--------
This module defines all shipping address API endpoints:
- List user's addresses
- Create new addresses
- Update existing addresses
- Delete addresses
- Get/set default address

API ENDPOINTS:
--------------
GET    /addresses           - List all user addresses
GET    /addresses/default   - Get default address
GET    /addresses/{id}      - Get specific address
POST   /addresses           - Create new address
PUT    /addresses/{id}      - Update address
DELETE /addresses/{id}      - Delete address
POST   /addresses/{id}/set-default - Set as default

ADDRESS MANAGEMENT:
-------------------
Each user can have multiple shipping addresses:
- Home address
- Work address
- Other locations (family, office, etc.)

One address can be marked as "default" for quick checkout.
If a user deletes their default address, another is auto-promoted.
First address created is automatically set as default.

DEFAULT ADDRESS LOGIC:
----------------------
1. First address -> automatically default
2. Setting new default -> unsets previous default
3. Deleting default -> first remaining becomes default
4. Only one default at a time

SECURITY:
---------
All endpoints require authentication.
Users can only access their own addresses.
Address ownership is verified on every operation.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List

from ..auth.dependencies import get_current_user
from ..models.address import AddressCreate, AddressUpdate, AddressResponse
from ..firebase import address_repo

# Create router with prefix and tag for OpenAPI docs
router = APIRouter(prefix="/addresses", tags=["Addresses"])


# ==============================================================================
# ADDRESS ENDPOINTS - All require authentication
# ==============================================================================


@router.get("", response_model=List[AddressResponse])
async def list_addresses(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all addresses for current user.

    Returns all saved shipping addresses for the user.
    Used in profile address management and checkout address selection.

    Returns:
        List of addresses (may be empty for new users)

    Example:
        GET /addresses
    """
    addresses = await address_repo.get_user_addresses(current_user["id"])
    return addresses


@router.get("/default", response_model=AddressResponse)
async def get_default_address(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get default address for current user.

    Returns the address marked as default (is_default=True).
    Used to pre-select address at checkout.

    Returns:
        Default address

    Raises:
        404: No default address set

    Example:
        GET /addresses/default
    """
    address = await address_repo.get_default_address(current_user["id"])

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default address set"
        )

    return address


@router.get("/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific address by ID.

    Path Parameters:
        address_id: Firestore document ID

    Returns:
        Address details

    Raises:
        404: Address not found or belongs to another user

    Example:
        GET /addresses/abc123
    """
    address = await address_repo.get_by_id(address_id)

    # Security: Verify address belongs to current user
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    return address


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: AddressCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new shipping address.

    Creates address and associates with current user.
    First address is automatically set as default.
    If is_default=True, previous default is unset.

    Request Body:
        AddressCreate with full_name, phone, address details

    Returns:
        Created address with generated ID

    Example:
        POST /addresses
        {
            "full_name": "John Doe",
            "phone": "9876543210",
            "address_line1": "123 Main Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "address_type": "home",
            "is_default": true
        }
    """
    # If this is set as default, unset other defaults first
    if address_data.is_default:
        existing_addresses = await address_repo.get_user_addresses(current_user["id"])
        for addr in existing_addresses:
            if addr.get("is_default"):
                await address_repo.update(addr["id"], {"is_default": False})

    # Prepare address document
    address_dict = address_data.model_dump()
    address_dict["user_id"] = current_user["id"]

    # First address is automatically default
    existing = await address_repo.get_user_addresses(current_user["id"])
    if not existing:
        address_dict["is_default"] = True

    # Save to Firestore
    address_id = await address_repo.create(address_dict)
    address = await address_repo.get_by_id(address_id)

    return address


@router.put("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: str,
    update_data: AddressUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update an existing address.

    Partial update - only provided fields are changed.
    If is_default=True, previous default is unset.

    Path Parameters:
        address_id: Address ID to update

    Request Body:
        AddressUpdate with optional fields

    Returns:
        Updated address

    Raises:
        404: Address not found or belongs to another user

    Example:
        PUT /addresses/abc123
        {"phone": "9123456789", "is_default": true}
    """
    # Verify ownership
    address = await address_repo.get_by_id(address_id)
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    # If setting as default, unset other defaults first
    if update_data.is_default:
        existing_addresses = await address_repo.get_user_addresses(current_user["id"])
        for addr in existing_addresses:
            if addr["id"] != address_id and addr.get("is_default"):
                await address_repo.update(addr["id"], {"is_default": False})

    # Build update dictionary with only non-None values
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

    if update_dict:
        await address_repo.update(address_id, update_dict)

    updated = await address_repo.get_by_id(address_id)
    return updated


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Delete an address.

    Permanently removes the address from user's saved addresses.
    If deleted address was default, first remaining address becomes default.

    Path Parameters:
        address_id: Address ID to delete

    Raises:
        404: Address not found or belongs to another user

    Example:
        DELETE /addresses/abc123

    Note:
        Past orders retain address snapshot, so historical
        data is not affected by address deletion.
    """
    # Verify ownership
    address = await address_repo.get_by_id(address_id)
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    # Delete the address
    await address_repo.delete(address_id)

    # If deleted address was default, promote another
    if address.get("is_default"):
        remaining = await address_repo.get_user_addresses(current_user["id"])
        if remaining:
            await address_repo.update(remaining[0]["id"], {"is_default": True})


@router.post("/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    address_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set an address as default.

    Marks the specified address as default and unsets
    any previously default address.

    Path Parameters:
        address_id: Address ID to set as default

    Returns:
        Updated address with is_default=True

    Raises:
        404: Address not found or belongs to another user

    Example:
        POST /addresses/abc123/set-default
    """
    # Verify ownership
    address = await address_repo.get_by_id(address_id)
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    # Unset other defaults
    existing_addresses = await address_repo.get_user_addresses(current_user["id"])
    for addr in existing_addresses:
        if addr["id"] != address_id and addr.get("is_default"):
            await address_repo.update(addr["id"], {"is_default": False})

    # Set this one as default
    await address_repo.update(address_id, {"is_default": True})

    updated = await address_repo.get_by_id(address_id)
    return updated
