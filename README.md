# Bliss Card ✦ Artisan & Luxury Greeting Cards E-Commerce Platform

A complete, production-ready full-stack e-commerce web application called **"Bliss Card"**, engineered for handcrafted, luxury greeting cards, stationery, and bespoke gift boxes.

---

## 🛠️ Tech Stack

- **Frontend**: Plain HTML5, CSS3 (Custom Responsive & Mobile-First Design Tokens), Vanilla Modern JavaScript (ES6+), Fetch API with CSRF token handling.
- **Backend**: Python 3.14+, Django 6.1+, Django REST Framework (DRF) 3.18+.
- **Database**: SQLite3 (Django ORM with atomic transactions).
- **Authentication**: Session-based authentication with hashed passwords (`PBKDF2`), role-based access control (RBAC), and CSRF protection.

---

## 👥 User Roles & Permissions

1. **Admin (`admin`)**:
   - Access to Admin Dashboard (`/admin-dashboard/`) and Django Admin (`/admin/`).
   - Platform analytics: total platform revenue, total orders, pending orders, user counts.
   - Manages all users, sellers, products, categories, and orders.
   - Can update order fulfillment statuses across the entire store.
2. **Seller (`seller`)**:
   - Access to Seller Hub (`/seller-dashboard/`).
   - Seller analytics: total earnings, units sold, active listings, pending fulfillments.
   - Full CRUD over their own greeting card inventory: publish new cards, edit descriptions/pricing/stock, delete cards.
   - Views orders containing their products and updates fulfillment status (`Pending` &rarr; `Shipped` &rarr; `Delivered`).
3. **Buyer (`buyer`)**:
   - Browses catalog with live search, category filtering, and sorting (`/`).
   - Views product detail pages with real-time stock verification (`/products/<id>/`).
   - Adds items to a persistent shopping cart with live subtotal/total calculation (`/cart/`).
   - Checks out with shipping address form and atomic stock deduction (`/checkout/`).
   - Views past order history and can cancel pending orders (`/orders/`).

---

## 📁 Full Folder Structure

```text
Blisscart/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── blisscard/                       # Django project configuration
│   ├── __init__.py
│   ├── settings.py                  # Core settings, custom User, DRF, Media/Static config
│   ├── urls.py                      # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                        # User management & Authentication app
│   ├── migrations/
│   │   └── 0001_initial.py          # Custom User model migrations
│   ├── __init__.py
│   ├── admin.py                     # Custom UserAdmin with role filter & fieldsets
│   ├── apps.py
│   ├── models.py                    # User model (Admin, Seller, Buyer roles)
│   ├── permissions.py               # IsAdminRole, IsSellerRole, IsBuyerRole
│   ├── serializers.py               # UserSerializer, RegisterSerializer, LoginSerializer
│   ├── tests.py                     # Auth and role unit tests
│   ├── urls.py                      # /api/auth/ endpoints
│   └── views.py                     # Register, Login, Logout, CSRF, Me views
├── store/                           # Store Core: Catalog, Cart, Orders, Dashboards
│   ├── management/
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── seed_data.py         # Database seeder with sample accounts & cards
│   ├── migrations/
│   │   └── 0001_initial.py          # Category, Product, Cart, Order migrations
│   ├── __init__.py
│   ├── admin.py                     # Admin customization for Products, Orders, Carts
│   ├── apps.py
│   ├── models.py                    # Category, Product, Cart, CartItem, Order, OrderItem
│   ├── page_urls.py                 # Frontend template routes (/, /cart/, /checkout/, etc.)
│   ├── serializers.py               # DRF serializers for Products, Cart, Orders
│   ├── tests.py                     # Complete test suite (32 unit & integration tests)
│   ├── urls.py                      # /api/ REST endpoints
│   └── views.py                     # Catalog, Cart, Order, and Dashboard views
├── static/
│   ├── css/
│   │   └── style.css                # Mobile-first CSS stylesheet
│   └── js/
│       ├── api.js                   # Unified fetch client with CSRF & Toasts
│       ├── auth.js                  # Login & Registration client validation
│       ├── products.js              # Live search, category tabs, and detail loader
│       ├── cart.js                  # Persistent cart management & navbar counter
│       ├── orders.js                # Checkout processing & order history
│       └── dashboard.js             # Admin & Seller dashboard metrics and modals
├── templates/
│   ├── base.html                    # Common layout, sticky nav, mobile drawer, footer
│   ├── index.html                   # Product catalog, hero banner, filters, live search
│   ├── product_detail.html          # Product image, stock check, quantity selector
│   ├── cart.html                    # Shopping cart table & order summary
│   ├── checkout.html                # Delivery address form & order confirmation
│   ├── orders.html                  # Customer order tracking & history
│   ├── login.html                   # Login form with 1-click test credentials
│   ├── register.html                # Buyer / Seller registration form
│   ├── admin_dashboard.html         # Admin platform metrics & order control
│   └── seller_dashboard.html        # Seller analytics, card CRUD & order fulfillment
└── media/
    └── products/                    # User & seller uploaded card photography
```

