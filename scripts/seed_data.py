#!/usr/bin/env python3
"""
Seed script to populate Firebase Firestore with sample data.
Run this script after setting up Firebase credentials.

Usage:
    python scripts/seed_data.py
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Sample product data
SAMPLE_PRODUCTS = [
    {
        "name": "Apple iPhone 15 Pro Max",
        "name_lower": "apple iphone 15 pro max",
        "description": "The most powerful iPhone ever. Features a titanium design, A17 Pro chip, and an advanced camera system for stunning photos and videos.",
        "price": 159900,
        "original_price": 169900,
        "category": "Electronics",
        "brand": "Apple",
        "sku": "IPHONE15PM-256",
        "stock_quantity": 50,
        "images": [
            "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400",
            "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400",
        "specifications": {
            "Display": "6.7-inch Super Retina XDR",
            "Chip": "A17 Pro",
            "Storage": "256GB",
            "Camera": "48MP Main + 12MP Ultra Wide",
            "Battery": "All-day battery life"
        },
        "is_active": True,
        "is_featured": True,
        "tags": ["smartphone", "apple", "iphone", "5g"],
        "rating": 4.8,
        "review_count": 1250,
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "name_lower": "samsung galaxy s24 ultra",
        "description": "Experience the future with Galaxy AI. S Pen included, 200MP camera, and Snapdragon 8 Gen 3 processor.",
        "price": 134999,
        "original_price": 144999,
        "category": "Electronics",
        "brand": "Samsung",
        "sku": "GALAXY-S24U-256",
        "stock_quantity": 75,
        "images": [
            "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400",
        "specifications": {
            "Display": "6.8-inch QHD+ Dynamic AMOLED",
            "Processor": "Snapdragon 8 Gen 3",
            "Storage": "256GB",
            "Camera": "200MP Wide + 12MP Ultra Wide",
            "Battery": "5000mAh"
        },
        "is_active": True,
        "is_featured": True,
        "tags": ["smartphone", "samsung", "galaxy", "android"],
        "rating": 4.7,
        "review_count": 890,
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "name_lower": "sony wh-1000xm5 headphones",
        "description": "Industry-leading noise canceling with Auto NC Optimizer. 30-hour battery life and crystal-clear hands-free calling.",
        "price": 29990,
        "original_price": 34990,
        "category": "Electronics",
        "brand": "Sony",
        "sku": "SONY-WH1000XM5",
        "stock_quantity": 100,
        "images": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
        "specifications": {
            "Type": "Over-ear",
            "Noise Canceling": "Yes",
            "Battery Life": "30 hours",
            "Connectivity": "Bluetooth 5.2, 3.5mm",
            "Weight": "250g"
        },
        "is_active": True,
        "is_featured": True,
        "tags": ["headphones", "wireless", "noise-canceling", "sony"],
        "rating": 4.9,
        "review_count": 2500,
    },
    {
        "name": "MacBook Pro 14-inch M3 Pro",
        "name_lower": "macbook pro 14-inch m3 pro",
        "description": "The most advanced Mac laptops ever. M3 Pro chip, stunning Liquid Retina XDR display, and all-day battery life.",
        "price": 199900,
        "original_price": 199900,
        "category": "Computers",
        "brand": "Apple",
        "sku": "MBP14-M3PRO-512",
        "stock_quantity": 30,
        "images": [
            "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400",
        "specifications": {
            "Chip": "Apple M3 Pro",
            "Memory": "18GB",
            "Storage": "512GB SSD",
            "Display": "14.2-inch Liquid Retina XDR",
            "Battery": "Up to 17 hours"
        },
        "is_active": True,
        "is_featured": True,
        "tags": ["laptop", "macbook", "apple", "m3"],
        "rating": 4.9,
        "review_count": 450,
    },
    {
        "name": "Nike Air Max 270",
        "name_lower": "nike air max 270",
        "description": "The Nike Air Max 270 delivers visible cushioning under every step. Updated for modern comfort with a sleek design.",
        "price": 12995,
        "original_price": 15995,
        "category": "Fashion",
        "brand": "Nike",
        "sku": "NIKE-AM270-BLK",
        "stock_quantity": 200,
        "images": [
            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "specifications": {
            "Upper": "Mesh and synthetic",
            "Midsole": "Air Max unit",
            "Outsole": "Rubber",
            "Style": "Running/Lifestyle"
        },
        "is_active": True,
        "is_featured": False,
        "tags": ["shoes", "nike", "sneakers", "running"],
        "rating": 4.5,
        "review_count": 3200,
    },
    {
        "name": "Levi's 501 Original Jeans",
        "name_lower": "levi's 501 original jeans",
        "description": "The original blue jean since 1873. Button fly, straight leg, and iconic 5-pocket styling.",
        "price": 4999,
        "original_price": 5999,
        "category": "Fashion",
        "brand": "Levi's",
        "sku": "LEVIS-501-32",
        "stock_quantity": 150,
        "images": [
            "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400",
        "specifications": {
            "Fit": "Original/Straight",
            "Rise": "Regular",
            "Material": "100% Cotton Denim",
            "Closure": "Button Fly"
        },
        "is_active": True,
        "is_featured": False,
        "tags": ["jeans", "denim", "levis", "fashion"],
        "rating": 4.6,
        "review_count": 5600,
    },
    {
        "name": "Instant Pot Duo 7-in-1",
        "name_lower": "instant pot duo 7-in-1",
        "description": "7-in-1 functionality: pressure cooker, slow cooker, rice cooker, steamer, sauté, yogurt maker & warmer.",
        "price": 8999,
        "original_price": 10999,
        "category": "Home & Kitchen",
        "brand": "Instant Pot",
        "sku": "IPOT-DUO-6QT",
        "stock_quantity": 80,
        "images": [
            "https://images.unsplash.com/photo-1585515320310-259814833e62?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1585515320310-259814833e62?w=400",
        "specifications": {
            "Capacity": "6 Quart",
            "Functions": "7-in-1",
            "Power": "1000W",
            "Material": "Stainless Steel"
        },
        "is_active": True,
        "is_featured": False,
        "tags": ["kitchen", "appliance", "pressure-cooker", "instant-pot"],
        "rating": 4.7,
        "review_count": 12000,
    },
    {
        "name": "The Psychology of Money",
        "name_lower": "the psychology of money",
        "description": "Timeless lessons on wealth, greed, and happiness by Morgan Housel. A New York Times bestseller.",
        "price": 399,
        "original_price": 499,
        "category": "Books",
        "brand": "Jaico Publishing",
        "sku": "BOOK-PSYMONEY",
        "stock_quantity": 500,
        "images": [
            "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
        "specifications": {
            "Author": "Morgan Housel",
            "Pages": "256",
            "Language": "English",
            "Format": "Paperback"
        },
        "is_active": True,
        "is_featured": False,
        "tags": ["book", "finance", "psychology", "bestseller"],
        "rating": 4.8,
        "review_count": 25000,
    },
    {
        "name": "Dyson V15 Detect Vacuum",
        "name_lower": "dyson v15 detect vacuum",
        "description": "Reveals invisible dust with a laser. Most powerful and intelligent cordless vacuum from Dyson.",
        "price": 62900,
        "original_price": 69900,
        "category": "Home & Kitchen",
        "brand": "Dyson",
        "sku": "DYSON-V15-DET",
        "stock_quantity": 25,
        "images": [
            "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=400",
        "specifications": {
            "Runtime": "Up to 60 minutes",
            "Suction": "230 AW",
            "Dustbin": "0.76L",
            "Weight": "3.1 kg"
        },
        "is_active": True,
        "is_featured": True,
        "tags": ["vacuum", "dyson", "cordless", "cleaning"],
        "rating": 4.6,
        "review_count": 890,
    },
    {
        "name": "Fitbit Charge 6",
        "name_lower": "fitbit charge 6",
        "description": "Advanced health & fitness tracker with built-in GPS, stress management tools, and 7-day battery life.",
        "price": 14999,
        "original_price": 16999,
        "category": "Electronics",
        "brand": "Fitbit",
        "sku": "FITBIT-CHG6",
        "stock_quantity": 120,
        "images": [
            "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400"
        ],
        "thumbnail": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400",
        "specifications": {
            "Display": "AMOLED touchscreen",
            "GPS": "Built-in",
            "Battery": "7 days",
            "Water Resistant": "50m"
        },
        "is_active": True,
        "is_featured": False,
        "tags": ["fitness", "tracker", "smartwatch", "fitbit"],
        "rating": 4.4,
        "review_count": 2100,
    },
]


def seed_products():
    """Seed products to Firestore."""
    from app.firebase import init_firebase, product_repo

    print("Initializing Firebase...")
    init_firebase()

    print(f"Seeding {len(SAMPLE_PRODUCTS)} products...")

    for i, product in enumerate(SAMPLE_PRODUCTS, 1):
        product["created_at"] = datetime.utcnow().isoformat()
        product["updated_at"] = datetime.utcnow().isoformat()

        try:
            # Use sync method since we're running outside of async context
            product_repo.collection.add(product)
            print(f"  [{i}/{len(SAMPLE_PRODUCTS)}] Added: {product['name']}")
        except Exception as e:
            print(f"  Error adding {product['name']}: {e}")

    print("\nSeeding complete!")
    print(f"Total products added: {len(SAMPLE_PRODUCTS)}")


def seed_admin_user():
    """Create an admin user for testing."""
    from app.firebase import init_firebase, user_repo
    from app.auth.utils import hash_password

    print("\nCreating admin user...")

    admin_data = {
        "email": "admin@shopease.com",
        "password_hash": hash_password("Admin123!"),
        "first_name": "Admin",
        "last_name": "User",
        "phone": "9999999999",
        "is_active": True,
        "is_admin": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        user_repo.collection.add(admin_data)
        print("  Admin user created!")
        print("  Email: admin@shopease.com")
        print("  Password: Admin123!")
    except Exception as e:
        print(f"  Error creating admin: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("E-Commerce Data Seeder")
    print("=" * 50)

    try:
        seed_products()
        seed_admin_user()
        print("\n" + "=" * 50)
        print("All done! You can now start the application.")
        print("=" * 50)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("  1. Set up Firebase credentials in .env file")
        print("  2. Installed all requirements (pip install -r backend/requirements.txt)")
        sys.exit(1)
