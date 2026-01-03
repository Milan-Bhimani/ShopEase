# E-Commerce Web Application

A complete e-commerce web application with FastAPI backend, Firebase Firestore database, and Bootstrap 5 frontend.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI       │────▶│   Firebase      │
│   (Bootstrap)   │     │   Backend       │     │   Firestore     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     HTML/JS              REST API              Document DB
```

**Tech Stack:**
- **Backend:** Python 3.11 + FastAPI
- **Database:** Google Firebase Firestore
- **Frontend:** HTML5 + Bootstrap 5.3 + Vanilla JavaScript
- **Authentication:** JWT tokens with bcrypt password hashing
- **Containerization:** Docker + Docker Compose
- **Deployment:** Google Cloud Run

## Project Structure

```
ecommerce-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Configuration management
│   │   ├── firebase.py          # Firebase initialization & repositories
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # Auth endpoints
│   │   │   ├── utils.py         # Password hashing, JWT
│   │   │   └── dependencies.py  # Auth middleware
│   │   ├── models/
│   │   │   ├── user.py          # User Pydantic models
│   │   │   ├── product.py       # Product models
│   │   │   ├── cart.py          # Cart models
│   │   │   ├── order.py         # Order & Payment models
│   │   │   └── address.py       # Address models
│   │   ├── routes/
│   │   │   ├── users.py         # User profile endpoints
│   │   │   ├── products.py      # Product catalog endpoints
│   │   │   ├── cart.py          # Shopping cart endpoints
│   │   │   ├── orders.py        # Order & checkout endpoints
│   │   │   └── addresses.py     # Address management endpoints
│   │   └── utils/
│   │       └── validators.py    # Input validation utilities
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── index.html               # Home page
│   ├── login.html               # Login page
│   ├── signup.html              # Registration page
│   ├── product.html             # Product detail page
│   ├── cart.html                # Shopping cart page
│   ├── checkout.html            # Checkout page
│   ├── confirmation.html        # Order confirmation page
│   ├── profile.html             # User profile & orders
│   ├── css/
│   │   └── styles.css           # Custom styles
│   └── js/
│       ├── api.js               # API client
│       └── utils.js             # Utility functions
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_auth.py             # Auth tests
│   ├── test_cart.py             # Cart tests
│   └── test_orders.py           # Order tests
├── docker-compose.yml
├── nginx.conf
├── API_DOCS.md
└── README.md
```

## Features

### Backend
- RESTful API with automatic OpenAPI documentation
- JWT-based authentication with secure password hashing (bcrypt)
- Firebase Firestore integration with async operations
- Input validation using Pydantic models
- CORS support for cross-origin requests
- Rate limiting and security headers (via nginx)

### Frontend
- Responsive design (mobile-first) with Bootstrap 5
- Product catalog with search and category filtering
- Shopping cart with real-time updates
- Checkout with multiple payment methods
- User profile with order history
- Address management

### Payment Methods
- Credit/Debit Card (dummy processing)
- UPI
- Net Banking
- Cash on Delivery

## Local Development Setup

### Prerequisites
- Python 3.11+
- Firebase project with Firestore enabled
- Docker (optional, for containerized setup)

### 1. Clone and Setup

```bash
cd ecommerce-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 2. Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing
3. Enable Firestore Database
4. Go to Project Settings > Service Accounts
5. Generate new private key (JSON)
6. Save as `serviceAccountKey.json` or set environment variables

### 3. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp backend/.env.example backend/.env
```

Edit `.env`:
```env
# Application
DEBUG=true
JWT_SECRET_KEY=your-secure-random-key-here

# Firebase (Option 1: Use JSON file)
FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json

# Firebase (Option 2: Use environment variables)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789

# CORS
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### 4. Seed Sample Data (Optional)

```bash
python scripts/seed_data.py
```

### 5. Run the Application

```bash
# From backend directory
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Docker Setup

### Build and Run with Docker Compose

```bash
# Set environment variables
export JWT_SECRET_KEY=your-secret-key
export FIREBASE_PROJECT_ID=your-project
# ... other Firebase variables

# Build and run
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### With Nginx (Production)

```bash
docker-compose --profile production up --build
```

## Running Tests

