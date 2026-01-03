"""
Address API routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List

from ..auth.dependencies import get_current_user
from ..models.address import AddressCreate, AddressUpdate, AddressResponse
from ..firebase import address_repo

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get("", response_model=List[AddressResponse])
async def list_addresses(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all addresses for current user.

    Returns:
        List of addresses
    """
    addresses = await address_repo.get_user_addresses(current_user["id"])
    return addresses


@router.get("/default", response_model=AddressResponse)
async def get_default_address(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get default address for current user.

    Returns:
        Default address
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
    Get a specific address.

    Args:
        address_id: Address ID

    Returns:
        Address details
    """
    address = await address_repo.get_by_id(address_id)

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
    Create a new address.

    Args:
        address_data: Address details

    Returns:
        Created address
    """
    # If this is set as default, unset other defaults
    if address_data.is_default:
        existing_addresses = await address_repo.get_user_addresses(current_user["id"])
        for addr in existing_addresses:
            if addr.get("is_default"):
                await address_repo.update(addr["id"], {"is_default": False})

    # Create address document
    address_dict = address_data.model_dump()
    address_dict["user_id"] = current_user["id"]

    # If this is the first address, make it default
    existing = await address_repo.get_user_addresses(current_user["id"])
    if not existing:
        address_dict["is_default"] = True

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
    Update an address.

    Args:
        address_id: Address ID
        update_data: Fields to update

    Returns:
        Updated address
    """
    # Verify ownership
    address = await address_repo.get_by_id(address_id)
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    # If setting as default, unset other defaults
    if update_data.is_default:
        existing_addresses = await address_repo.get_user_addresses(current_user["id"])
        for addr in existing_addresses:
            if addr["id"] != address_id and addr.get("is_default"):
                await address_repo.update(addr["id"], {"is_default": False})

    # Build update dictionary
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

    Args:
        address_id: Address ID
    """
    # Verify ownership
    address = await address_repo.get_by_id(address_id)
    if not address or address.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    await address_repo.delete(address_id)

    # If deleted address was default, set another as default
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

    Args:
        address_id: Address ID

    Returns:
        Updated address
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