---

## 🚀 Step-by-Step Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Seed Demo Data (Admin, Sellers, Buyer, Categories & Products)
```bash
python manage.py seed_data
```

### 4. Run the Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your web browser.

---

## 🔑 Pre-Configured Test Accounts

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Platform oversight, all orders, products, users & `/admin/` |
| **Seller** | `seller_john` | `seller123` | Card inventory management, sales metrics, order fulfillment |
| **Seller** | `seller_alice`| `seller123` | Artisan catalog management, order fulfillment |
| **Buyer** | `buyer_bob` | `buyer123` | Browsing cards, cart, checkout, order history |

*(Tip: The Login page at `/login/` contains **1-Click Test Chips** to instantly autofill any of these test credentials!)*

---

## 🔌 API Endpoint Reference

### Authentication (`/api/auth/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/auth/csrf/` | Retrieve CSRF token cookie | No |
| `POST` | `/api/auth/register/` | Register as Buyer or Seller | No |
| `POST` | `/api/auth/login/` | Sign in & establish session | No |
| `POST` | `/api/auth/logout/` | Sign out current session | Yes |
| `GET` | `/api/auth/me/` | Current user profile & role | No (returns state) |

### Products & Categories (`/api/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/categories/` | List all categories with product counts | No |
| `GET` | `/api/products/` | Filter, search, and sort products | No |
| `POST` | `/api/products/` | Create a new greeting card | Yes (Seller / Admin) |
| `GET` | `/api/products/<id>/` | View individual card details | No |
| `PUT` | `/api/products/<id>/` | Update card details | Yes (Owner Seller / Admin) |
| `DELETE` | `/api/products/<id>/` | Remove card from inventory | Yes (Owner Seller / Admin) |
| `GET` | `/api/seller/products/`| List all cards published by current seller | Yes (Seller / Admin) |

### Shopping Cart (`/api/cart/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/cart/` | Retrieve authenticated user's cart | Yes |
| `POST` | `/api/cart/items/` | Add card to cart (with stock limit validation) | Yes |
| `PATCH` | `/api/cart/items/<id>/`| Update quantity of card in cart | Yes |
| `DELETE` | `/api/cart/items/<id>/`| Remove item from cart | Yes |
| `DELETE` | `/api/cart/clear/` | Clear all items from cart | Yes |

### Orders & Checkout (`/api/orders/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/orders/checkout/`| Place order: atomic stock deduction & cart clearance | Yes |
| `GET` | `/api/orders/` | List customer's orders (or all orders for Admin) | Yes |
| `GET` | `/api/orders/<id>/` | Detailed order info | Yes (Buyer / Item Seller / Admin) |
| `PATCH` | `/api/orders/<id>/status/`| Update fulfillment status (`Shipped`, `Delivered`, `Cancelled`) | Yes (Seller / Admin) |

### Dashboards (`/api/dashboard/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/dashboard/admin/` | Platform revenue, orders, products, users stats | Yes (Admin) |
| `GET` | `/api/dashboard/seller/`| Seller earnings, units sold, orders, and products | Yes (Seller) |

---

## 🧪 Automated Tests

The application includes 32 automated unit and integration tests covering user roles, authentication, catalog filters, stock management, cart transactions, atomic checkout, seller isolation, and dashboard metrics.

To execute the test suite:
```bash
python manage.py test
```
All 32 tests will run and pass cleanly.

