#!/usr/bin/env python3
"""
==============================================================================
ShopEase Fresh Data Seeder (seed_fresh_data.py)
==============================================================================

PURPOSE:
--------
Complete database reset script that clears all existing products and
repopulates Firestore with 50 diverse products across multiple categories.

This is the RECOMMENDED seeder for setting up a fresh database.

USAGE:
------
    cd /path/to/ecommerce-app
    python scripts/seed_fresh_data.py

PREREQUISITES:
--------------
1. Firebase credentials configured in backend/.env file
2. Backend dependencies installed:
   pip install -r backend/requirements.txt

WHAT THIS SCRIPT DOES:
----------------------
1. Initializes Firebase connection
2. DELETES all existing products (clears the products collection)
3. Adds 50 new products organized by category:

   ELECTRONICS (10 products):
   - Apple iPhone 15 Pro, Samsung Galaxy S24 Ultra
   - Sony WH-1000XM5, AirPods Pro 2, JBL Flip 6
   - Apple Watch Series 9, Canon EOS R50
   - Samsung TV, Bose QC Earbuds, Logitech Mouse

   COMPUTERS (5 products):
   - MacBook Air M3, Dell XPS 15
   - iPad Pro M4, ASUS ROG Gaming
   - Lenovo ThinkPad X1 Carbon

   FASHION (10 products):
   - Nike Air Max, Levi's 501, Adidas Ultraboost
   - Ray-Ban Aviator, Tommy Polo, Puma RS-X
   - H&M T-Shirts, Fossil Watch, Zara Blazer, CK Belt

   HOME & KITCHEN (10 products):
   - Instant Pot, Dyson V15, Philips Air Fryer
   - Nespresso, Le Creuset, KitchenAid Mixer
   - iRobot Roomba, Vitamix, Casper Pillow, Brabantia

   BOOKS (5 products):
   - Atomic Habits, Psychology of Money, Sapiens
   - Deep Work, Thinking Fast and Slow

   SPORTS & FITNESS (5 products):
   - Fitbit Charge 6, Yoga Mat, Bowflex Dumbbells
   - Wilson Tennis Racket, Under Armour Bag

   BEAUTY (5 products):
   - Dyson Airwrap, Philips Shaver, Oral-B iO
   - SK-II Essence, Foreo Luna

PRODUCT CATEGORIES:
-------------------
- Electronics (10)
- Computers (5)
- Fashion (10)
- Home & Kitchen (10)
- Books (5)
- Sports & Fitness (5)
- Beauty (5)

Total: 50 products with realistic Indian pricing (in INR)

WARNING:
--------
This script DELETES ALL existing products before adding new ones.
Any custom products or modifications will be lost.
Use this for fresh setups or complete resets only.
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 50 Fresh Products - Diverse Categories
PRODUCTS = [
    # Electronics (10 products)
    {
        "name": "Apple iPhone 15 Pro",
        "description": "Premium titanium design with A17 Pro chip. 48MP camera system with 5x optical zoom. Action button for quick access.",
        "price": 134900,
        "original_price": 149900,
        "category": "Electronics",
        "brand": "Apple",
        "sku": "IPHONE15PRO-256",
        "stock_quantity": 45,
        "images": ["https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400",
        "specifications": {"Display": "6.1-inch Super Retina XDR", "Chip": "A17 Pro", "Storage": "256GB", "Camera": "48MP Triple"},
        "is_active": True,
        "is_featured": True,
        "tags": ["smartphone", "apple", "iphone", "5g", "premium"],
        "rating": 4.8,
        "review_count": 2450,
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "description": "Galaxy AI powered smartphone with S Pen. 200MP camera, titanium frame, and Snapdragon 8 Gen 3.",
        "price": 129999,
        "original_price": 144999,
        "category": "Electronics",
        "brand": "Samsung",
        "sku": "GALAXY-S24U-256",
        "stock_quantity": 60,
        "images": ["https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400",
        "specifications": {"Display": "6.8-inch QHD+ AMOLED", "Processor": "Snapdragon 8 Gen 3", "Storage": "256GB", "Camera": "200MP"},
        "is_active": True,
        "is_featured": True,
        "tags": ["smartphone", "samsung", "galaxy", "android", "s-pen"],
        "rating": 4.7,
        "review_count": 1890,
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "description": "Industry-leading noise cancellation with 30-hour battery. Ultra-comfortable design with premium sound.",
        "price": 26990,
        "original_price": 34990,
        "category": "Electronics",
        "brand": "Sony",
        "sku": "SONY-WH1000XM5-BLK",
        "stock_quantity": 85,
        "images": ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
        "specifications": {"Type": "Over-ear", "Battery": "30 hours", "Noise Canceling": "Yes", "Connectivity": "Bluetooth 5.2"},
        "is_active": True,
        "is_featured": True,
        "tags": ["headphones", "wireless", "noise-canceling", "sony", "premium"],
        "rating": 4.9,
        "review_count": 5620,
    },
    {
        "name": "Apple AirPods Pro 2",
        "description": "Adaptive Audio with personalized Spatial Audio. USB-C charging case with precision finding.",
        "price": 24900,
        "original_price": 26900,
        "category": "Electronics",
        "brand": "Apple",
        "sku": "AIRPODS-PRO2-USBC",
        "stock_quantity": 120,
        "images": ["https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=400",
        "specifications": {"Type": "In-ear", "Battery": "6 hours", "Case Battery": "30 hours", "ANC": "Yes"},
        "is_active": True,
        "is_featured": False,
        "tags": ["earbuds", "wireless", "apple", "airpods", "anc"],
        "rating": 4.8,
        "review_count": 8920,
    },
    {
        "name": "JBL Flip 6 Portable Speaker",
        "description": "Bold sound with deep bass. IP67 waterproof and dustproof. 12 hours of playtime.",
        "price": 9999,
        "original_price": 12999,
        "category": "Electronics",
        "brand": "JBL",
        "sku": "JBL-FLIP6-BLU",
        "stock_quantity": 150,
        "images": ["https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400",
        "specifications": {"Battery": "12 hours", "Waterproof": "IP67", "Bluetooth": "5.1", "Power": "30W"},
        "is_active": True,
        "is_featured": False,
        "tags": ["speaker", "bluetooth", "portable", "jbl", "waterproof"],
        "rating": 4.6,
        "review_count": 3450,
    },
    {
        "name": "Apple Watch Series 9",
        "description": "Powerful health and fitness companion. Double tap gesture, brighter display, and carbon neutral.",
        "price": 41900,
        "original_price": 44900,
        "category": "Electronics",
        "brand": "Apple",
        "sku": "WATCH-S9-45MM",
        "stock_quantity": 70,
        "images": ["https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400",
        "specifications": {"Display": "45mm Always-On Retina", "Chip": "S9 SiP", "Battery": "18 hours", "Water Resistant": "50m"},
        "is_active": True,
        "is_featured": True,
        "tags": ["smartwatch", "apple", "fitness", "health", "wearable"],
        "rating": 4.7,
        "review_count": 2180,
    },
    {
        "name": "Canon EOS R50 Mirrorless Camera",
        "description": "Compact mirrorless camera perfect for content creators. 4K video and advanced autofocus.",
        "price": 72990,
        "original_price": 79990,
        "category": "Electronics",
        "brand": "Canon",
        "sku": "CANON-EOSR50-KIT",
        "stock_quantity": 25,
        "images": ["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400",
        "specifications": {"Sensor": "24.2MP APS-C", "Video": "4K 30fps", "ISO": "100-32000", "AF Points": "651"},
        "is_active": True,
        "is_featured": False,
        "tags": ["camera", "mirrorless", "canon", "photography", "4k"],
        "rating": 4.5,
        "review_count": 890,
    },
    {
        "name": "Samsung 55\" Crystal UHD TV",
        "description": "Crystal Processor 4K for stunning picture quality. Smart TV with built-in voice assistants.",
        "price": 47990,
        "original_price": 59990,
        "category": "Electronics",
        "brand": "Samsung",
        "sku": "SAM-TV55-CU8000",
        "stock_quantity": 35,
        "images": ["https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400",
        "specifications": {"Screen": "55-inch", "Resolution": "4K UHD", "HDR": "HDR10+", "Smart TV": "Tizen OS"},
        "is_active": True,
        "is_featured": False,
        "tags": ["tv", "samsung", "4k", "smart-tv", "uhd"],
        "rating": 4.4,
        "review_count": 1560,
    },
    {
        "name": "Bose QuietComfort Earbuds II",
        "description": "World-class noise cancellation in a compact form. CustomTune technology for personalized sound.",
        "price": 22990,
        "original_price": 26900,
        "category": "Electronics",
        "brand": "Bose",
        "sku": "BOSE-QCEB2-BLK",
        "stock_quantity": 65,
        "images": ["https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400",
        "specifications": {"Type": "In-ear", "Battery": "6 hours", "ANC": "CustomTune", "IPX": "IPX4"},
        "is_active": True,
        "is_featured": False,
        "tags": ["earbuds", "bose", "noise-canceling", "wireless", "premium"],
        "rating": 4.6,
        "review_count": 2340,
    },
    {
        "name": "Logitech MX Master 3S Mouse",
        "description": "Precision wireless mouse with MagSpeed scrolling. Quiet clicks and ergonomic design.",
        "price": 9995,
        "original_price": 10995,
        "category": "Electronics",
        "brand": "Logitech",
        "sku": "LOGI-MXM3S-GRY",
        "stock_quantity": 90,
        "images": ["https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400",
        "specifications": {"DPI": "8000", "Battery": "70 days", "Connectivity": "Bluetooth/USB", "Buttons": "7"},
        "is_active": True,
        "is_featured": False,
        "tags": ["mouse", "wireless", "logitech", "ergonomic", "productivity"],
        "rating": 4.8,
        "review_count": 4560,
    },

    # Computers (5 products)
    {
        "name": "MacBook Air M3 13-inch",
        "description": "Supercharged by M3 chip. Fanless design, stunning Liquid Retina display, 18-hour battery.",
        "price": 114900,
        "original_price": 119900,
        "category": "Computers",
        "brand": "Apple",
        "sku": "MBA-M3-13-256",
        "stock_quantity": 40,
        "images": ["https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400",
        "specifications": {"Chip": "Apple M3", "Memory": "8GB", "Storage": "256GB SSD", "Display": "13.6-inch Liquid Retina"},
        "is_active": True,
        "is_featured": True,
        "tags": ["laptop", "macbook", "apple", "m3", "ultrabook"],
        "rating": 4.9,
        "review_count": 1250,
    },
    {
        "name": "Dell XPS 15 Laptop",
        "description": "Premium Windows laptop with 3.5K OLED display. Intel Core i7 and RTX 4060 graphics.",
        "price": 189990,
        "original_price": 209990,
        "category": "Computers",
        "brand": "Dell",
        "sku": "DELL-XPS15-I7",
        "stock_quantity": 20,
        "images": ["https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400",
        "specifications": {"Processor": "Intel Core i7-13700H", "Memory": "16GB", "Storage": "512GB SSD", "Display": "15.6-inch OLED"},
        "is_active": True,
        "is_featured": False,
        "tags": ["laptop", "dell", "xps", "windows", "oled"],
        "rating": 4.6,
        "review_count": 780,
    },
    {
        "name": "Apple iPad Pro 12.9-inch M4",
        "description": "The thinnest Apple product ever. Ultra Retina XDR display with tandem OLED technology.",
        "price": 119900,
        "original_price": 124900,
        "category": "Computers",
        "brand": "Apple",
        "sku": "IPADPRO-M4-256",
        "stock_quantity": 35,
        "images": ["https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400",
        "specifications": {"Chip": "Apple M4", "Display": "12.9-inch Ultra Retina XDR", "Storage": "256GB", "Camera": "12MP Wide"},
        "is_active": True,
        "is_featured": True,
        "tags": ["tablet", "ipad", "apple", "m4", "pro"],
        "rating": 4.8,
        "review_count": 650,
    },
    {
        "name": "ASUS ROG Strix Gaming Laptop",
        "description": "Powerful gaming laptop with RTX 4070. 165Hz display and advanced cooling system.",
        "price": 159990,
        "original_price": 179990,
        "category": "Computers",
        "brand": "ASUS",
        "sku": "ASUS-ROG-G16",
        "stock_quantity": 15,
        "images": ["https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400",
        "specifications": {"Processor": "Intel Core i9-13980HX", "GPU": "RTX 4070", "Display": "16-inch 165Hz", "Memory": "32GB"},
        "is_active": True,
        "is_featured": False,
        "tags": ["laptop", "gaming", "asus", "rog", "rtx"],
        "rating": 4.7,
        "review_count": 420,
    },
    {
        "name": "Lenovo ThinkPad X1 Carbon",
        "description": "Ultra-light business laptop built for professionals. Military-grade durability with all-day battery.",
        "price": 169990,
        "original_price": 189990,
        "category": "Computers",
        "brand": "Lenovo",
        "sku": "LENOVO-X1C-GEN11",
        "stock_quantity": 25,
        "images": ["https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400",
        "specifications": {"Processor": "Intel Core i7-1365U", "Memory": "16GB", "Storage": "512GB SSD", "Display": "14-inch 2.8K OLED"},
        "is_active": True,
        "is_featured": False,
        "tags": ["laptop", "business", "lenovo", "thinkpad", "ultrabook"],
        "rating": 4.7,
        "review_count": 890,
    },

    # Fashion (10 products)
    {
        "name": "Nike Air Max 270",
        "description": "Iconic sneakers with the tallest Air unit yet. Breathable mesh upper and comfortable cushioning.",
        "price": 12995,
        "original_price": 15995,
        "category": "Fashion",
        "brand": "Nike",
        "sku": "NIKE-AM270-BLK-42",
        "stock_quantity": 180,
        "images": ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "specifications": {"Upper": "Mesh/Synthetic", "Sole": "Air Max 270 unit", "Closure": "Lace-up", "Style": "Lifestyle"},
        "is_active": True,
        "is_featured": True,
        "tags": ["shoes", "nike", "sneakers", "airmax", "running"],
        "rating": 4.6,
        "review_count": 8920,
    },
    {
        "name": "Levi's 501 Original Jeans",
        "description": "The original blue jean since 1873. Iconic straight fit with button fly.",
        "price": 4999,
        "original_price": 6499,
        "category": "Fashion",
        "brand": "Levi's",
        "sku": "LEVIS-501-INDIGO-32",
        "stock_quantity": 200,
        "images": ["https://images.unsplash.com/photo-1542272604-787c3835535d?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400",
        "specifications": {"Fit": "Original Straight", "Rise": "Regular", "Material": "100% Cotton Denim", "Closure": "Button Fly"},
        "is_active": True,
        "is_featured": False,
        "tags": ["jeans", "denim", "levis", "501", "classic"],
        "rating": 4.7,
        "review_count": 12450,
    },
    {
        "name": "Adidas Ultraboost 23",
        "description": "Premium running shoes with BOOST midsole. Primeknit+ upper for adaptive fit.",
        "price": 16999,
        "original_price": 19999,
        "category": "Fashion",
        "brand": "Adidas",
        "sku": "ADIDAS-UB23-WHT-43",
        "stock_quantity": 95,
        "images": ["https://images.unsplash.com/photo-1556906781-9a412961c28c?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1556906781-9a412961c28c?w=400",
        "specifications": {"Upper": "Primeknit+", "Midsole": "BOOST", "Outsole": "Continental Rubber", "Drop": "10mm"},
        "is_active": True,
        "is_featured": False,
        "tags": ["shoes", "adidas", "running", "ultraboost", "performance"],
        "rating": 4.8,
        "review_count": 5670,
    },
    {
        "name": "Ray-Ban Aviator Classic",
        "description": "Timeless aviator sunglasses with gold frame. Crystal green lenses with 100% UV protection.",
        "price": 15490,
        "original_price": 16990,
        "category": "Fashion",
        "brand": "Ray-Ban",
        "sku": "RAYBAN-AVT-GOLD",
        "stock_quantity": 75,
        "images": ["https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400",
        "specifications": {"Frame": "Gold Metal", "Lens": "Crystal Green", "UV Protection": "100%", "Size": "58mm"},
        "is_active": True,
        "is_featured": False,
        "tags": ["sunglasses", "rayban", "aviator", "eyewear", "classic"],
        "rating": 4.7,
        "review_count": 6780,
    },
    {
        "name": "Tommy Hilfiger Polo Shirt",
        "description": "Classic fit polo with signature flag logo. Premium pique cotton for everyday comfort.",
        "price": 3999,
        "original_price": 4999,
        "category": "Fashion",
        "brand": "Tommy Hilfiger",
        "sku": "TH-POLO-NVY-L",
        "stock_quantity": 150,
        "images": ["https://images.unsplash.com/photo-1625910513413-5fc58dc39d95?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1625910513413-5fc58dc39d95?w=400",
        "specifications": {"Fit": "Classic", "Material": "100% Cotton Pique", "Collar": "Ribbed", "Closure": "Button Placket"},
        "is_active": True,
        "is_featured": False,
        "tags": ["polo", "shirt", "tommy", "casual", "classic"],
        "rating": 4.5,
        "review_count": 3240,
    },
    {
        "name": "Puma RS-X Sneakers",
        "description": "Retro-inspired chunky sneakers with bold design. Running System technology for comfort.",
        "price": 8999,
        "original_price": 10999,
        "category": "Fashion",
        "brand": "Puma",
        "sku": "PUMA-RSX-MLT-41",
        "stock_quantity": 110,
        "images": ["https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400",
        "specifications": {"Upper": "Mesh/Leather", "Sole": "RS cushioning", "Style": "Retro/Chunky", "Closure": "Lace-up"},
        "is_active": True,
        "is_featured": False,
        "tags": ["shoes", "puma", "sneakers", "retro", "chunky"],
        "rating": 4.4,
        "review_count": 2180,
    },
    {
        "name": "H&M Cotton T-Shirt Pack",
        "description": "Essential crew neck t-shirts in a 3-pack. Soft organic cotton for everyday wear.",
        "price": 1499,
        "original_price": 1999,
        "category": "Fashion",
        "brand": "H&M",
        "sku": "HM-TSHIRT-3PK-M",
        "stock_quantity": 300,
        "images": ["https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
        "specifications": {"Material": "100% Organic Cotton", "Fit": "Regular", "Neckline": "Crew neck", "Pack": "3 pieces"},
        "is_active": True,
        "is_featured": False,
        "tags": ["tshirt", "basic", "cotton", "pack", "essential"],
        "rating": 4.3,
        "review_count": 8920,
    },
    {
        "name": "Fossil Minimalist Watch",
        "description": "Clean and modern leather watch with slim profile. Quartz movement and water resistant.",
        "price": 9995,
        "original_price": 12995,
        "category": "Fashion",
        "brand": "Fossil",
        "sku": "FOSSIL-MIN-BRN",
        "stock_quantity": 55,
        "images": ["https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400",
        "specifications": {"Movement": "Quartz", "Case": "44mm Stainless Steel", "Strap": "Genuine Leather", "Water Resistant": "50m"},
        "is_active": True,
        "is_featured": False,
        "tags": ["watch", "fossil", "leather", "minimalist", "classic"],
        "rating": 4.6,
        "review_count": 3450,
    },
    {
        "name": "Zara Slim Fit Blazer",
        "description": "Modern slim fit blazer for smart casual occasions. Lightweight fabric with notch lapels.",
        "price": 6990,
        "original_price": 8990,
        "category": "Fashion",
        "brand": "Zara",
        "sku": "ZARA-BLZR-NVY-40",
        "stock_quantity": 45,
        "images": ["https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400",
        "specifications": {"Fit": "Slim", "Material": "Polyester Blend", "Lapel": "Notch", "Closure": "Two-button"},
        "is_active": True,
        "is_featured": False,
        "tags": ["blazer", "formal", "zara", "slim-fit", "smart-casual"],
        "rating": 4.4,
        "review_count": 1890,
    },
    {
        "name": "Calvin Klein Leather Belt",
        "description": "Classic leather dress belt with signature CK buckle. Reversible black/brown design.",
        "price": 3499,
        "original_price": 4499,
        "category": "Fashion",
        "brand": "Calvin Klein",
        "sku": "CK-BELT-REV-34",
        "stock_quantity": 120,
        "images": ["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400",
        "specifications": {"Material": "Genuine Leather", "Type": "Reversible", "Buckle": "Silver-tone CK", "Width": "35mm"},
        "is_active": True,
        "is_featured": False,
        "tags": ["belt", "leather", "calvin-klein", "reversible", "accessory"],
        "rating": 4.5,
        "review_count": 2670,
    },

    # Home & Kitchen (10 products)
    {
        "name": "Instant Pot Duo 7-in-1",
        "description": "Multi-use pressure cooker, slow cooker, rice cooker, steamer, and more. 6-quart capacity.",
        "price": 8999,
        "original_price": 12999,
        "category": "Home & Kitchen",
        "brand": "Instant Pot",
        "sku": "IPOT-DUO-6QT",
        "stock_quantity": 70,
        "images": ["https://images.unsplash.com/photo-1585515320310-259814833e62?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1585515320310-259814833e62?w=400",
        "specifications": {"Capacity": "6 Quart", "Functions": "7-in-1", "Power": "1000W", "Material": "Stainless Steel"},
        "is_active": True,
        "is_featured": True,
        "tags": ["kitchen", "appliance", "pressure-cooker", "instant-pot", "cooking"],
        "rating": 4.7,
        "review_count": 24560,
    },
    {
        "name": "Dyson V15 Detect Vacuum",
        "description": "Intelligent cordless vacuum with laser dust detection. Piezo sensor for real-time particle counting.",
        "price": 62900,
        "original_price": 69900,
        "category": "Home & Kitchen",
        "brand": "Dyson",
        "sku": "DYSON-V15-DET",
        "stock_quantity": 30,
        "images": ["https://images.unsplash.com/photo-1558317374-067fb5f30001?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=400",
        "specifications": {"Runtime": "60 minutes", "Suction": "230 AW", "Bin Capacity": "0.76L", "Weight": "3.1 kg"},
        "is_active": True,
        "is_featured": True,
        "tags": ["vacuum", "dyson", "cordless", "cleaning", "smart"],
        "rating": 4.8,
        "review_count": 3450,
    },
    {
        "name": "Philips Air Fryer XXL",
        "description": "Rapid Air technology for healthier frying. Extra large capacity for family meals.",
        "price": 19990,
        "original_price": 24990,
        "category": "Home & Kitchen",
        "brand": "Philips",
        "sku": "PHILIPS-AF-XXL",
        "stock_quantity": 55,
        "images": ["https://images.unsplash.com/photo-1626509653291-18d9a934b9db?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1626509653291-18d9a934b9db?w=400",
        "specifications": {"Capacity": "1.4 kg", "Power": "2225W", "Technology": "Rapid Air", "Display": "Digital"},
        "is_active": True,
        "is_featured": False,
        "tags": ["air-fryer", "philips", "kitchen", "cooking", "healthy"],
        "rating": 4.6,
        "review_count": 5670,
    },
    {
        "name": "Nespresso Vertuo Next",
        "description": "Coffee machine with Centrifusion technology. Brews 5 cup sizes from espresso to carafe.",
        "price": 15990,
        "original_price": 18990,
        "category": "Home & Kitchen",
        "brand": "Nespresso",
        "sku": "NESPRESSO-VN-BLK",
        "stock_quantity": 40,
        "images": ["https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=400",
        "specifications": {"Technology": "Centrifusion", "Cup Sizes": "5", "Water Tank": "1.1L", "Preheat": "30 seconds"},
        "is_active": True,
        "is_featured": False,
        "tags": ["coffee", "nespresso", "espresso", "kitchen", "appliance"],
        "rating": 4.5,
        "review_count": 4230,
    },
    {
        "name": "Le Creuset Dutch Oven",
        "description": "Iconic enameled cast iron pot for perfect braising. Superior heat retention and distribution.",
        "price": 32990,
        "original_price": 36990,
        "category": "Home & Kitchen",
        "brand": "Le Creuset",
        "sku": "LECREUSET-DO-5QT",
        "stock_quantity": 25,
        "images": ["https://images.unsplash.com/photo-1585837575652-267c041d77d4?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1585837575652-267c041d77d4?w=400",
        "specifications": {"Capacity": "5.5 Quart", "Material": "Enameled Cast Iron", "Oven Safe": "500°F", "Dishwasher Safe": "Yes"},
        "is_active": True,
        "is_featured": False,
        "tags": ["cookware", "dutch-oven", "le-creuset", "cast-iron", "premium"],
        "rating": 4.9,
        "review_count": 8920,
    },
    {
        "name": "KitchenAid Stand Mixer",
        "description": "Professional-grade stand mixer with 10 speeds. Includes flat beater, dough hook, and wire whip.",
        "price": 44990,
        "original_price": 52990,
        "category": "Home & Kitchen",
        "brand": "KitchenAid",
        "sku": "KITCHENAID-SM-5QT",
        "stock_quantity": 35,
        "images": ["https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400",
        "specifications": {"Capacity": "5 Quart", "Power": "325W", "Speeds": "10", "Attachments": "3 included"},
        "is_active": True,
        "is_featured": False,
        "tags": ["mixer", "kitchenaid", "baking", "kitchen", "appliance"],
        "rating": 4.8,
        "review_count": 12340,
    },
    {
        "name": "iRobot Roomba j7+",
        "description": "Smart robot vacuum with obstacle avoidance. Learns and maps your home for efficient cleaning.",
        "price": 69990,
        "original_price": 79990,
        "category": "Home & Kitchen",
        "brand": "iRobot",
        "sku": "IROBOT-J7PLUS",
        "stock_quantity": 20,
        "images": ["https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
        "specifications": {"Navigation": "iAdapt 3.0", "Suction": "10x Power Lifting", "Battery": "75 min", "Self-Empty": "Yes"},
        "is_active": True,
        "is_featured": False,
        "tags": ["robot", "vacuum", "irobot", "roomba", "smart-home"],
        "rating": 4.5,
        "review_count": 2890,
    },
    {
        "name": "Vitamix Explorian Blender",
        "description": "Professional-grade blending with variable speed control. Aircraft-grade stainless steel blades.",
        "price": 39990,
        "original_price": 44990,
        "category": "Home & Kitchen",
        "brand": "Vitamix",
        "sku": "VITAMIX-E310",
        "stock_quantity": 30,
        "images": ["https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=400",
        "specifications": {"Capacity": "48 oz", "Motor": "2.0 HP", "Speed": "Variable + Pulse", "BPA-Free": "Yes"},
        "is_active": True,
        "is_featured": False,
        "tags": ["blender", "vitamix", "kitchen", "smoothie", "professional"],
        "rating": 4.8,
        "review_count": 5670,
    },
    {
        "name": "Casper Original Pillow",
        "description": "Two layers of premium pillows in one. Supportive inner core with soft outer layer.",
        "price": 4999,
        "original_price": 5999,
        "category": "Home & Kitchen",
        "brand": "Casper",
        "sku": "CASPER-PILLOW-STD",
        "stock_quantity": 100,
        "images": ["https://images.unsplash.com/photo-1592789705501-f9ae4278a9a5?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1592789705501-f9ae4278a9a5?w=400",
        "specifications": {"Size": "Standard", "Fill": "Polyester Microfiber", "Cover": "100% Cotton", "Washable": "Yes"},
        "is_active": True,
        "is_featured": False,
        "tags": ["pillow", "bedding", "casper", "sleep", "comfort"],
        "rating": 4.4,
        "review_count": 3450,
    },
    {
        "name": "Brabantia Laundry Basket",
        "description": "Stylish 60L laundry basket with lid. Durable plastic with ventilation holes.",
        "price": 2999,
        "original_price": 3499,
        "category": "Home & Kitchen",
        "brand": "Brabantia",
        "sku": "BRABANTIA-LB-60L",
        "stock_quantity": 80,
        "images": ["https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
        "specifications": {"Capacity": "60L", "Material": "Plastic", "Features": "Ventilation holes", "Lid": "Yes"},
        "is_active": True,
        "is_featured": False,
        "tags": ["laundry", "basket", "storage", "home", "organization"],
        "rating": 4.3,
        "review_count": 1230,
    },

    # Books (5 products)
    {
        "name": "Atomic Habits",
        "description": "An Easy & Proven Way to Build Good Habits & Break Bad Ones by James Clear. #1 NYT Bestseller.",
        "price": 499,
        "original_price": 699,
        "category": "Books",
        "brand": "Penguin Random House",
        "sku": "BOOK-ATOMICHABITS",
        "stock_quantity": 400,
        "images": ["https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
        "specifications": {"Author": "James Clear", "Pages": "320", "Language": "English", "Format": "Paperback"},
        "is_active": True,
        "is_featured": True,
        "tags": ["book", "self-help", "habits", "bestseller", "productivity"],
        "rating": 4.8,
        "review_count": 89560,
    },
    {
        "name": "The Psychology of Money",
        "description": "Timeless lessons on wealth, greed, and happiness by Morgan Housel. Financial wisdom for everyone.",
        "price": 399,
        "original_price": 499,
        "category": "Books",
        "brand": "Jaico Publishing",
        "sku": "BOOK-PSYMONEY",
        "stock_quantity": 350,
        "images": ["https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400",
        "specifications": {"Author": "Morgan Housel", "Pages": "256", "Language": "English", "Format": "Paperback"},
        "is_active": True,
        "is_featured": False,
        "tags": ["book", "finance", "psychology", "investing", "wealth"],
        "rating": 4.7,
        "review_count": 45670,
    },
    {
        "name": "Sapiens: A Brief History",
        "description": "A Brief History of Humankind by Yuval Noah Harari. Explores the history of our species.",
        "price": 599,
        "original_price": 799,
        "category": "Books",
        "brand": "Harper Collins",
        "sku": "BOOK-SAPIENS",
        "stock_quantity": 280,
        "images": ["https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400",
        "specifications": {"Author": "Yuval Noah Harari", "Pages": "512", "Language": "English", "Format": "Paperback"},
        "is_active": True,
        "is_featured": False,
        "tags": ["book", "history", "science", "anthropology", "bestseller"],
        "rating": 4.6,
        "review_count": 67890,
    },
    {
        "name": "Deep Work",
        "description": "Rules for Focused Success in a Distracted World by Cal Newport. Master deep work skills.",
        "price": 449,
        "original_price": 599,
        "category": "Books",
        "brand": "Piatkus",
        "sku": "BOOK-DEEPWORK",
        "stock_quantity": 220,
        "images": ["https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400",
        "specifications": {"Author": "Cal Newport", "Pages": "304", "Language": "English", "Format": "Paperback"},
        "is_active": True,
        "is_featured": False,
        "tags": ["book", "productivity", "focus", "work", "self-improvement"],
        "rating": 4.5,
        "review_count": 23450,
    },
    {
        "name": "Thinking, Fast and Slow",
        "description": "A groundbreaking tour of the mind by Nobel laureate Daniel Kahneman. How we think and decide.",
        "price": 549,
        "original_price": 699,
        "category": "Books",
        "brand": "Penguin",
        "sku": "BOOK-THINKFASTSLOW",
        "stock_quantity": 180,
        "images": ["https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400",
        "specifications": {"Author": "Daniel Kahneman", "Pages": "512", "Language": "English", "Format": "Paperback"},
        "is_active": True,
        "is_featured": False,
        "tags": ["book", "psychology", "economics", "decision-making", "nobel"],
        "rating": 4.6,
        "review_count": 34560,
    },

    # Sports & Fitness (5 products)
    {
        "name": "Fitbit Charge 6",
        "description": "Advanced fitness tracker with built-in GPS. Heart rate monitoring, stress management, and 7-day battery.",
        "price": 14999,
        "original_price": 16999,
        "category": "Sports & Fitness",
        "brand": "Fitbit",
        "sku": "FITBIT-CHG6-BLK",
        "stock_quantity": 90,
        "images": ["https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400",
        "specifications": {"Display": "AMOLED", "GPS": "Built-in", "Battery": "7 days", "Water Resistant": "50m"},
        "is_active": True,
        "is_featured": False,
        "tags": ["fitness", "tracker", "fitbit", "health", "wearable"],
        "rating": 4.5,
        "review_count": 4560,
    },
    {
        "name": "Yoga Mat Premium",
        "description": "Extra thick 6mm yoga mat with alignment lines. Non-slip surface with carrying strap included.",
        "price": 1999,
        "original_price": 2499,
        "category": "Sports & Fitness",
        "brand": "Liforme",
        "sku": "YOGA-MAT-6MM-GRY",
        "stock_quantity": 150,
        "images": ["https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400",
        "specifications": {"Thickness": "6mm", "Material": "Eco TPE", "Size": "183x61cm", "Features": "Alignment lines"},
        "is_active": True,
        "is_featured": False,
        "tags": ["yoga", "mat", "fitness", "exercise", "eco-friendly"],
        "rating": 4.6,
        "review_count": 3450,
    },
    {
        "name": "Bowflex Adjustable Dumbbells",
        "description": "Space-saving adjustable dumbbells from 5-52.5 lbs. Replace 15 sets of weights.",
        "price": 34999,
        "original_price": 42999,
        "category": "Sports & Fitness",
        "brand": "Bowflex",
        "sku": "BOWFLEX-DB-552",
        "stock_quantity": 25,
        "images": ["https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400",
        "specifications": {"Weight Range": "5-52.5 lbs", "Increments": "2.5 lbs", "Sets Replaced": "15", "Material": "Steel/Plastic"},
        "is_active": True,
        "is_featured": False,
        "tags": ["dumbbells", "weights", "home-gym", "fitness", "adjustable"],
        "rating": 4.7,
        "review_count": 8920,
    },
    {
        "name": "Wilson Tennis Racket",
        "description": "Pro Staff RF97 Autograph. Roger Federer's racket of choice for precision and control.",
        "price": 22990,
        "original_price": 26990,
        "category": "Sports & Fitness",
        "brand": "Wilson",
        "sku": "WILSON-RF97-AUTO",
        "stock_quantity": 35,
        "images": ["https://images.unsplash.com/photo-1617083934555-ac7d4ca95210?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1617083934555-ac7d4ca95210?w=400",
        "specifications": {"Head Size": "97 sq in", "Weight": "340g", "String Pattern": "16x19", "Balance": "31cm"},
        "is_active": True,
        "is_featured": False,
        "tags": ["tennis", "racket", "wilson", "pro", "sports"],
        "rating": 4.8,
        "review_count": 1230,
    },
    {
        "name": "Under Armour Gym Bag",
        "description": "Water-resistant duffle bag with shoe compartment. Perfect for gym and travel.",
        "price": 3999,
        "original_price": 4999,
        "category": "Sports & Fitness",
        "brand": "Under Armour",
        "sku": "UA-DUFFEL-40L",
        "stock_quantity": 85,
        "images": ["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400",
        "specifications": {"Capacity": "40L", "Material": "UA Storm technology", "Pockets": "6", "Strap": "Adjustable shoulder"},
        "is_active": True,
        "is_featured": False,
        "tags": ["bag", "gym", "duffle", "under-armour", "sports"],
        "rating": 4.5,
        "review_count": 2340,
    },

    # Beauty & Personal Care (5 products)
    {
        "name": "Dyson Airwrap Complete",
        "description": "Multi-styler for multiple hair types. Curl, wave, smooth, and dry with no extreme heat.",
        "price": 45900,
        "original_price": 49900,
        "category": "Beauty",
        "brand": "Dyson",
        "sku": "DYSON-AIRWRAP-CMP",
        "stock_quantity": 30,
        "images": ["https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400",
        "specifications": {"Attachments": "6", "Motor": "V9 Digital", "Heat Settings": "3", "Cable": "2.5m"},
        "is_active": True,
        "is_featured": True,
        "tags": ["hair", "styling", "dyson", "airwrap", "beauty"],
        "rating": 4.7,
        "review_count": 4560,
    },
    {
        "name": "Philips Electric Shaver",
        "description": "Series 9000 wet & dry electric shaver. Contour detect technology for 20% closer shave.",
        "price": 24990,
        "original_price": 29990,
        "category": "Beauty",
        "brand": "Philips",
        "sku": "PHILIPS-S9000",
        "stock_quantity": 45,
        "images": ["https://images.unsplash.com/photo-1621607512022-6aecc4fed814?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1621607512022-6aecc4fed814?w=400",
        "specifications": {"Type": "Wet & Dry", "Heads": "3 rotary", "Battery": "60 min", "Cleaning": "SmartClean"},
        "is_active": True,
        "is_featured": False,
        "tags": ["shaver", "grooming", "philips", "electric", "men"],
        "rating": 4.6,
        "review_count": 3450,
    },
    {
        "name": "Oral-B iO Series 9",
        "description": "AI-powered smart toothbrush with 3D tracking. 7 cleaning modes and pressure sensor.",
        "price": 18999,
        "original_price": 24999,
        "category": "Beauty",
        "brand": "Oral-B",
        "sku": "ORALB-IO9-BLK",
        "stock_quantity": 60,
        "images": ["https://images.unsplash.com/photo-1559591938-52eae78d47c8?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1559591938-52eae78d47c8?w=400",
        "specifications": {"Modes": "7", "Battery": "14 days", "Features": "AI tracking", "Display": "Interactive color"},
        "is_active": True,
        "is_featured": False,
        "tags": ["toothbrush", "electric", "oral-b", "dental", "smart"],
        "rating": 4.8,
        "review_count": 2890,
    },
    {
        "name": "SK-II Facial Treatment Essence",
        "description": "Iconic Pitera essence for crystal clear skin. Over 90% Pitera for visible transformation.",
        "price": 14990,
        "original_price": 16990,
        "category": "Beauty",
        "brand": "SK-II",
        "sku": "SKII-FTE-230ML",
        "stock_quantity": 40,
        "images": ["https://images.unsplash.com/photo-1571781926291-c477ebfd024b?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?w=400",
        "specifications": {"Size": "230ml", "Key Ingredient": "Pitera", "Skin Type": "All", "Origin": "Japan"},
        "is_active": True,
        "is_featured": False,
        "tags": ["skincare", "essence", "sk-ii", "luxury", "anti-aging"],
        "rating": 4.7,
        "review_count": 5670,
    },
    {
        "name": "Foreo Luna 4",
        "description": "Smart facial cleansing device with app connectivity. T-Sonic pulsations for deep cleanse.",
        "price": 16990,
        "original_price": 19990,
        "category": "Beauty",
        "brand": "Foreo",
        "sku": "FOREO-LUNA4-PNK",
        "stock_quantity": 35,
        "images": ["https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=400"],
        "thumbnail": "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=400",
        "specifications": {"Technology": "T-Sonic", "Battery": "650 uses", "App": "Yes", "Waterproof": "Yes"},
        "is_active": True,
        "is_featured": False,
        "tags": ["skincare", "cleansing", "foreo", "beauty-tech", "facial"],
        "rating": 4.5,
        "review_count": 2340,
    },
]


def clear_all_products():
    """Delete all existing products from Firestore."""
    from app.firebase import init_firebase, product_repo

    print("Clearing all existing products...")

    try:
        # Get all products
        docs = product_repo.collection.stream()
        count = 0

        for doc in docs:
            doc.reference.delete()
            count += 1

        print(f"  Deleted {count} products")
        return count
    except Exception as e:
        print(f"  Error clearing products: {e}")
        return 0


def seed_products():
    """Seed fresh products to Firestore."""
    from app.firebase import init_firebase, product_repo

    print(f"\nAdding {len(PRODUCTS)} new products...")

    for i, product in enumerate(PRODUCTS, 1):
        # Add metadata
        product["name_lower"] = product["name"].lower()
        product["created_at"] = datetime.utcnow().isoformat()
        product["updated_at"] = datetime.utcnow().isoformat()

        try:
            product_repo.collection.add(product)
            print(f"  [{i}/{len(PRODUCTS)}] Added: {product['name']}")
        except Exception as e:
            print(f"  Error adding {product['name']}: {e}")

    print(f"\nTotal products added: {len(PRODUCTS)}")


if __name__ == "__main__":
    print("=" * 60)
    print("ShopEase Fresh Data Seeder")
    print("=" * 60)

    try:
        from app.firebase import init_firebase

        print("\nInitializing Firebase...")
        init_firebase()

        # Clear existing products
        deleted = clear_all_products()

        # Seed new products
        seed_products()

        print("\n" + "=" * 60)
        print("Done! Refresh your app to see the new products.")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("  1. Set up Firebase credentials in .env file")
        print("  2. Installed all requirements")
        sys.exit(1)
