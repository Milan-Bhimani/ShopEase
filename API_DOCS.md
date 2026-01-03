# E-Commerce API Documentation

Base URL: `/api`

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### Register User
```
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "9876543210"
}
```

**Response (201):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "abc123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "9876543210"
  }
}
```

### Login
```
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200):** Same as register response

### Get Current User
```
GET /api/auth/me
```
**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "abc123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "9876543210",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### Logout
```
POST /api/auth/logout
```
**Auth Required:** Yes

---

## User Endpoints

### Get Profile
```
GET /api/users/profile
```
**Auth Required:** Yes

### Update Profile
```
PUT /api/users/profile
```
**Auth Required:** Yes

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "phone": "9876543210"
}
```

### Change Password
```
POST /api/users/change-password
```
**Auth Required:** Yes

**Request Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass123"
}
```

---

## Product Endpoints

### List Products
```
GET /api/products
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter by category |
| search | string | Search query |
| featured | boolean | Show only featured |
| min_price | number | Minimum price |
| max_price | number | Maximum price |
| page | integer | Page number (default: 1) |
| per_page | integer | Items per page (default: 20, max: 100) |

**Response (200):**
```json
{
  "products": [
    {
      "id": "prod123",
      "name": "Product Name",
      "description": "Product description",
      "price": 999.00,
      "original_price": 1299.00,
      "discount_percentage": 23,
      "category": "Electronics",
      "brand": "BrandName",
      "stock_quantity": 50,
      "in_stock": true,
      "images": ["url1", "url2"],
      "thumbnail": "url1",
      "is_featured": true,
      "rating": 4.5,
      "review_count": 120
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "has_more": true
}
```

### Get Featured Products
```
GET /api/products/featured?limit=10
```

### Get Categories
```
GET /api/products/categories
```

**Response (200):**
```json
[
  {
    "id": "electronics",
    "name": "Electronics",
    "slug": "electronics",
    "product_count": 50
  }
]
```

### Get Single Product
```
GET /api/products/{product_id}
```

---

## Cart Endpoints

### Get Cart
```
GET /api/cart
```
**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "cart123",
  "user_id": "user123",
  "items": [
    {
      "product_id": "prod123",
      "product_name": "Product Name",
      "product_image": "url",
      "price": 999.00,
      "quantity": 2,
      "subtotal": 1998.00,
      "in_stock": true,
      "stock_quantity": 50
    }
  ],
  "item_count": 2,
  "subtotal": 1998.00,
  "tax": 359.64,
  "shipping": 0,
  "total": 2357.64
}
```

### Get Cart Summary
```
GET /api/cart/summary
```
**Auth Required:** Yes

**Response (200):**
```json
{
  "item_count": 2,
  "total": 2357.64
}
```

### Add to Cart
```
POST /api/cart/items
```
**Auth Required:** Yes

**Request Body:**
```json
{
  "product_id": "prod123",
  "quantity": 1
}
```

### Update Cart Item
```
PUT /api/cart/items/{product_id}
```
**Auth Required:** Yes

**Request Body:**
```json
{
  "quantity": 3
}
```

### Remove from Cart
```
DELETE /api/cart/items/{product_id}
```
**Auth Required:** Yes

### Clear Cart
```
DELETE /api/cart
```
**Auth Required:** Yes

---

## Address Endpoints

### List Addresses
```
GET /api/addresses
```
**Auth Required:** Yes

### Get Default Address
```
GET /api/addresses/default
```
**Auth Required:** Yes

### Create Address
```
POST /api/addresses
```
**Auth Required:** Yes

**Request Body:**
```json
{
  "full_name": "John Doe",
  "phone": "9876543210",
  "address_line1": "123 Main St",
  "address_line2": "Apt 4B",
  "landmark": "Near Park",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001",
  "country": "India",
  "address_type": "home",
  "is_default": true
}
```

### Update Address
```
PUT /api/addresses/{address_id}
```
**Auth Required:** Yes

### Delete Address
```
DELETE /api/addresses/{address_id}
```
**Auth Required:** Yes

### Set Default Address
```
POST /api/addresses/{address_id}/set-default
```
**Auth Required:** Yes

---

## Order Endpoints

### List Orders
```
GET /api/orders?page=1&per_page=10
```
**Auth Required:** Yes

**Response (200):**
```json
{
  "orders": [
    {
      "id": "order123",
      "order_number": "ORD-20240101-ABC123",
      "user_id": "user123",
      "items": [...],
      "shipping_address": {...},
      "status": "confirmed",
      "payment_method": "card",
      "payment_status": "completed",
      "subtotal": 1998.00,
      "tax": 359.64,
      "shipping_cost": 0,
      "discount": 0,
      "total": 2357.64,
      "created_at": "2024-01-01T00:00:00",
      "estimated_delivery": "2024-01-08"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 10
}
```

### Get Order
```
GET /api/orders/{order_id}
```
**Auth Required:** Yes

### Create Order (Checkout)
```
POST /api/orders
```
**Auth Required:** Yes

**Request Body:**
```json
{
  "address_id": "addr123",
  "payment": {
    "method": "card",
    "card_last_four": "4242",
    "card_brand": "Visa"
  },
  "notes": "Please deliver after 5 PM"
}
```

**Payment Methods:**
- `card` - Credit/Debit Card
- `upi` - UPI Payment
- `net_banking` - Net Banking
- `wallet` - Digital Wallet
- `cod` - Cash on Delivery

**Response (201):**
```json
{
  "success": true,
  "order_id": "order123",
  "order_number": "ORD-20240101-ABC123",
  "transaction_id": "TXN-ABC123DEF456",
  "payment_method": "card",
  "amount": 2357.64,
  "message": "Order placed successfully!"
}
```

### Cancel Order
```
POST /api/orders/{order_id}/cancel
```
**Auth Required:** Yes

### Track Order
```
GET /api/orders/{order_id}/track
```
**Auth Required:** Yes

**Response (200):**
```json
{
  "order_id": "order123",
  "order_number": "ORD-20240101-ABC123",
  "current_status": "shipped",
  "estimated_delivery": "2024-01-08",
  "timeline": [
    {
      "status": "pending",
      "label": "Order Placed",
      "completed": true,
      "timestamp": "2024-01-01T00:00:00"
    },
    {
      "status": "confirmed",
      "label": "Order Confirmed",
      "completed": true,
      "timestamp": "2024-01-01T01:00:00"
    }
  ]
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

---

## Health Check

```
GET /api/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```
