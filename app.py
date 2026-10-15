import os
import secrets
from datetime import datetime, date, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, abort, jsonify, g
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Product, Order, OrderItem, Notification, PriceReference, Report
from services.pricing_service import estimate_fair_price
from services.matching_service import rank_products_for_buyer, calculate_match_score
from services.surplus_service import analyze_surplus_risk, get_farmer_surplus_alerts

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

# Ensure folders exist
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


# ==========================================
# CSRF & SECURITY HELPERS
# ==========================================

def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]

@app.before_request
def check_csrf():
    if app.config.get("TESTING"):
        return
    # Enforce CSRF validation for state-modifying requests
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        # Exclude safe API endpoints if needed, but validate tokens in forms and headers
        token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        session_token = session.get("csrf_token")
        if not session_token or not token or token != session_token:
            # If AJAX, return JSON error; otherwise flash error
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({"error": "Invalid or missing CSRF token"}), 400
            flash("Session expired or invalid security token. Please try again.", "danger")
            return redirect(request.referrer or url_for("index"))

@app.context_processor
def inject_global_context():
    current_user = None
    unread_notifications_count = 0
    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])
        if current_user:
            unread_notifications_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
            
    return {
        "current_user": current_user,
        "unread_notifications_count": unread_notifications_count,
        "csrf_token": generate_csrf_token,
        "now": datetime.now(timezone.utc)
    }


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        user = db.session.get(User, session["user_id"])
        if not user or not user.is_active:
            session.clear()
            flash("Your account has been deactivated or not found. Please log in again.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("login", next=request.url))
            user = db.session.get(User, session["user_id"])
            if not user or user.role not in allowed_roles:
                flash("Access denied. You do not have permissions for this page.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route("/")
def index():
    # Impact statistics from real application database
    total_farmers = User.query.filter_by(role="farmer", is_active=True).count()
    total_products = Product.query.filter_by(is_available=True).count()
    completed_orders = Order.query.filter_by(status="Completed").count()
    
    # Calculate total weight traded (kg)
    completed_items = OrderItem.query.join(Order).filter(Order.status == "Completed").all()
    total_kg_traded = sum(
        item.quantity * (100 if item.product.unit == "quintal" else 1000 if item.product.unit == "tonne" else 1)
        for item in completed_items if item.product
    )

    # Featured farmer listings
    featured_products = (
        Product.query.filter_by(is_available=True)
        .order_by(Product.created_at.desc())
        .limit(6)
        .all()
    )

    # Surplus Rescue Deals
    surplus_deals = (
        Product.query.filter_by(is_available=True, is_surplus=True)
        .order_by(Product.discount_percentage.desc())
        .limit(4)
        .all()
    )

    categories = [
        {"name": "Vegetables", "icon": "bi-egg-fried", "img": "vegetables.svg", "desc": "Tomatoes, Onions, Potatoes, Greens"},
        {"name": "Fruits", "icon": "bi-apple", "img": "fruits.svg", "desc": "Mangoes, Bananas, Apples, Papayas"},
        {"name": "Grains", "icon": "bi-flower1", "img": "grains.svg", "desc": "Basmati Rice, Wheat, Millets, Oats"},
        {"name": "Pulses", "icon": "bi-basket2", "img": "pulses.svg", "desc": "Toor Dal, Moong Dal, Chickpeas"},
        {"name": "Spices", "icon": "bi-fire", "img": "spices.svg", "desc": "Turmeric, Chillies, Cumin, Mustard"},
        {"name": "Dairy & Honey", "icon": "bi-cup-hot", "img": "dairy.svg", "desc": "Organic Honey, Pure Ghee, Paneer"}
    ]

    return render_template(
        "index.html",
        total_farmers=total_farmers,
        total_products=total_products,
        completed_orders=completed_orders,
        total_kg_traded=round(total_kg_traded, 1),
        featured_products=featured_products,
        surplus_deals=surplus_deals,
        categories=categories
    )


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "buyer").strip().lower()
        phone = request.form.get("phone", "").strip()
        village = request.form.get("village", "").strip()
        district = request.form.get("district", "").strip()
        business_type = request.form.get("business_type", "").strip()
        farm_details = request.form.get("farm_details", "").strip()

        # Validation
        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("register.html", form_data=request.form)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", form_data=request.form)

        if role not in ["farmer", "buyer"]:
            role = "buyer"

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        user = User(
            name=name,
            email=email,
            role=role,
            phone=phone,
            village=village,
            district=district,
            business_type=business_type,
            farm_details=farm_details if role == "farmer" else None
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Create welcome notification
        welcome_msg = (
            f"Welcome to FarmDirect AI, {name}! Your {role.title()} account is active. "
            "Explore direct agricultural trade with zero middleman commissions."
        )
        notif = Notification(user_id=user.id, message=welcome_msg)
        db.session.add(notif)
        db.session.commit()

        # Auto-login
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_role"] = user.role

        flash(f"Account created successfully! Welcome, {name}.", "success")
        if user.role == "farmer":
            return redirect(url_for("farmer_dashboard"))
        return redirect(url_for("marketplace"))

    return render_template("register.html", form_data={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("This account has been deactivated. Please contact support.", "danger")
                return render_template("login.html")

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role

            flash(f"Welcome back, {user.name}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)

            if user.role == "farmer":
                return redirect(url_for("farmer_dashboard"))
            elif user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("buyer_dashboard"))
        else:
            flash("Invalid email or password. Please check your credentials.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = db.session.get(User, session["user_id"])
    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip()
        user.phone = request.form.get("phone", user.phone).strip()
        user.village = request.form.get("village", user.village).strip()
        user.district = request.form.get("district", user.district).strip()
        user.business_type = request.form.get("business_type", user.business_type).strip()
        if user.is_farmer():
            user.farm_details = request.form.get("farm_details", user.farm_details).strip()

        # Optional password update
        new_pw = request.form.get("new_password", "").strip()
        if new_pw:
            if len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return render_template("profile.html", user=user)
            user.set_password(new_pw)

        db.session.commit()
        session["user_name"] = user.name
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


# ==========================================
# BUYER MARKETPLACE & CATALOG
# ==========================================

@app.route("/marketplace")
def marketplace():
    # Filtering parameters
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    district = request.args.get("district", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    min_qty = request.args.get("min_qty", type=float)
    surplus_only = request.args.get("surplus", "").lower() in ["1", "true", "yes"]
    sort_by = request.args.get("sort", "newest")

    query = Product.query.filter_by(is_available=True).filter(Product.quantity > 0)

    # Filters
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%")) |
            (Product.location.ilike(f"%{search}%"))
        )
    if category:
        query = query.filter(Product.category.ilike(category))
    if district:
        query = query.filter(Product.district.ilike(f"%{district}%"))
    if min_price is not None and min_price >= 0:
        query = query.filter(Product.price >= min_price)
    if max_price is not None and max_price > 0:
        query = query.filter(Product.price <= max_price)
    if min_qty is not None and min_qty > 0:
        query = query.filter(Product.quantity >= min_qty)
    if surplus_only:
        query = query.filter(Product.is_surplus == True)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "qty_desc":
        query = query.order_by(Product.quantity.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    products = query.all()

    # Get distinct categories and districts for dropdown filter menus
    all_categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]
    all_districts = [d[0] for d in db.session.query(Product.district).distinct().all() if d[0]]

    # If user is a logged-in buyer, compute matching recommendations
    recommendations = []
    current_user = None
    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])
        if current_user and current_user.is_buyer():
            all_active = Product.query.filter_by(is_available=True).filter(Product.quantity > 0).all()
            recommendations = rank_products_for_buyer(
                products=all_active,
                buyer=current_user,
                search_query=search if search else None,
                limit=3
            )

    return render_template(
        "marketplace.html",
        products=products,
        categories=all_categories,
        districts=all_districts,
        recommendations=recommendations,
        selected_category=category,
        selected_district=district,
        search_query=search,
        min_price=min_price,
        max_price=max_price,
        min_qty=min_qty,
        surplus_only=surplus_only,
        sort_by=sort_by
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    # Run AI Fair Price Assistant on this product
    pricing_analysis = estimate_fair_price(
        product_name=product.name,
        category=product.category,
        quantity=product.quantity,
        unit=product.unit,
        harvest_date=product.harvest_date,
        freshness_date=product.freshness_date,
        current_price=product.price,
        district=product.district,
        price_ref_model=PriceReference
    )

    # Surplus evaluation
    surplus_analysis = analyze_surplus_risk(product)

    # Buyer matching score if buyer is viewing
    buyer_match = None
    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])
        if current_user and current_user.is_buyer():
            buyer_match = calculate_match_score(product, current_user)

    # Similar products in category
    similar_products = (
        Product.query.filter(Product.category == product.category, Product.id != product.id, Product.is_available == True)
        .limit(3)
        .all()
    )

    return render_template(
        "product_detail.html",
        product=product,
        pricing_analysis=pricing_analysis,
        surplus_analysis=surplus_analysis,
        buyer_match=buyer_match,
        similar_products=similar_products
    )


@app.route("/product/<int:product_id>/report", methods=["POST"])
@login_required
def report_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("Please provide a reason for the report.", "warning")
        return redirect(url_for("product_detail", product_id=product_id))

    report = Report(
        reporter_id=session["user_id"],
        product_id=product.id,
        reason=reason
    )
    db.session.add(report)
    db.session.commit()

    flash("Thank you. The listing has been reported to administration for safety verification.", "info")
    return redirect(url_for("product_detail", product_id=product_id))


# ==========================================
# DIRECT ORDERING SYSTEM
# ==========================================

@app.route("/order/create", methods=["POST"])
@login_required
def create_order():
    user = db.session.get(User, session["user_id"])
    if not user.is_buyer() and not user.is_admin():
        flash("Only registered buyers (or admins) can place direct orders.", "danger")
        return redirect(url_for("marketplace"))

    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=float)
    delivery_details = request.form.get("delivery_details", "").strip()
    notes = request.form.get("notes", "").strip()

    if not product_id or not quantity or quantity <= 0:
        flash("Invalid product or order quantity. Must be a positive number.", "danger")
        return redirect(request.referrer or url_for("marketplace"))

    if not delivery_details:
        flash("Please specify a delivery address or pickup arrangement.", "warning")
        return redirect(url_for("product_detail", product_id=product_id))

    # Safe inventory check with database transaction
    product = db.session.get(Product, product_id)
    if not product or not product.is_available:
        flash("Sorry, this agricultural lot is no longer available.", "danger")
        return redirect(url_for("marketplace"))

    if quantity > product.quantity:
        flash(
            f"Insufficient stock! You requested {quantity} {product.unit}, "
            f"but only {product.quantity} {product.unit} is currently available.",
            "danger"
        )
        return redirect(url_for("product_detail", product_id=product_id))

    # Calculate subtotal using effective price (applying surplus discount if active)
    unit_price = product.effective_price
    subtotal = round(unit_price * quantity, 2)
    total_amount = subtotal

    # Atomic inventory deduction
    product.quantity = round(product.quantity - quantity, 2)
    if product.quantity <= 0:
        product.quantity = 0.0
        product.is_available = False

    # Create Order
    order = Order(
        buyer_id=user.id,
        total_amount=total_amount,
        status="Pending",
        delivery_address_or_pickup_details=delivery_details,
        payment_method="Cash on Delivery / Direct Settlement",
        notes=notes
    )
    db.session.add(order)
    db.session.flush()  # generates order.id

    # Create OrderItem
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        farmer_id=product.farmer_id,
        quantity=quantity,
        unit_price=unit_price,
        subtotal=subtotal
    )
    db.session.add(item)

    # In-App Notification for Farmer
    farmer_msg = (
        f"New Order #{order.id}: {user.name} ({user.business_type.title() if user.business_type else 'Buyer'}) "
        f"ordered {quantity} {product.unit} of {product.name} for ₹{total_amount:.2f}."
    )
    notif_farmer = Notification(
        user_id=product.farmer_id,
        message=farmer_msg,
        related_order_id=order.id
    )
    db.session.add(notif_farmer)

    # In-App Notification for Buyer
    buyer_msg = (
        f"Order #{order.id} placed successfully for {quantity} {product.unit} of {product.name}. "
        f"Farmer {product.farmer.name} has been notified to review and fulfill your order."
    )
    notif_buyer = Notification(
        user_id=user.id,
        message=buyer_msg,
        related_order_id=order.id
    )
    db.session.add(notif_buyer)

    db.session.commit()

    flash(
        f"Order #{order.id} successfully placed! Total: ₹{total_amount:.2f}. "
        f"The farmer has received your direct order.",
        "success"
    )
    return redirect(url_for("buyer_dashboard"))


