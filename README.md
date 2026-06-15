# 🏔️ Extreme Adventure — Travel Booking Platform

A full-stack travel booking web application for **Extreme Adventure** (Est. 2009, Bhopal), offering curated travel packages across 120+ destinations in India.

---

## 🚀 Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 + Vite | UI framework & build tool |
| Tailwind CSS | Styling |
| Zustand | Global state management |
| React Router v6 | Client-side routing |
| Axios | HTTP requests |
| react-icons | Icon library |

### Backend
| Technology | Purpose |
|---|---|
| Flask | Python web framework |
| SQLAlchemy | ORM |
| PostgreSQL | Primary database |
| Flask-JWT-Extended | JWT authentication |
| Flask-Limiter | Rate limiting |
| Cloudinary | Image storage |
| psycopg2 | PostgreSQL adapter |

---

## 📁 Project Structure

```
extreme-adventure/
│
├── frontend/                  # React + Vite app
│   ├── public/
│   ├── src/
│   │   ├── admin/             # Admin dashboard pages
│   │   │   ├── pages/
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── Package.jsx
│   │   │   │   ├── PackageCollection.jsx
│   │   │   │   ├── PackageCollectionDetail.jsx
│   │   │   │   ├── PackageFormPage.jsx
│   │   │   │   └── Country.jsx
│   │   │   └── store/
│   │   │       ├── packageStore.js
│   │   │       ├── packageCollectionStore.js
│   │   │       ├── countryStore.js
│   │   │       ├── bannerStore.js
│   │   │       ├── dashboardStore.js
│   │   │       ├── formStore.js
│   │   │       └── profileStore.js
│   │   ├── components/        # Shared user-facing components
│   │   │   ├── NavBar.jsx
│   │   │   ├── Carousel.jsx
│   │   │   ├── Collections.jsx
│   │   │   ├── Package.jsx
│   │   │   ├── BestCountries.jsx
│   │   │   ├── Country.jsx
│   │   │   ├── Deals.jsx
│   │   │   ├── WhyChooseUs.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── TravelAssistant.jsx   # AI chat widget (Aria)
│   │   ├── pages/             # User-facing pages
│   │   │   ├── About.jsx
│   │   │   ├── Contact.jsx
│   │   │   ├── Review.jsx
│   │   │   ├── Packages.jsx
│   │   │   ├── PackageDetail.jsx
│   │   │   ├── CountryDetail.jsx
│   │   │   └── CollectionDetail.jsx
│   │   ├── store/
│   │   │   └── userStore.js
│   │   ├── AuthPage.jsx
│   │   ├── ProtectedRoute.jsx
│   │   ├── api.js
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── backend/                   # Flask app
    ├── models.py              # SQLAlchemy models
    ├── app.py                 # Flask app entry point
    ├── config/
    │   ├── extension.py       # db, limiter init
    │   └── middleware.py      # JWT auth middleware
    ├── routes/
    │   ├── admin_routes.py    # All admin CRUD routes
    │   └── user_routes.py     # All public user routes
    ├── migrations/            # Alembic migrations
    ├── requirements.txt
    └── .env
```

---

## 🗃️ Database Schema

```
Country
  └── PackageCollection (many)    ← country_id FK
        └── Package (many-to-many) ← package_collection_association
              ├── PackageDays (many)
              │     ├── Activities (many)
              │     └── DaysDescription (many)
              ├── Review (many)
              └── Form/Enquiry (many)

Admin               ← separate auth table
Banner              ← carousel images
```

**Key design decision:** `Package ↔ PackageCollection` is a **many-to-many** relationship via `package_collection_association` junction table. A package must belong to at least one collection.

---

## ⚙️ Environment Setup

### Backend `.env`
```env
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=postgresql://user:password@localhost:5432/extreme_adventure
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Frontend `src/api.js`
```js
export const API = 'http://localhost:5000'   // development
// export const API = 'https://your-api.com'  // production
```

---

## 🛠️ Installation & Running

### Backend

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up database
flask db init
flask db migrate -m "initial"
flask db upgrade

# 4. Run the server
flask run
# or
python app.py
```

### Frontend

