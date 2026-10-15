# FarmDirect AI — Fresh from the Farm. Fair for Everyone.

[![Python](https://img.shields.io/badge/Python-3.12-2d6a4f.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-40916c.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-52b788.svg)](https://www.sqlalchemy.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-74c69d.svg)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/Automated_Tests-14_Passed_100%25-brightgreen.svg)]()

> **24-Hour College Hackathon MVP**: Direct Peer-to-Peer Agricultural Marketplace with AI-assisted Fair Price Estimation, Multi-Criteria Farmer-Buyer Matching, Atomic Inventory Management, and Surplus Rescue Food-Waste Prevention.

---

## 1. Executive Summary & Problem Statement

In conventional Indian agricultural supply chains, fresh produce passes through 4 to 6 intermediary tiers (village aggregators, APMC mandi commission agents, regional wholesalers, sub-distributors, and local cart vendors). 

This fragmented structure creates major economic and environmental crises:
1. **Severe Farmer Income Erosion**: Farmers often receive **less than 30–35%** of the final consumer price.
2. **High Procuring Costs**: Commercial food businesses (restaurants, cloud kitchens, grocery retailers) pay inflated margins.
3. **Massive Post-Harvest Spoilage**: Transport holding delays and lack of demand forecasting cause over 25% of fresh produce to spoil before reaching kitchens.

### The FarmDirect AI Solution
FarmDirect AI directly connects verified farmers with restaurants, retailers, wholesalers, and consumers with:
- **Zero Intermediary Commissions**: 100% of the sale realization goes straight to the farmer.
- **AI Feature 1: Fair Price Assistant**: Multi-factor price estimation combining mandi reference baselines, harvest freshness age, bulk volume scales, and regional corridors.
- **AI Feature 2: Smart Farmer-Buyer Matching**: Ranks produce lots matching buyer volume scale, district proximity, and culinary freshness requirements with transparent explanations.
- **AI Feature 3: Surplus Rescue**: Detects inventory approaching shelf-life limits and suggests farmer-controlled discounts (15–30%) on the *Surplus Deals* channel to prevent avoidable food waste.
- **Atomic Inventory & Order Pipeline**: Prevents overselling, manages multi-step fulfillment (Pending &rarr; Accepted &rarr; Ready for Dispatch &rarr; Completed), and restores stock upon cancellation.

---

## 2. Technology Stack

- **Backend**: Python 3.12, Flask 3.1.
- **Database & ORM**: SQLite 3 with SQLAlchemy ORM (`Flask-SQLAlchemy`).
- **Frontend**: Responsive HTML5, Custom CSS3 Design System (Deep Forest Green, Warm Cream, Harvest Yellow), Bootstrap 5.3.3, Bootstrap Icons 1.11.3.
- **Interactive Visualizations**: Chart.js 4.4.x for farmer inventory distribution and market analytics.
- **AI / Heuristic Engine**: Pure Python modules for explainable pricing, multi-attribute compatibility scoring, and freshness decay modeling.
- **Security & Authentication**:
  - Session-based authentication with cryptographically hashed passwords via Werkzeug (`generate_password_hash` / `check_password_hash`).
  - Server-side Role-Based Access Control (`@login_required`, `@role_required`).
  - Session CSRF token validation on all state-modifying POST requests (`X-CSRF-Token` & form tokens).
  - Parameterized database operations through SQLAlchemy preventing SQL injection.
  - Safe file upload handling (`secure_filename`, extension whitelist).

---

## 3. Project Directory Structure

```text
niat555/
├── app.py                     # Main Flask application, routes, CSRF middleware & error handlers
├── config.py                  # Environment-driven configuration and paths
├── models.py                  # SQLAlchemy models: User, Product, Order, OrderItem, Notification, PriceReference, Report
├── seed.py                    # Database seed script with rich Indian agricultural demo data
├── requirements.txt           # Python dependency specifications
├── .env                       # Development environment variables
├── .env.example               # Environment template
├── README.md                  # Comprehensive setup, demo guide & test report
│
├── services/                  # AI and Business Logic Engines
│   ├── __init__.py
│   ├── pricing_service.py     # AI Fair Price Assistant (mandi baselines, freshness, bulk scaling)
│   ├── matching_service.py    # Smart Farmer-Buyer Matching Engine (scores & explanations)
│   └── surplus_service.py     # Surplus Rescue & Food Waste Prevention Service
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Core layout, responsive navigation, flash alerts & footer
│   ├── index.html             # Homepage: Hero, live stats counter, categories, surplus deals
│   ├── login.html             # Login form with 1-Click Hackathon Demo Buttons
│   ├── register.html          # Role-based registration (Farmer vs Restaurant/Retailer/Wholesaler)
│   ├── marketplace.html       # Full catalogue with live search, multi-filters & AI recommendations
│   ├── product_detail.html    # Product page with AI price breakdown & direct ordering form
│   ├── farmer_dashboard.html  # Farmer portal: KPIs, Chart.js stock analytics, surplus alerts
│   ├── buyer_dashboard.html   # Buyer portal: Active tracking timeline, spend KPIs, recommendations
│   ├── admin_dashboard.html   # Protected admin portal: User directory, moderation, reports queue
│   ├── add_product.html       # Add listing form with instant AI Fair Price preview button
│   ├── edit_product.html      # Edit listing, update inventory & surplus discount toggle
│   ├── orders.html            # Orders management table with status filtering
│   ├── ai_insights.html       # Dedicated AI Hub with interactive pricing & matching simulators
│   ├── notifications.html     # Real-time activity notifications feed
│   ├── profile.html           # User profile & credentials manager
│   ├── how_it_works.html      # Process explanation & middleman problem breakdown
│   ├── about.html             # Mission & agricultural impact philosophy
│   ├── faq.html               # Frequently asked questions
│   ├── terms.html             # Terms of direct trade
│   ├── privacy.html           # Privacy and data handling policy
│   └── error.html             # Custom 400, 403, 404, 500 error display
│
├── static/                    # Static Assets
│   ├── css/
│   │   └── style.css          # Professional agricultural CSS design system
│   ├── js/
│   │   └── main.js            # Dynamic price calculators, AJAX CSRF, tooltips, demo login autofill
│   ├── images/                # Brand logo & SVG category graphics (vegetables, fruits, grains, etc.)
│   └── uploads/               # User-uploaded agricultural produce photos
│
└── tests/                     # Automated Test Suite
    ├── __init__.py
    └── test_app.py            # 14 comprehensive unit & integration tests
```

---

## 4. Quickstart Setup Guide (Windows / PowerShell)

### Step 1: Open Terminal in Project Directory
```powershell
cd c:\Users\chara\OneDrive\Desktop\niat555
```

### Step 2: (Optional) Create & Activate Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Seed Database with Indian Agricultural Demo Data
Populates the database with realistic farmers, buyers, admins, active produce listings (tomatoes, onions, potatoes, mangoes, basmati rice, chillies, etc.), Agmarknet baseline benchmarks, and sample orders:
```powershell
python seed.py
```
*Output:*
```text
=== Database Seed Completed Successfully! ===
Users created: 9
Products created: 10
Orders created: 3
Benchmark price references: 12
```

### Step 5: Start the Application
```powershell
python app.py
```
Open your browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 5. Pre-Seeded Hackathon Demo Credentials

For rapid presentation during the hackathon, the login page (`/login`) includes **1-Click Quick Demo Login Buttons** to log in as any role without manual typing.

| Role | Name & Entity | Email Address | Password | Use Case / Specialty |
| :--- | :--- | :--- | :--- | :--- |
| **Farmer** | Rameshwar Patel | `farmer.ramesh@farmdirect.demo` | `Password@123` | Nashik Organic Vegetable Farm (Tomatoes, Onions, Chillies) |
| **Farmer** | Sardar Balvinder Singh | `farmer.balvinder@farmdirect.demo` | `Password@123` | Punjab Grain Farmer (1121 Basmati Rice, Sharbati Wheat) |
| **Farmer** | Suresh Kumar Gowda | `farmer.suresh@farmdirect.demo` | `Password@123` | Mandya Horticulture Farmer (GI Yelakki Bananas) |
| **Buyer (Restaurant)** | Chef Vikram (Spice Kitchen) | `spicekitchen@demo.com` | `Password@123` | Pune fine-dining restaurant requiring fresh morning harvests |
| **Buyer (Wholesaler)** | AgroMega Wholesale Hub | `agromega@demo.com` | `Password@123` | APMC Navi Mumbai wholesale trader procuring bulk consignments |
| **Buyer (Retailer)** | Daily Fresh Supermarket | `dailyfresh@demo.com` | `Password@123` | Bengaluru grocery store procuring shelf-stable lots |
| **Buyer (Consumer)** | Anita Sharma | `anita.consumer@demo.com` | `Password@123` | Individual household consumer |
| **Platform Admin** | System Administrator | `admin@farmdirect.ai` | `Password@123` | Platform oversight, moderation, reports, and GMV audit |

---

## 6. Official 10-Step Hackathon Live Demonstration Script

Follow this script to deliver an end-to-end demonstration for hackathon judges:

1. **Homepage & Problem Statement (`/`)**:
   - Open [http://127.0.0.1:5000](http://127.0.0.1:5000).
   - Point out the hero headline: *"From Our Farms to Your Business. Directly."*
   - Highlight the **Live Impact Stats** calculated directly from the database (farmers, active listings, kilograms traded).
   - Explain the middleman breakdown: eliminating 4-6 intermediaries so farmers earn 35% more while restaurants save 20%.

2. **Farmer Experience (`/login` &rarr; Click "Farmer Ramesh")**:
   - Click the 1-Click login button for **Farmer Ramesh**.
   - Review the **Farmer Dashboard**: KPIs (Active listings, Realized earnings, Inventory stock), Chart.js portfolio breakdown, and incoming orders.

3. **List New Produce with AI Fair Price Assistant (`/farmer/product/add`)**:
   - Click **List New Harvest**.
   - Enter `Vine-Ripened Round Tomatoes`, Category `Vegetables`, Quantity `100`, Unit `kg`.
   - Click **Get AI Fair Price Recommendation**.
   - Show the judge the transparent factor breakdown (Base mandi reference, Freshness factor, Volume scale, Regional hub differential) and 90% confidence score.
   - Click **Apply ₹28.84 to Price Field** and publish the listing.

4. **Buyer Experience (`/login` &rarr; Click "Restaurant Buyer")**:
   - Switch to **Chef Vikram (Spice Kitchen)**.
   - Note the personalized **"Recommended for Your Restaurant Needs"** section, which uses the AI matching engine to rank lots by proximity (Pune/Nashik corridor) and recent harvest freshness.

5. **Search & Filter the Marketplace (`/marketplace`)**:
   - Search for `Tomatoes` or filter by `Vegetables`.
   - Show the newly listed lot alongside existing listings, complete with harvest date badges, price per unit in ₹, and stock counts.

6. **Place a Direct Order (`/product/<id>`)**:
   - Open the tomatoes listing.
   - Point out the dynamic order total calculator (adjust quantity from 10 kg to 25 kg &rarr; live total calculates instantly).
   - Enter delivery address (`Spice Kitchen Gate 2, Koregaon Park, Pune`) and submit the order.
   - Point out the atomic inventory deduction (stock immediately drops by 25 kg, preventing any overselling).

7. **Farmer Order Fulfillment (`/farmer/dashboard`)**:
   - Switch back to **Farmer Ramesh**.
   - Notice the in-app notification bell badge counter increased.
   - Under *Recent Incoming Orders*, find Chef Vikram's order and click **Manage &rarr; Accept Order**.
   - Then advance it to **Ready for Dispatch**.

8. **Buyer Tracking Timeline (`/buyer/dashboard`)**:
   - Return to Chef Vikram's dashboard.
   - Show the live tracking status pill updated to `Ready for Dispatch`, with direct farmer phone contact visible.

9. **AI Surplus Rescue Demonstration (`/farmer/dashboard` &amp; `/marketplace?surplus=1`)**:
   - Show the **AI Surplus Stock Risk Alert** banner on Farmer Ramesh's dashboard.
   - Point out the Spinach clearance lot flagged due to approaching shelf-life limits.
   - Click **Apply 25% Surplus Deal** &rarr; the listing immediately receives a red `25% OFF` badge and appears on the homepage and `/marketplace?surplus=1` for rapid clearance.

10. **Admin Moderation & GMV Audit (`/admin`)**:
    - Log in as `admin@farmdirect.ai`.
    - View platform-wide statistics, total GMV traded, user directory, and listings moderation table.
    - Demonstrate toggling a listing's status to suspend or reactivate inappropriate items.

---

## 7. Automated Testing Results

The application includes 14 comprehensive automated unit and integration tests executing under `pytest`:

```powershell
pytest tests/test_app.py -v
```

### Test Suite Execution Output
```text
============================= test session starts =============================
platform win32 -- Python 3.12.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\chara\OneDrive\Desktop\niat555
collected 14 items

tests/test_app.py::FarmDirectTestCase::test_ai_fair_price_assistant_service PASSED [  7%]
tests/test_app.py::FarmDirectTestCase::test_csrf_token_enforcement PASSED          [ 14%]
tests/test_app.py::FarmDirectTestCase::test_insufficient_stock_rejection PASSED     [ 21%]
tests/test_app.py::FarmDirectTestCase::test_order_cancellation_restores_stock PASSED [ 28%]
tests/test_app.py::FarmDirectTestCase::test_order_total_with_surplus_discount PASSED [ 35%]
tests/test_app.py::FarmDirectTestCase::test_password_hashing PASSED               [ 42%]
tests/test_app.py::FarmDirectTestCase::test_product_creation_and_editing PASSED   [ 50%]
tests/test_app.py::FarmDirectTestCase::test_product_search_and_filtering PASSED   [ 57%]
tests/test_app.py::FarmDirectTestCase::test_role_based_access PASSED              [ 64%]
tests/test_app.py::FarmDirectTestCase::test_smart_buyer_matching_engine PASSED    [ 71%]
tests/test_app.py::FarmDirectTestCase::test_successful_order_placement PASSED     [ 78%]
tests/test_app.py::FarmDirectTestCase::test_surplus_rescue_service PASSED         [ 85%]
tests/test_app.py::FarmDirectTestCase::test_user_registration_and_login PASSED    [ 92%]
tests/test_app.py::FarmDirectTestCase::test_valid_and_invalid_order_status_transitions PASSED [100%]

============================= 14 passed in 18.62s =============================
```

All 14 tests pass with **100% success rate**.

---

## 8. AI / ML Implementation Details

### Transparent Heuristics over Black-Box Fakes
In keeping with hackathon integrity guidelines, FarmDirect AI does not make fake external API claims:
1. **Price Reference Data**: The `PriceReference` model stores demo mandi benchmarks (Agmarknet simulation) for commodities across Indian agricultural districts.
2. **Multi-Factor Price Estimation**:
   $$\text{Price}_{\text{unit}} = \text{Base}_{\text{commodity}} \times \text{UnitMultiplier} \times (1.0 + F_{\text{freshness}} + F_{\text{volume}} + F_{\text{region}})$$
   - Ultra-fresh harvest within 24–48h: $+8\%$ quality premium.
   - Bulk commercial batch ($\ge 1,000\text{ kg}$): $-10\%$ wholesale scaling.
   - High-demand metro corridor: $+6\%$ regional adjustment.
3. **Smart Matching Score (0–100%)**:
   - Product relevance keyword/category match: 30 pts.
   - Batch sufficiency & lot capacity: 25 pts.
   - Geographic district proximity: 20 pts.
   - Persona suitability (Restaurant vs Wholesaler vs Retailer vs Consumer): 15 pts.
   - Price competitiveness vs budget: 10 pts.
4. **Surplus Risk Detection**:
   - Evaluates remaining shelf life $(\text{freshness\_date} - \text{today})$.
   - Flags urgency as Low, Medium, or High.
   - Suggests advisory 15–35% clearance discounts. The farmer retains 100% control to accept, alter, or ignore suggestions.

---

## 9. Security & Data Protection Highlights

- **Password Security**: Zero plaintext passwords. All credentials are stored with `generate_password_hash` (PBKDF2/SHA-256).
- **CSRF Defense**: Session CSRF token validation on all state-modifying POST requests (`X-CSRF-Token` & form tokens).
- **Session Protection**: `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"`.
- **Role Isolation**: Server-side role checks with `@login_required` and `@role_required` decorators ensure buyers cannot tamper with farmer stock or order statuses, and non-admins cannot access moderation controls.
- **Atomic Operations**: Database stock deductions and cancellations use safe SQLAlchemy transactions, preventing overselling or ghost inventory.

---

## 10. Limitations & Future Roadmap

- **MVP Scope**: Settlement is simulated as Cash on Delivery (COD) / Direct Settlement upon produce inspection. Future iterations will integrate UPI escrow smart contracts.
- **Logistics**: The platform facilitates direct farmer-buyer dispatch and contact. Future phases can integrate community truck pooling and rural aggregator drop points.
- **Live Mandi API**: The current reference dataset uses 12 demo district baselines. In production, this can connect directly to real-time e-NAM / Agmarknet government APIs.

---

**FarmDirect AI** &bull; *Fresh from the Farm. Fair for Everyone.*
