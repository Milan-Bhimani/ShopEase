"""
==============================================================================
Firebase Firestore Module (firebase.py)
==============================================================================

PURPOSE:
--------
This module handles all database operations using Google Firebase Firestore.
It provides:
1. Firebase initialization and connection management
2. Generic repository pattern for CRUD operations
3. Specialized repositories for each collection (users, products, etc.)

WHY FIREBASE FIRESTORE?
-----------------------
We chose Firestore as our database because:

1. **NoSQL Flexibility**: Document-based storage is perfect for e-commerce
   where products have varying attributes (clothing has sizes, electronics
   have specs, etc.)

2. **Real-time Updates**: Built-in real-time listeners (though not used here,
   useful for future features like live inventory updates)

3. **Scalability**: Automatically scales to handle millions of documents
   without infrastructure management

4. **Serverless-Friendly**: Works great with Vercel, Cloud Functions, etc.
   No connection pools to manage

5. **Free Tier**: Generous free tier (50K reads, 20K writes per day)
   perfect for starting out

6. **Firebase Ecosystem**: Integrates with Firebase Auth, Storage, Hosting
   if needed in the future

DATABASE STRUCTURE (Collections):
--------------------------------
    users/
    ├── {user_id}/
    │   ├── email: string
    │   ├── password_hash: string
    │   ├── first_name: string
    │   ├── last_name: string
    │   ├── phone: string
    │   ├── is_active: boolean
    │   ├── is_admin: boolean
    │   ├── created_at: string (ISO timestamp)
    │   └── updated_at: string (ISO timestamp)

    products/
    ├── {product_id}/
    │   ├── name: string
    │   ├── description: string
    │   ├── price: number
    │   ├── category: string
    │   ├── brand: string
    │   ├── image_url: string
    │   ├── stock: number
    │   ├── is_featured: boolean
    │   └── ...

    carts/
    ├── {cart_id}/
    │   ├── user_id: string
    │   ├── items: array
    │   │   ├── product_id: string
    │   │   ├── quantity: number
    │   │   └── ...
    │   └── updated_at: string

    orders/
    ├── {order_id}/
    │   ├── user_id: string
    │   ├── order_number: string
    │   ├── status: string
    │   ├── items: array
    │   ├── total: number
    │   └── ...

    addresses/
    ├── {address_id}/
    │   ├── user_id: string
    │   ├── full_name: string
    │   ├── address_line1: string
    │   ├── city: string
    │   ├── state: string
    │   ├── pincode: string
    │   ├── is_default: boolean
    │   └── ...

REPOSITORY PATTERN:
------------------
We use the Repository pattern to abstract database operations:

1. FirestoreRepository: Base class with generic CRUD methods
2. UserRepository, ProductRepository, etc.: Specialized classes with
   domain-specific queries

This provides:
- Separation of concerns (routes don't know about Firestore)
- Easy testing (can mock repositories)
- Consistent error handling
- Single place to add logging, caching, etc.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# ==============================================================================
# GLOBAL FIRESTORE CLIENT
# ==============================================================================
# We use a global variable to store the Firestore client instance.
# This ensures we reuse the same connection across all requests,
# avoiding the overhead of creating new connections.
_db: Optional[firestore.Client] = None


# ==============================================================================
# FIREBASE INITIALIZATION
# ==============================================================================
def init_firebase() -> firestore.Client:
    """
    Initialize Firebase Admin SDK and return Firestore client.

    Should be called once at application startup (in main.py lifespan).
    Subsequent calls return the existing client (idempotent).

    The function handles three credential sources (from config.py):
    1. Credential file path (for Docker/local development)
    2. Credentials dictionary (from environment variables)

    Returns:
        firestore.Client: Initialized Firestore client

    Raises:
        Exception: If Firebase initialization fails
    """
    global _db

    # Return existing client if already initialized
    if _db is not None:
        return _db

    settings = get_settings()
    firebase_creds = settings.get_firebase_credentials()

    try:
        # Check if using credential file path
        # config.py returns {"credential_path": "..."} when file path is used
        if "credential_path" in firebase_creds:
            cred = credentials.Certificate(firebase_creds["credential_path"])
        else:
            # Use credentials dictionary directly
            cred = credentials.Certificate(firebase_creds)

        # Initialize Firebase app if not already initialized
        # firebase_admin._apps is the internal registry of initialized apps
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")

        # Create and store Firestore client
        _db = firestore.client()
        return _db

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def get_db() -> firestore.Client:
    """
    Get Firestore client instance.

    This is the main entry point for getting the database client.
    It automatically initializes Firebase if not already done.

    Returns:
        firestore.Client: Firestore client for database operations
    """
    global _db
    if _db is None:
        _db = init_firebase()
    return _db


# ==============================================================================
# COLLECTION NAMES
# ==============================================================================
class Collections:
    """
    Constants for Firestore collection names.

    Using constants instead of string literals helps:
    - Prevent typos (IDE autocomplete)
    - Easy renaming if needed
    - Single source of truth for collection names
    """
    USERS = "users"
    PRODUCTS = "products"
    CARTS = "carts"
    ORDERS = "orders"
    ADDRESSES = "addresses"
    CATEGORIES = "categories"


# ==============================================================================
# GENERIC FIRESTORE REPOSITORY
# ==============================================================================
class FirestoreRepository:
    """
    Generic repository for Firestore CRUD operations.

    This base class provides common database operations that work with
    any Firestore collection. Specialized repositories inherit from this
    and add domain-specific methods.

    The async methods don't actually use async I/O (Firestore Python SDK
    is synchronous), but we mark them async for consistency with FastAPI
    and potential future migration to async Firestore client.

    Usage:
        repo = FirestoreRepository("my_collection")
        doc_id = await repo.create({"name": "Test"})
        doc = await repo.get_by_id(doc_id)
        await repo.update(doc_id, {"name": "Updated"})
        await repo.delete(doc_id)
    """

    def __init__(self, collection_name: str):
        """
        Initialize repository for a specific collection.

        Args:
            collection_name: Name of the Firestore collection
        """
        self.collection_name = collection_name

    @property
    def collection(self):
        """
        Get collection reference.

        Using a property ensures we always get the current database client,
        even if it was initialized after the repository was created.
        """
        return get_db().collection(self.collection_name)

    async def create(self, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Create a new document in the collection.

        Automatically adds created_at and updated_at timestamps.

        Args:
            data: Document data as dictionary
            doc_id: Optional specific document ID. If not provided,
                   Firestore generates a unique ID automatically.

        Returns:
            str: The document ID of the created document

        Example:
            user_id = await user_repo.create({
                "email": "user@example.com",
                "name": "John Doe"
            })
        """
        # Add timestamps for auditing
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()

        if doc_id:
            # Use specific document ID (useful for user IDs from auth, etc.)
            self.collection.document(doc_id).set(data)
            return doc_id
        else:
            # Let Firestore generate a unique ID
            # add() returns (timestamp, document_reference)
            doc_ref = self.collection.add(data)
            return doc_ref[1].id

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.

        Args:
            doc_id: The document ID to retrieve

        Returns:
            Document data as dictionary with 'id' field added,
            or None if document doesn't exist

        Example:
            user = await user_repo.get_by_id("abc123")
            if user:
                print(user["email"])
        """
        doc = self.collection.document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id  # Include document ID in the data
            return data
        return None

    async def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all documents in the collection.

        Args:
            limit: Maximum number of documents to return (default 100)
                   Use pagination for larger datasets.

        Returns:
            List of document dictionaries with 'id' field added
        """
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
        """
        Query documents by a single field condition.

        Args:
            field: Field name to query
            operator: Comparison operator ("==", "!=", "<", "<=", ">", ">=",
                     "array-contains", "in", "not-in")
            value: Value to compare against
            limit: Maximum results to return

        Returns:
            List of matching document dictionaries

        Example:
            # Get all active users
            active_users = await user_repo.query("is_active", "==", True)

            # Get products under $50
            cheap_products = await product_repo.query("price", "<", 50)
        """
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
        """
        Update an existing document.

        Only updates the fields provided in data; other fields remain unchanged.
        Automatically updates the updated_at timestamp.

        Args:
            doc_id: Document ID to update
            data: Dictionary of fields to update

        Returns:
            True if document was updated, False if document doesn't exist

        Example:
            await user_repo.update("abc123", {"name": "New Name"})
        """
        data["updated_at"] = datetime.utcnow().isoformat()
        doc_ref = self.collection.document(doc_id)
        if doc_ref.get().exists:
            doc_ref.update(data)
            return True
        return False

    async def delete(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if document was deleted, False if it didn't exist
        """
        doc_ref = self.collection.document(doc_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        return False

    async def exists(self, doc_id: str) -> bool:
        """
        Check if a document exists.

        Args:
            doc_id: Document ID to check

        Returns:
            True if document exists, False otherwise
        """
        return self.collection.document(doc_id).get().exists


# ==============================================================================
# SPECIALIZED REPOSITORIES
# ==============================================================================
# These repositories extend FirestoreRepository with domain-specific methods.
# They encapsulate the business logic for each entity type.

class UserRepository(FirestoreRepository):
    """
    Repository for user operations.

    Extends base repository with user-specific queries like
    finding users by email (for authentication).
    """

    def __init__(self):
        super().__init__(Collections.USERS)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address.

        Used during login to find the user and verify password.
        Email is lowercased for case-insensitive matching.

        Args:
            email: User's email address

        Returns:
            User document or None if not found
        """
        results = await self.query("email", "==", email.lower(), limit=1)
        return results[0] if results else None

    # ==========================================================================
    # ADMIN METHODS
    # ==========================================================================

    async def get_all_users(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get all users for admin dashboard.

        Returns all users sorted by creation date (newest first).
        Used by admin to manage user accounts.

        Args:
            limit: Maximum users to return

        Returns:
            List of all user documents
        """
        users = await self.get_all(limit=limit)
        # Sort by created_at descending
        users.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return users

    async def get_user_count(self) -> int:
        """
        Get total count of registered users.

        Used for admin dashboard statistics.

        Returns:
            Total number of users
        """
        docs = list(self.collection.stream())
        return len(docs)

    async def get_active_user_count(self) -> int:
        """
        Get count of active (non-deactivated) users.

        Used for admin dashboard statistics.

        Returns:
            Number of active users
        """
        users = await self.query("is_active", "==", True, limit=10000)
        return len(users)

    async def search_users(self, search: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search users by email or name.

        Searches across email, first_name, and last_name fields.
        Note: This is a simple implementation - fetches all users
        and filters in Python. For large user bases, consider
        using Algolia or similar.

        Args:
            search: Search term
            limit: Maximum results to return

        Returns:
            List of matching users
        """
        all_users = await self.get_all(limit=1000)
        search_lower = search.lower()

        results = []
        for user in all_users:
            # Search in email, first_name, last_name
            if (search_lower in user.get("email", "").lower() or
                search_lower in user.get("first_name", "").lower() or
                search_lower in user.get("last_name", "").lower()):
                results.append(user)
                if len(results) >= limit:
                    break

        return results


class ProductRepository(FirestoreRepository):
    """
    Repository for product operations.

    Extends base repository with e-commerce specific queries:
    - Category filtering
    - Search functionality
    - Featured products
    """

    def __init__(self):
        super().__init__(Collections.PRODUCTS)

    async def get_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get products by category.

        Args:
            category: Category name to filter by
            limit: Maximum products to return

        Returns:
            List of products in the specified category
        """
        return await self.query("category", "==", category, limit=limit)

    async def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search products by name.

        Uses Firestore's range query for prefix matching.
        The '\uf8ff' character is a high Unicode character that comes
        after all standard characters, effectively creating a "starts with" query.

        Note: Firestore doesn't support full-text search natively.
        For production with complex search needs, consider:
        - Algolia (full-text search as a service)
        - Elasticsearch (self-hosted)
        - Firebase Extensions for search

        Args:
            query: Search term (matches start of product name)
            limit: Maximum results to return

        Returns:
            List of matching products
        """
        # Simple prefix search on name_lower field
        # Products must have a name_lower field (lowercase version of name)
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
        """
        Get featured products for homepage display.

        Args:
            limit: Maximum featured products to return

        Returns:
            List of featured products
        """
        return await self.query("is_featured", "==", True, limit=limit)

    # ==========================================================================
    # ADMIN METHODS
    # ==========================================================================

    async def get_all_with_inactive(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get all products including inactive ones.

        Unlike the regular product listing which filters by is_active=True,
        this returns ALL products for admin management.

        Args:
            limit: Maximum products to return

        Returns:
            List of all products sorted by created_at descending
        """
        products = await self.get_all(limit=limit)
        # Sort by created_at descending (newest first)
        products.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return products

    async def get_product_count(self) -> int:
        """
        Get total count of all products.

        Used for admin dashboard statistics.

        Returns:
            Total number of products
        """
        docs = list(self.collection.stream())
        return len(docs)

    async def get_active_product_count(self) -> int:
        """
        Get count of active (visible) products.

        Used for admin dashboard statistics.

        Returns:
            Number of active products
        """
        products = await self.query("is_active", "==", True, limit=10000)
        return len(products)

    async def search_products_admin(
        self,
        search: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search products by name for admin panel.

        Unlike the regular search, this includes inactive products
        and can optionally filter by category.

        Args:
            search: Search term (case-insensitive)
            category: Optional category filter
            limit: Maximum results to return

        Returns:
            List of matching products
        """
        all_products = await self.get_all(limit=1000)
        search_lower = search.lower()

        results = []
        for product in all_products:
            # Check name match
            name_match = search_lower in product.get("name", "").lower()

            # Check category if specified
            category_match = True
            if category:
                category_match = product.get("category", "") == category

            if name_match and category_match:
                results.append(product)
                if len(results) >= limit:
                    break

        return results


class CartRepository(FirestoreRepository):
    """
    Repository for shopping cart operations.

    Each user has one cart document that contains an array of items.
    """

    def __init__(self):
        super().__init__(Collections.CARTS)

    async def get_user_cart(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cart for a specific user.

        Args:
            user_id: User's ID

        Returns:
            Cart document or None if user has no cart
        """
        results = await self.query("user_id", "==", user_id, limit=1)
        return results[0] if results else None

    async def clear_cart(self, user_id: str) -> bool:
        """
        Clear all items from user's cart.

        Called after order is placed to empty the cart.

        Args:
            user_id: User's ID

        Returns:
            True if cart was cleared, False if no cart exists
        """
        cart = await self.get_user_cart(user_id)
        if cart:
            await self.update(cart["id"], {"items": [], "updated_at": datetime.utcnow().isoformat()})
            return True
        return False


class OrderRepository(FirestoreRepository):
    """
    Repository for order operations.

    Handles order storage and retrieval. Orders are sorted by
    creation date (most recent first) in Python since Firestore
    requires composite indexes for combined where + orderBy queries.
    """

    def __init__(self):
        super().__init__(Collections.ORDERS)

    async def get_user_orders(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all orders for a user, sorted by date (newest first).

        Note: We sort in Python instead of using Firestore's orderBy because
        combining where() with orderBy() requires a composite index.
        For small to medium order counts per user, Python sorting is fine.

        Args:
            user_id: User's ID
            limit: Maximum orders to return

        Returns:
            List of orders sorted by created_at descending
        """
        docs = self.collection.where(
            filter=FieldFilter("user_id", "==", user_id)
        ).limit(limit).stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)

        # Sort by created_at descending (newest first)
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    # ==========================================================================
    # ADMIN METHODS
    # ==========================================================================

    async def get_all_orders(
        self,
        status: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Get all orders for admin dashboard.

        Optionally filter by order status. Returns orders sorted
        by creation date (newest first).

        Args:
            status: Optional status filter (e.g., "pending", "shipped")
            limit: Maximum orders to return

        Returns:
            List of all orders
        """
        if status:
            orders = await self.query("status", "==", status, limit=limit)
        else:
            orders = await self.get_all(limit=limit)

        # Sort by created_at descending
        orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return orders

    async def get_order_count(self) -> int:
        """
        Get total count of all orders.

        Used for admin dashboard statistics.

        Returns:
            Total number of orders
        """
        docs = list(self.collection.stream())
        return len(docs)

    async def get_order_count_by_status(self) -> Dict[str, int]:
        """
        Get order count grouped by status.

        Used for admin dashboard to show order distribution.

        Returns:
            Dictionary mapping status to count, e.g.:
            {"pending": 5, "shipped": 10, "delivered": 20}
        """
        all_orders = await self.get_all(limit=10000)

        status_counts = {}
        for order in all_orders:
            status = order.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts

    async def get_total_revenue(self) -> float:
        """
        Calculate total revenue from completed orders.

        Only counts orders with status "delivered" or payment_status "paid".
        Used for admin dashboard revenue statistic.

        Returns:
            Total revenue in INR
        """
        all_orders = await self.get_all(limit=10000)

        total = 0.0
        for order in all_orders:
            # Count revenue from delivered orders or paid orders
            status = order.get("status", "")
            payment_status = order.get("payment_status", "")

            if status == "delivered" or payment_status == "paid":
                total += float(order.get("total", 0))

        return total

    async def get_recent_orders_count(self, days: int = 7) -> int:
        """
        Get count of orders placed in the last N days.

        Used for admin dashboard to show recent activity.

        Args:
            days: Number of days to look back (default 7)

        Returns:
            Number of orders in the specified period
        """
        from datetime import timedelta

        all_orders = await self.get_all(limit=10000)
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        count = 0
        for order in all_orders:
            created_at = order.get("created_at", "")
            if created_at >= cutoff:
                count += 1

        return count

    async def search_orders(
        self,
        search: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search orders by order number or customer email.

        Used by admin to find specific orders. Searches in order_number
        and the user's email (if attached to order).

        Args:
            search: Search term
            limit: Maximum results to return

        Returns:
            List of matching orders
        """
        all_orders = await self.get_all(limit=1000)
        search_lower = search.lower()

        results = []
        for order in all_orders:
            # Search in order_number
            order_num_match = search_lower in order.get("order_number", "").lower()

            # Search in user email (if stored in order)
            email_match = search_lower in order.get("user_email", "").lower()

            if order_num_match or email_match:
                results.append(order)
                if len(results) >= limit:
                    break

        # Sort by created_at descending
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results


class AddressRepository(FirestoreRepository):
    """
    Repository for shipping address operations.

    Users can have multiple addresses, with one marked as default.
    """

    def __init__(self):
        super().__init__(Collections.ADDRESSES)

    async def get_user_addresses(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all addresses for a user.

        Args:
            user_id: User's ID

        Returns:
            List of user's addresses
        """
        return await self.query("user_id", "==", user_id)

    async def get_default_address(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's default address for checkout.

        Uses compound query (user_id AND is_default).

        Args:
            user_id: User's ID

        Returns:
            Default address or None if no default is set
        """
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


# ==============================================================================
# REPOSITORY SINGLETONS
# ==============================================================================
# Create single instances of each repository.
# These are imported throughout the application for database operations.
#
# Why singletons?
# - Consistent state across all requests
# - No overhead of creating new instances
# - Easy to import: from app.firebase import user_repo
user_repo = UserRepository()
product_repo = ProductRepository()
cart_repo = CartRepository()
order_repo = OrderRepository()
address_repo = AddressRepository()
