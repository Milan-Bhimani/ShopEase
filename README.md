# ShopEase - E-Commerce Web Application

A full-featured e-commerce web application built with FastAPI, Firebase Firestore, and Bootstrap 5.

## Live Demo

**Production URL:** https://ecommerce-nfieuqqjy-milans-projects-22ba0caf.vercel.app

**Admin Dashboard:** https://ecommerce-nfieuqqjy-milans-projects-22ba0caf.vercel.app/admin.html
- Email: `admin@shopease.com`
- Password: `Admin123!`

---

## Features

### Customer Features
- Product catalog with search and category filtering
- Shopping cart with real-time updates
- User authentication (JWT-based)
- Multiple payment methods (Card, UPI, Net Banking, COD)
- Order tracking and history
- Address management
- Responsive design (mobile-first)

### Admin Dashboard
- Dashboard with statistics (products, orders, users, revenue)
- Product management (add, edit, delete, toggle visibility)
- Order management (view details, update status)
- User management (view users, toggle active status)

### Technical Features
- RESTful API with automatic OpenAPI documentation
- Firebase Firestore NoSQL database
- JWT authentication with bcrypt password hashing
- Docker containerization
- Vercel deployment ready

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11 + FastAPI |
| Database | Google Firebase Firestore |
| Frontend | HTML5 + Bootstrap 5.3 + Vanilla JS |
| Auth | JWT + bcrypt |
| Deployment | Vercel / Docker |

---

## Project Structure

```
ecommerce-app/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Configuration
│   │   ├── firebase.py             # Database operations
│   │   ├── email.py                # Email utilities
│   │   ├── auth/
│   │   │   ├── routes.py           # Auth endpoints
│   │   │   ├── utils.py            # Password/JWT utilities
│   │   │   └── dependencies.py     # Auth middleware
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   ├── address.py
│   │   │   └── admin.py            # Admin models
│   │   └── routes/
│   │       ├── users.py
│   │       ├── products.py
│   │       ├── cart.py
│   │       ├── orders.py
│   │       ├── addresses.py
│   │       └── admin.py            # Admin endpoints
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html                  # Home page
│   ├── login.html                  # Login
│   ├── signup.html                 # Registration
│   ├── product.html                # Product detail
│   ├── cart.html                   # Shopping cart
│   ├── checkout.html               # Checkout
│   ├── confirmation.html           # Order confirmation
│   ├── profile.html                # User profile
│   ├── search.html                 # Search results
│   ├── admin.html                  # Admin dashboard
│   ├── css/
│   │   ├── styles.css
│   │   └── admin.css
│   ├── js/
│   │   ├── api.js                  # API client
│   │   ├── utils.js                # Utilities
│   │   └── admin.js                # Admin logic
│   └── pages/                      # Static pages
├── scripts/
│   ├── seed_data.py                # Seed 10 products
│   └── seed_fresh_data.py          # Seed 50 products
├── api/
│   └── index.py                    # Vercel serverless entry
├── docker-compose.yml
├── vercel.json
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Firebase project with Firestore enabled
- Node.js (optional, for some tools)

---

## Option 1: Local Development

### Step 1: Clone the Repository

```bash
git clone https://github.com/Milan-Bhimani/ShopEase.git
cd ShopEase
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project (or use existing)
3. Enable **Firestore Database**
4. Go to **Project Settings > Service Accounts**
5. Click **Generate new private key**
6. Save the JSON file

### Step 5: Set Environment Variables

Create `backend/.env` file:

```env
# Application
DEBUG=true
JWT_SECRET_KEY=your-super-secret-key-change-this

# Firebase - Option A: JSON file path
FIREBASE_CREDENTIALS_PATH=C:/path/to/serviceAccountKey.json

# Firebase - Option B: Individual values (for production)
# FIREBASE_PROJECT_ID=your-project-id
# FIREBASE_PRIVATE_KEY_ID=your-private-key-id
# FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
# FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
# FIREBASE_CLIENT_ID=123456789

# CORS
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Step 6: Seed Sample Data (Optional)

```bash
# From project root
cd ..
python scripts/seed_fresh_data.py
```

This creates:
- 50 sample products across categories
- Admin user (admin@shopease.com / Admin123!)

### Step 7: Run the Application

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 8: Access the Application

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Frontend |
| http://localhost:8000/admin.html | Admin Dashboard |
| http://localhost:8000/api/docs | API Documentation |
| http://localhost:8000/api/redoc | API Reference |

---

## Option 2: Docker Setup

### Step 1: Set Environment Variables

Create a `.env` file in the project root:

```env
JWT_SECRET_KEY=your-super-secret-key
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789
```

### Step 2: Build and Run

```bash
# Build and start containers
docker-compose up --build