```bash
# From project root
cd tests
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

## Google Cloud Deployment

### Prerequisites
- Google Cloud account with billing enabled
- gcloud CLI installed and configured
- Docker installed locally

### Step 1: Setup Google Cloud Project

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Configure Firebase

Your Firebase project should be in the same Google Cloud project, or you need to add the Cloud Run service account to Firebase.

### Step 3: Build and Push Docker Image

```bash
# Configure Docker for Google Container Registry
gcloud auth configure-docker

# Build the image
docker build -t gcr.io/YOUR_PROJECT_ID/ecommerce-api:latest -f backend/Dockerfile .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/ecommerce-api:latest
```

### Step 4: Deploy to Cloud Run

```bash
gcloud run deploy ecommerce-api \
  --image gcr.io/YOUR_PROJECT_ID/ecommerce-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "JWT_SECRET_KEY=your-production-secret" \
  --set-env-vars "FIREBASE_PROJECT_ID=your-project-id" \
  --set-env-vars "FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com" \
  --set-env-vars "DEBUG=false" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

**Note:** For the Firebase private key, use Google Secret Manager:

```bash
# Create secret
echo -n "YOUR_PRIVATE_KEY" | gcloud secrets create firebase-private-key --data-file=-

# Deploy with secret
gcloud run deploy ecommerce-api \
  --image gcr.io/YOUR_PROJECT_ID/ecommerce-api:latest \
  --set-secrets "FIREBASE_PRIVATE_KEY=firebase-private-key:latest"
```

### Step 5: Configure Custom Domain (Optional)

```bash
gcloud run domain-mappings create \
  --service ecommerce-api \
  --domain your-domain.com \
  --region us-central1
```

### Step 6: Frontend Deployment

For the frontend, you can either:

1. **Include in Docker image** (already configured)
2. **Deploy to Firebase Hosting:**

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize Firebase Hosting
firebase init hosting

# Deploy
firebase deploy --only hosting
```

3. **Deploy to Cloud Storage + CDN:**

```bash
# Create bucket
gsutil mb gs://your-frontend-bucket

# Copy files
gsutil -m cp -r frontend/* gs://your-frontend-bucket/

# Make public
gsutil iam ch allUsers:objectViewer gs://your-frontend-bucket
```

## API Documentation

See [API_DOCS.md](API_DOCS.md) for complete API reference.

### Quick Reference

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/auth/register` | POST | Register new user | No |
| `/api/auth/login` | POST | Login | No |
| `/api/auth/me` | GET | Get current user | Yes |
| `/api/products` | GET | List products | No |
| `/api/products/{id}` | GET | Get product | No |
| `/api/cart` | GET | Get cart | Yes |
| `/api/cart/items` | POST | Add to cart | Yes |
| `/api/orders` | POST | Create order | Yes |
| `/api/orders` | GET | List orders | Yes |
| `/api/addresses` | GET/POST | Manage addresses | Yes |

## Test Plan

### Unit Tests
- Authentication (register, login, token validation)
- Cart operations (add, update, remove, clear)
- Order creation and cancellation
- Address CRUD operations

### Integration Tests
- Complete checkout flow
- User registration to order placement
- Cart persistence across sessions

### Manual Test Scenarios

1. **User Registration & Login**
   - Register new account
   - Login with credentials
   - Verify token persistence

2. **Product Browsing**
   - View product listing
   - Filter by category
   - Search products
   - View product details

3. **Cart Operations**
   - Add product to cart
   - Update quantity
   - Remove item
   - Verify price calculations

4. **Checkout Flow**
   - Add shipping address
   - Select payment method
   - Place order (Card, UPI, COD)
   - View confirmation

5. **Order Management**
   - View order history
   - Cancel pending order
   - Track order status

## Security Considerations

- Passwords hashed with bcrypt (work factor 12)
- JWT tokens with configurable expiration
- HTTPS required in production
- CORS configured for specific origins
- Input validation on all endpoints
- SQL injection prevention (Firestore is NoSQL)
- XSS protection via content security headers

## Future Enhancements

- Email notifications (order confirmation, shipping updates)
- Product reviews and ratings
- Wishlist functionality
- Coupon/discount codes
- Inventory management
- Admin dashboard
- Real payment gateway integration (Razorpay, Stripe)
- Push notifications for mobile app

## License

MIT License - see LICENSE file for details.