@app.route("/buyer/orders")
@login_required
def buyer_orders():
    user = db.session.get(User, session["user_id"])
    status_filter = request.args.get("status")
    
    query = Order.query.filter_by(buyer_id=user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders, view_as="buyer", status_filter=status_filter)


@app.route("/buyer/order/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    # Verify authorization
    if order.buyer_id != session["user_id"] and session.get("user_role") != "admin":
        flash("You are not authorized to cancel this order.", "danger")
        return redirect(url_for("buyer_orders"))

    if not order.can_transition_to("Cancelled"):
        flash(f"Order #{order.id} cannot be cancelled in its current '{order.status}' status.", "danger")
        return redirect(url_for("buyer_orders"))

    order.status = "Cancelled"

    # Safely restore product stock
    for item in order.items:
        prod = db.session.get(Product, item.product_id)
        if prod:
            prod.quantity = round(prod.quantity + item.quantity, 2)
            prod.is_available = True
            
            # Notify farmer
            cancel_msg = f"Order #{order.id} was cancelled. {item.quantity} {prod.unit} of {prod.name} has been restored to your active inventory."
            db.session.add(Notification(user_id=prod.farmer_id, message=cancel_msg, related_order_id=order.id))

    db.session.commit()
    flash(f"Order #{order.id} has been cancelled and inventory has been restored.", "info")
    return redirect(url_for("buyer_orders"))


# ==========================================
# FARMER DASHBOARD & ACTIONS
# ==========================================

@app.route("/farmer/dashboard")
@login_required
@role_required("farmer", "admin")
def farmer_dashboard():
    farmer_id = session["user_id"]
    farmer = db.session.get(User, farmer_id)

    # Listings
    active_products = Product.query.filter_by(farmer_id=farmer_id, is_available=True).all()
    all_products = Product.query.filter_by(farmer_id=farmer_id).order_by(Product.created_at.desc()).all()
    total_listings = len(active_products)
    total_stock_kg = sum(
        p.quantity * (100 if p.unit == "quintal" else 1000 if p.unit == "tonne" else 1)
        for p in active_products
    )

    # Orders for this farmer's products
    farmer_order_items = (
        OrderItem.query.filter_by(farmer_id=farmer_id)
        .join(Order)
        .order_by(Order.created_at.desc())
        .all()
    )
    
    unique_orders_dict = {}
    for item in farmer_order_items:
        if item.order_id not in unique_orders_dict:
            unique_orders_dict[item.order_id] = item.order

    orders_list = list(unique_orders_dict.values())
    total_orders = len(orders_list)
    completed_orders = [o for o in orders_list if o.status == "Completed"]
    pending_orders = [o for o in orders_list if o.status == "Pending"]

    # Earnings calculation from completed and in-progress orders
    completed_earnings = sum(
        item.subtotal for item in farmer_order_items if item.order.status == "Completed"
    )
    potential_pipeline_earnings = sum(
        item.subtotal for item in farmer_order_items if item.order.status in ["Pending", "Accepted", "Ready for Dispatch"]
    )

    # AI Surplus alerts
    surplus_alerts = get_farmer_surplus_alerts(active_products)

    # AI Price suggestions for farmer's active listings
    price_suggestions = []
    for p in active_products[:5]:
        suggestion = estimate_fair_price(
            product_name=p.name,
            category=p.category,
            quantity=p.quantity,
            unit=p.unit,
            harvest_date=p.harvest_date,
            freshness_date=p.freshness_date,
            current_price=p.price,
            district=p.district,
            price_ref_model=PriceReference
        )
        price_suggestions.append({"product": p, "analysis": suggestion})

    return render_template(
        "farmer_dashboard.html",
        farmer=farmer,
        total_listings=total_listings,
        total_stock_kg=round(total_stock_kg, 1),
        total_orders=total_orders,
        completed_sales_count=len(completed_orders),
        pending_orders_count=len(pending_orders),
        completed_earnings=completed_earnings,
        potential_earnings=potential_pipeline_earnings,
        active_products=active_products,
        all_products=all_products,
        recent_orders=orders_list[:6],
        surplus_alerts=surplus_alerts,
        price_suggestions=price_suggestions
    )


@app.route("/farmer/product/add", methods=["GET", "POST"])
@login_required
@role_required("farmer", "admin")
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        quantity = request.form.get("quantity", type=float)
        unit = request.form.get("unit", "kg").strip().lower()
        price = request.form.get("price", type=float)
        location = request.form.get("location", "").strip()
        village = request.form.get("village", "").strip()
        district = request.form.get("district", "").strip()
        harvest_date_str = request.form.get("harvest_date", "").strip()
        freshness_date_str = request.form.get("freshness_date", "").strip()

        # Validation
        if not name or not category or not location:
            flash("Product name, category, and location are required.", "danger")
            return render_template("add_product.html", form_data=request.form)

        if quantity is None or quantity <= 0:
            flash("Available quantity must be a positive number.", "danger")
            return render_template("add_product.html", form_data=request.form)

        if price is None or price <= 0:
            flash("Price per unit must be a positive number in INR.", "danger")
            return render_template("add_product.html", form_data=request.form)

        harvest_date = None
        if harvest_date_str:
            try:
                harvest_date = datetime.strptime(harvest_date_str, "%Y-%m-%d").date()
                if harvest_date > date.today():
                    flash("Harvest date cannot be in the future.", "warning")
                    return render_template("add_product.html", form_data=request.form)
            except ValueError:
                flash("Invalid harvest date format. Please use YYYY-MM-DD.", "danger")
                return render_template("add_product.html", form_data=request.form)

        freshness_date = None
        if freshness_date_str:
            try:
                freshness_date = datetime.strptime(freshness_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid freshness date format.", "danger")
                return render_template("add_product.html", form_data=request.form)

        # Handle optional image upload
        image_path = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secrets.token_hex(8) + "_" + secure_filename(file.filename)
                save_dest = Config.UPLOAD_FOLDER / filename
                file.save(save_dest)
                image_path = f"uploads/{filename}"

        product = Product(
            farmer_id=session["user_id"],
            name=name,
            category=category,
            description=description,
            quantity=quantity,
            unit=unit,
            price=price,
            location=location,
            village=village,
            district=district,
            harvest_date=harvest_date,
            freshness_date=freshness_date,
            image_path=image_path,
            is_available=True
        )

        db.session.add(product)
        db.session.commit()

        flash(f"Produce listing '{product.name}' created and published to marketplace!", "success")
        return redirect(url_for("farmer_dashboard"))

    # Prefill location from farmer profile if available
    user = db.session.get(User, session["user_id"])
    default_form = {
        "location": f"{user.village or ''}, {user.district or ''}".strip(", "),
        "village": user.village or "",
        "district": user.district or ""
    }
    return render_template("add_product.html", form_data=default_form)


@app.route("/farmer/product/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("farmer", "admin")
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    # Authorization
    if product.farmer_id != session["user_id"] and session.get("user_role") != "admin":
        flash("You are not authorized to edit this listing.", "danger")
        return redirect(url_for("farmer_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        quantity = request.form.get("quantity", type=float)
        unit = request.form.get("unit", product.unit).strip().lower()
        price = request.form.get("price", type=float)
        location = request.form.get("location", "").strip()
        village = request.form.get("village", "").strip()
        district = request.form.get("district", "").strip()
        is_available = request.form.get("is_available") == "1"
        is_surplus = request.form.get("is_surplus") == "1"
        discount_percentage = request.form.get("discount_percentage", type=float) or 0.0

        if not name or not category or not location:
            flash("Name, category, and location cannot be empty.", "danger")
            return render_template("edit_product.html", product=product)

        if quantity is None or quantity < 0:
            flash("Quantity cannot be negative.", "danger")
            return render_template("edit_product.html", product=product)

        if price is None or price <= 0:
            flash("Price must be a positive number.", "danger")
            return render_template("edit_product.html", product=product)

        # Dates
        harvest_date_str = request.form.get("harvest_date", "").strip()
        if harvest_date_str:
            try:
                product.harvest_date = datetime.strptime(harvest_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        freshness_date_str = request.form.get("freshness_date", "").strip()
        if freshness_date_str:
            try:
                product.freshness_date = datetime.strptime(freshness_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Handle optional new image
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secrets.token_hex(8) + "_" + secure_filename(file.filename)
                save_dest = Config.UPLOAD_FOLDER / filename
                file.save(save_dest)
                product.image_path = f"uploads/{filename}"

        product.name = name
        product.category = category
        product.description = description
        product.quantity = quantity
        product.unit = unit
        product.price = price
        product.location = location
        product.village = village
        product.district = district
        product.is_available = is_available
        product.is_surplus = is_surplus
        product.discount_percentage = max(0.0, min(80.0, discount_percentage))

        db.session.commit()
        flash(f"Listing '{product.name}' updated successfully.", "success")
        return redirect(url_for("farmer_dashboard"))

    return render_template("edit_product.html", product=product)


@app.route("/farmer/product/<int:product_id>/toggle", methods=["POST"])
@login_required
@role_required("farmer", "admin")
def toggle_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    if product.farmer_id != session["user_id"] and session.get("user_role") != "admin":
        abort(403)

    product.is_available = not product.is_available
    db.session.commit()

    status_str = "active on the marketplace" if product.is_available else "marked as unavailable"
    flash(f"Listing '{product.name}' is now {status_str}.", "info")
    return redirect(url_for("farmer_dashboard"))


@app.route("/farmer/product/<int:product_id>/surplus", methods=["POST"])
@login_required
@role_required("farmer", "admin")
def apply_surplus_discount(product_id):
    product = db.session.get(Product, product_id)
    if not product or (product.farmer_id != session["user_id"] and session.get("user_role") != "admin"):
        abort(403)

    discount = request.form.get("discount", type=float)
    if discount and discount > 0:
        product.is_surplus = True
        product.discount_percentage = min(75.0, discount)
        flash(f"Surplus clearance deal activated for {product.name} ({product.discount_percentage:.0f}% discount)!", "success")
    else:
        product.is_surplus = False
        product.discount_percentage = 0.0
        flash(f"Surplus status removed for {product.name}.", "info")

    db.session.commit()
    return redirect(request.referrer or url_for("farmer_dashboard"))


@app.route("/farmer/orders")
@login_required
@role_required("farmer", "admin")
def farmer_orders():
    farmer_id = session["user_id"]
    status_filter = request.args.get("status")

    query = Order.query.join(OrderItem).filter(OrderItem.farmer_id == farmer_id)
    if status_filter:
        query = query.filter(Order.status == status_filter)

    orders = query.distinct().order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders, view_as="farmer", status_filter=status_filter)


@app.route("/farmer/order/<int:order_id>/status", methods=["POST"])
@login_required
@role_required("farmer", "admin")
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    new_status = request.form.get("status")
    
    # Verify that this farmer owns an item in this order or is admin
    farmer_id = session["user_id"]
    is_owner = any(item.farmer_id == farmer_id for item in order.items)
    if not is_owner and session.get("user_role") != "admin":
        flash("You are not authorized to update this order.", "danger")
        return redirect(url_for("farmer_orders"))

    if not order.can_transition_to(new_status):
        flash(f"Cannot transition order from '{order.status}' to '{new_status}'.", "danger")
        return redirect(url_for("farmer_orders"))

    order.status = new_status

    # If rejected, restore stock
    if new_status == "Rejected":
        for item in order.items:
            prod = db.session.get(Product, item.product_id)
            if prod:
                prod.quantity = round(prod.quantity + item.quantity, 2)
                prod.is_available = True

    # Send Notification to Buyer
    status_notes = {
        "Accepted": "The farmer accepted your order and is preparing the produce.",
        "Ready for Dispatch": "Your order is packed and ready for pickup / delivery dispatch.",
        "Completed": "Your order has been fulfilled. Thank you for supporting direct farmers!",
        "Rejected": "The farmer was unable to accept this order at this time. Stock has been restored."
    }
    buyer_msg = f"Order #{order.id} status updated to '{new_status}'. {status_notes.get(new_status, '')}"
    db.session.add(Notification(user_id=order.buyer_id, message=buyer_msg, related_order_id=order.id))

    db.session.commit()
    flash(f"Order #{order.id} status updated to '{new_status}'.", "success")
    return redirect(request.referrer or url_for("farmer_orders"))


# ==========================================
# BUYER DASHBOARD
# ==========================================

@app.route("/buyer/dashboard")
@login_required
def buyer_dashboard():
    user = db.session.get(User, session["user_id"])
    if user.is_farmer():
        return redirect(url_for("farmer_dashboard"))

    # Active and recent orders
    orders = Order.query.filter_by(buyer_id=user.id).order_by(Order.created_at.desc()).all()
    active_orders = [o for o in orders if o.status in ["Pending", "Accepted", "Ready for Dispatch"]]
    completed_orders = [o for o in orders if o.status == "Completed"]
    total_spent = sum(o.total_amount for o in completed_orders)

    # AI Personalized Recommendations
    available_products = Product.query.filter_by(is_available=True).filter(Product.quantity > 0).all()
    recommendations = rank_products_for_buyer(
        products=available_products,
        buyer=user,
        limit=6
    )

    # Surplus Rescue Deals for Buyer
    surplus_deals = (
        Product.query.filter_by(is_available=True, is_surplus=True)
        .order_by(Product.discount_percentage.desc())
        .limit(4)
        .all()
    )

    return render_template(
        "buyer_dashboard.html",
        user=user,
        active_orders=active_orders,
        completed_orders=completed_orders,
        total_spent=round(total_spent, 2),
        recommendations=recommendations,
        surplus_deals=surplus_deals
    )


# ==========================================
# AI INSIGHTS & API ENDPOINTS
# ==========================================

@app.route("/ai/insights")
def ai_insights():
    # Dedicated interactive AI Hub
    # Get reference data count
    ref_count = PriceReference.query.count()
    all_categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]

    # Sample demo benchmark calculations
    sample_benchmarks = [
        estimate_fair_price("Tomatoes", "Vegetables", 100, "kg", harvest_date=date.today(), district="Pune", price_ref_model=PriceReference),
        estimate_fair_price("Basmati Rice", "Grains", 500, "kg", harvest_date=None, district="Karnal", price_ref_model=PriceReference),
        estimate_fair_price("Alphonso Mangoes", "Fruits", 50, "dozen", harvest_date=date.today(), district="Ratnagiri", price_ref_model=PriceReference),
    ]

    return render_template(
        "ai_insights.html",
        categories=all_categories or ["Vegetables", "Fruits", "Grains", "Pulses", "Spices", "Dairy & Honey"],
        ref_count=ref_count,
        sample_benchmarks=sample_benchmarks
    )


@app.route("/api/ai/estimate-price", methods=["POST"])
def api_estimate_price():
    data = request.get_json(silent=True) or request.form
    product_name = data.get("product_name", "").strip()
    category = data.get("category", "Vegetables").strip()
    quantity = float(data.get("quantity", 100.0) or 100.0)
    unit = data.get("unit", "kg").strip()
    district = data.get("district", "").strip()
    current_price = float(data.get("current_price", 0) or 0) if data.get("current_price") else None
    
    harvest_date = None
    harvest_str = data.get("harvest_date")
    if harvest_str:
        try:
            harvest_date = datetime.strptime(harvest_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    analysis = estimate_fair_price(
        product_name=product_name,
        category=category,
        quantity=quantity,
        unit=unit,
        harvest_date=harvest_date,
        current_price=current_price,
        district=district,
        price_ref_model=PriceReference
    )
    return jsonify(analysis)


@app.route("/api/ai/match-listings", methods=["POST"])
def api_match_listings():
    data = request.get_json(silent=True) or request.form
    buyer = None
    if "user_id" in session:
        buyer = db.session.get(User, session["user_id"])

    search_query = data.get("search_query")
    preferred_category = data.get("category")
    required_quantity = float(data.get("quantity")) if data.get("quantity") else None
    max_budget = float(data.get("max_budget")) if data.get("max_budget") else None

    products = Product.query.filter_by(is_available=True).filter(Product.quantity > 0).all()
    results = rank_products_for_buyer(
        products=products,
        buyer=buyer,
        required_quantity=required_quantity,
        max_budget_per_unit=max_budget,
        preferred_category=preferred_category,
        search_query=search_query,
        limit=10
    )

    output = []
    for r in results:
        p = r["product"]
        output.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.effective_price,
            "unit": p.unit,
            "quantity": p.quantity,
            "location": p.location,
            "farmer_name": p.farmer.name,
            "match_score": r["match_score"],
            "explanation": r["explanation"],
            "is_bulk_suitable": r["is_bulk_suitable"]
        })

    return jsonify({"results": output})


# ==========================================
# NOTIFICATIONS
# ==========================================

@app.route("/notifications")
@login_required
def notifications():
    user_id = session["user_id"]
    user_notifications = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications.html", notifications=user_notifications)


@app.route("/notifications/mark-read/<int:notif_id>", methods=["POST"])
@login_required
def mark_notification_read(notif_id):
    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == session["user_id"]:
        notif.is_read = True
        db.session.commit()
    return redirect(request.referrer or url_for("notifications"))


@app.route("/notifications/mark-all-read", methods=["POST"])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=session["user_id"]).update({"is_read": True})
    db.session.commit()
    flash("All notifications marked as read.", "info")
    return redirect(request.referrer or url_for("notifications"))


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin")
@login_required
@role_required("admin")
def admin_dashboard():
    total_users = User.query.count()
    total_farmers = User.query.filter_by(role="farmer").count()
    total_buyers = User.query.filter_by(role="buyer").count()
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_available=True).count()
    total_orders = Order.query.count()
    
    # Total Gross Merchandise Value
    total_gmv = db.session.query(db.func.sum(Order.total_amount)).filter(Order.status != "Cancelled").scalar() or 0.0

    users_list = User.query.order_by(User.created_at.desc()).limit(20).all()
    products_list = Product.query.order_by(Product.created_at.desc()).limit(20).all()
    orders_list = Order.query.order_by(Order.created_at.desc()).limit(15).all()
    reports_list = Report.query.order_by(Report.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_farmers=total_farmers,
        total_buyers=total_buyers,
        total_products=total_products,
        active_products=active_products,
        total_orders=total_orders,
        total_gmv=round(total_gmv, 2),
        users_list=users_list,
        products_list=products_list,
        orders_list=orders_list,
        reports_list=reports_list
    )


@app.route("/admin/product/<int:product_id>/toggle-status", methods=["POST"])
@login_required
@role_required("admin")
def admin_toggle_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    product.is_available = not product.is_available
    db.session.commit()
    
    status_label = "Active" if product.is_available else "Suspended / Disabled"
    flash(f"Listing '{product.name}' status set to {status_label}.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/report/<int:report_id>/<action>", methods=["POST"])
@login_required
@role_required("admin")
def admin_handle_report(report_id, action):
    report = db.session.get(Report, report_id)
    if not report:
        abort(404)

    if action == "dismiss":
        report.status = "Dismissed"
        flash(f"Report #{report.id} dismissed.", "info")
    elif action == "disable-product":
        report.status = "Resolved"
        if report.product:
            report.product.is_available = False
            flash(f"Listing '{report.product.name}' disabled and report marked as resolved.", "warning")
    else:
        report.status = "Reviewed"

    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@role_required("admin")
def admin_toggle_user(user_id):
    if user_id == session["user_id"]:
        flash("You cannot suspend your own administrative account.", "danger")
        return redirect(url_for("admin_dashboard"))

    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "suspended"
    flash(f"User '{user.name}' ({user.email}) has been {status_str}.", "info")
    return redirect(url_for("admin_dashboard"))


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template("error.html", code=404, title="Page Not Found", message="The requested agricultural listing or page could not be found."), 404


@app.errorhandler(403)
def forbidden_error(error):
    return render_template("error.html", code=403, title="Access Forbidden", message="You do not have administrative or role-based clearance to access this resource."), 403


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("error.html", code=500, title="Server Error", message="An unexpected server error occurred. Please try again or return to the marketplace."), 500


# Application CLI commands
@app.cli.command("init-db")
def init_db_command():
    """Initializes the database tables."""
    db.create_all()
    print("Database tables created successfully.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Run development server
    app.run(host="127.0.0.1", port=5000, debug=True)
