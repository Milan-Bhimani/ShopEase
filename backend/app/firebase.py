"""
Firebase Firestore initialization and database operations.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# Global Firestore client
_db: Optional[firestore.Client] = None


def init_firebase() -> firestore.Client:
    """
    Initialize Firebase Admin SDK and return Firestore client.
    Should be called once at application startup.
    """
    global _db

    if _db is not None:
        return _db

    settings = get_settings()
    firebase_creds = settings.get_firebase_credentials()

    try:
        # Check if using credential file path
        if "credential_path" in firebase_creds:
            cred = credentials.Certificate(firebase_creds["credential_path"])
        else:
            # Use credentials dictionary
            cred = credentials.Certificate(firebase_creds)

        # Initialize Firebase app if not already initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")

        _db = firestore.client()
        return _db

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def get_db() -> firestore.Client:
    """Get Firestore client instance."""
    global _db
    if _db is None:
        _db = init_firebase()
    return _db


# ============================================================
# Collection Names (constants for consistency)
# ============================================================
class Collections:
    USERS = "users"
    PRODUCTS = "products"
    CARTS = "carts"
    ORDERS = "orders"
    ADDRESSES = "addresses"
    CATEGORIES = "categories"


# ============================================================
# Generic Firestore Operations
# ============================================================
class FirestoreRepository:
    """Generic repository for Firestore CRUD operations."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    @property
    def collection(self):
        """Get collection reference."""
        return get_db().collection(self.collection_name)

    async def create(self, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Create a new document.
        Returns the document ID.
        """
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()

        if doc_id:
            self.collection.document(doc_id).set(data)
            return doc_id
        else:
            doc_ref = self.collection.add(data)
            return doc_ref[1].id

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by its ID."""
        doc = self.collection.document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    async def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all documents in the collection."""
        docs = self.collection.limit(limit).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results

    async def query(
        self,
        field: str,
        operator: str,
        value: Any,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query documents by field."""
        docs = self.collection.where(
            filter=FieldFilter(field, operator, value)
        ).limit(limit).stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results

    async def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document."""
        data["updated_at"] = datetime.utcnow().isoformat()
        doc_ref = self.collection.document(doc_id)
        if doc_ref.get().exists:
            doc_ref.update(data)
            return True
        return False

    async def delete(self, doc_id: str) -> bool:
        """Delete a document."""
        doc_ref = self.collection.document(doc_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        return False

    async def exists(self, doc_id: str) -> bool:
        """Check if a document exists."""
        return self.collection.document(doc_id).get().exists


# ============================================================
# Specialized Repositories
# ============================================================
class UserRepository(FirestoreRepository):
    """Repository for user operations."""

    def __init__(self):
        super().__init__(Collections.USERS)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        results = await self.query("email", "==", email.lower(), limit=1)
        return results[0] if results else None


class ProductRepository(FirestoreRepository):
    """Repository for product operations."""

    def __init__(self):
        super().__init__(Collections.PRODUCTS)

    async def get_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get products by category."""
        return await self.query("category", "==", category, limit=limit)

    async def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search products by name.
        Note: Firestore doesn't support full-text search natively.
        For production, consider using Algolia or Elasticsearch.
        """
        # Simple prefix search on name field
        docs = self.collection.where(
            filter=FieldFilter("name_lower", ">=", query.lower())
        ).where(
            filter=FieldFilter("name_lower", "<=", query.lower() + "\uf8ff")
        ).limit(limit).stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results

    async def get_featured(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured products."""
        return await self.query("is_featured", "==", True, limit=limit)


class CartRepository(FirestoreRepository):
    """Repository for cart operations."""

    def __init__(self):
        super().__init__(Collections.CARTS)

    async def get_user_cart(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cart for a specific user."""
        results = await self.query("user_id", "==", user_id, limit=1)
        return results[0] if results else None

    async def clear_cart(self, user_id: str) -> bool:
        """Clear all items from user's cart."""
        cart = await self.get_user_cart(user_id)
        if cart:
            await self.update(cart["id"], {"items": [], "updated_at": datetime.utcnow().isoformat()})
            return True
        return False


class OrderRepository(FirestoreRepository):
    """Repository for order operations."""

    def __init__(self):
        super().__init__(Collections.ORDERS)

    async def get_user_orders(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all orders for a user."""
        # Removed order_by to avoid requiring composite index in Firestore
        docs = self.collection.where(
            filter=FieldFilter("user_id", "==", user_id)
        ).limit(limit).stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)

        # Sort by created_at descending in Python
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results


class AddressRepository(FirestoreRepository):
    """Repository for address operations."""

    def __init__(self):
        super().__init__(Collections.ADDRESSES)

    async def get_user_addresses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all addresses for a user."""
        return await self.query("user_id", "==", user_id)

    async def get_default_address(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get default address for a user."""
        docs = self.collection.where(
            filter=FieldFilter("user_id", "==", user_id)
        ).where(
            filter=FieldFilter("is_default", "==", True)
        ).limit(1).stream()

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None


# ============================================================
# Initialize repositories as singletons
# ============================================================
user_repo = UserRepository()
product_repo = ProductRepository()
cart_repo = CartRepository()
order_repo = OrderRepository()
address_repo = AddressRepository()