```bash
# 1. Install dependencies
npm install

# 2. Run development server
npm run dev

# 3. Build for production
npm run build
```

---

## 🔐 Authentication

- Admin authentication uses **JWT tokens** stored in `localStorage`
- Token is sent via `Authorization: Bearer <token>` header on every protected request
- Token expiry: **7 days**
- On login: token saved to `localStorage` + set as `axios.defaults.headers.common['Authorization']`
- On logout: token removed from `localStorage` + axios header deleted
- `ProtectedRoute` component validates token on every protected page load

---

## 📡 API Overview

### User Routes (Public) — `/user`
| Method | Endpoint | Description |
|---|---|---|
| GET | `/user/home` | Home collections with packages |
| GET | `/user/banners` | Carousel banners |
| GET | `/user/countries` | All countries |
| GET | `/user/countries/:id` | Country with collections |
| GET | `/user/collections` | All collections |
| GET | `/user/collections/:id` | Collection with packages |
| GET | `/user/packages` | All packages (filter/sort/paginate) |
| GET | `/user/packages/:id` | Package detail |
| GET | `/user/packages/:id/suggested` | Suggested packages |
| GET | `/user/packages/:id/reviews` | Package reviews |
| POST | `/user/packages/:id/enquiry` | Submit enquiry |
| POST | `/user/packages/:id/review` | Submit review |

### Admin Routes (Protected) — `/admin`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/admin/login` | Admin login |
| GET | `/admin/dashboard` | Dashboard stats |
| CRUD | `/admin/country` | Country management |
| CRUD | `/admin/package-collection` | Collection management |
| PUT | `/admin/package-collection/:id` | Add/remove packages |
| CRUD | `/admin/package` | Package management |
| GET/DELETE | `/admin/enquiries` | Enquiry management |
| GET/DELETE | `/admin/reviews` | Review management |
| CRUD | `/admin/banner` | Banner management |

---

## 🚦 Rate Limiting

```python
# Applied to all routes
default_limits = ["500 per day", "100 per hour"]

# Admin routes (stricter)
limiter.limit("100 per day;30 per hour")(adminBP)
```

---

## 🖼️ Image Management

All images are uploaded to **Cloudinary** and stored as URLs in the database.

| Resource | Cloudinary Folder |
|---|---|
| Country images | `countries/` |
| Collection images | `package-collections/` |
| Package images | `packages/` |
| Banner images | `banners/` |

Package images are stored as a **JSON array** of `{url, public_id}` objects, supporting multiple images per package.

---

## 🤖 AI Chat Widget (Aria)

A frontend-only travel assistant built without any AI API:

- **Keyword intent matching** across 14+ travel intents
- Covers: destinations, pricing, booking, cancellation, reviews, company info
- Quick chip shortcuts for common queries
- Typing indicator animation
- Navigate-to-page action buttons on each response
- Floating button with ping animation, bottom-right corner
- Zero backend dependency

---

## 📱 Key Features

### User-Facing
- 🏠 Dynamic home page with curated collections
- 🔍 Package search with filters (price, country, sort)
- 📦 Package detail with itinerary, inclusions, reviews
- 🌍 Browse by country and collection
- ⭐ Submit and read reviews
- 📋 Enquiry form with package snapshot
- 🤖 Aria — AI travel assistant widget
- 📱 Fully responsive (mobile + desktop)

### Admin Panel
- 📊 Dashboard with top packages, countries, enquiries stats
- 🗺️ Country + collection CRUD with image upload
- 📦 Package CRUD with rich text editor, multi-image upload, day builder
- 🔗 Many-to-many package-collection assignment
- 🖼️ Banner management (max 4)
- 📋 Enquiry & review management
- 🔒 JWT-protected routes

---

## 🚀 Deployment

### Backend (Render / Railway / VPS)
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app:app --workers 4 --bind 0.0.0.0:5000
```

### Frontend (Vercel / Netlify)
```bash
npm run build
# Upload /dist folder or connect repo to Vercel
```

### Environment variables
Set all `.env` values in your hosting platform's environment settings.

---

## 📄 License

This project is proprietary software developed by **Aditya Sharma**

---

*Built with ❤️ in Bhilai, Chhattisgarh*