# Or run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Step 3: Access the Application

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Frontend (via Nginx) |
| http://localhost:8000/admin.html | Admin Dashboard |
| http://localhost:8000/api/docs | API Documentation |

### Docker Commands Reference

```bash
# Rebuild specific service
docker-compose up --build backend

# View running containers
docker-compose ps

# Execute command in container
docker-compose exec backend bash

# View container logs
docker-compose logs backend

# Remove all containers and volumes
docker-compose down -v
```

---

## Option 3: Vercel Deployment

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Configure Environment Variables

In Vercel Dashboard or via CLI:

```bash
vercel env add JWT_SECRET_KEY
vercel env add FIREBASE_PROJECT_ID
vercel env add FIREBASE_PRIVATE_KEY_ID
vercel env add FIREBASE_PRIVATE_KEY
vercel env add FIREBASE_CLIENT_EMAIL
vercel env add FIREBASE_CLIENT_ID
```

### Step 4: Deploy

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

### Step 5: Seed Data (After Deployment)

Run locally with production Firebase credentials:
```bash
python scripts/seed_fresh_data.py
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login | No |
| POST | `/api/auth/logout` | Logout | Yes |
| GET | `/api/auth/me` | Get current user | Yes |

### Products

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/products` | List products | No |
| GET | `/api/products/featured` | Featured products | No |
| GET | `/api/products/categories` | List categories | No |
| GET | `/api/products/{id}` | Get product | No |
| POST | `/api/products` | Create product | Admin |
| PUT | `/api/products/{id}` | Update product | Admin |
| DELETE | `/api/products/{id}` | Delete product | Admin |

### Cart

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/cart` | Get cart | Yes |
| POST | `/api/cart/items` | Add item | Yes |
| PUT | `/api/cart/items/{id}` | Update quantity | Yes |
| DELETE | `/api/cart/items/{id}` | Remove item | Yes |

### Orders

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/orders` | List orders | Yes |
| GET | `/api/orders/{id}` | Get order | Yes |
| POST | `/api/orders` | Create order | Yes |
| POST | `/api/orders/{id}/cancel` | Cancel order | Yes |

### Admin

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/admin/stats` | Dashboard stats | Admin |
| GET | `/api/admin/orders` | All orders | Admin |
| PUT | `/api/admin/orders/{id}/status` | Update status | Admin |
| GET | `/api/admin/users` | All users | Admin |
| PUT | `/api/admin/users/{id}/status` | Toggle user | Admin |
| GET | `/api/admin/products` | All products | Admin |
| PUT | `/api/admin/products/{id}/toggle-active` | Toggle product | Admin |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEBUG` | Enable debug mode | No (default: false) |
| `JWT_SECRET_KEY` | Secret for JWT tokens | Yes |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase JSON | Option A |
| `FIREBASE_PROJECT_ID` | Firebase project ID | Option B |
| `FIREBASE_PRIVATE_KEY_ID` | Firebase private key ID | Option B |
| `FIREBASE_PRIVATE_KEY` | Firebase private key | Option B |
| `FIREBASE_CLIENT_EMAIL` | Firebase client email | Option B |
| `FIREBASE_CLIENT_ID` | Firebase client ID | Option B |
| `CORS_ORIGINS` | Allowed CORS origins | No |

---

## Default Accounts

After running seed script:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@shopease.com | Admin123! |

---

## Troubleshooting

### "Invalid email or password"
- Make sure you ran the seed script: `python scripts/seed_fresh_data.py`
- Check password is exactly: `Admin123!`

### Firebase connection error
- Verify Firebase credentials in `.env`
- Check Firestore is enabled in Firebase Console
- Ensure service account has Firestore access

### CORS errors
- Add your domain to `CORS_ORIGINS` in `.env`
- For local dev: `CORS_ORIGINS=http://localhost:8000`

### Docker issues
```bash
# Reset everything
docker-compose down -v
docker system prune -f
docker-compose up --build
```

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Author

**Milan Bhimani**
- GitHub: [@Milan-Bhimani](https://github.com/Milan-Bhimani)
