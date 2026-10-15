from datetime import datetime, date, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="buyer")  # farmer, buyer, admin
    phone = db.Column(db.String(20), nullable=True)
    village = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    business_type = db.Column(db.String(50), nullable=True)  # restaurant, retailer, wholesaler, consumer, smallholder
    farm_details = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    products = db.relationship("Product", backref="farmer", lazy="dynamic", foreign_keys="Product.farmer_id")
    orders = db.relationship("Order", backref="buyer", lazy="dynamic", foreign_keys="Order.buyer_id")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    reports = db.relationship("Report", backref="reporter", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_farmer(self):
        return self.role == "farmer"

    def is_buyer(self):
        return self.role == "buyer"

    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # Vegetables, Fruits, Grains, Pulses, Spices, Dairy & Honey
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Float, nullable=False)  # Available stock
    unit = db.Column(db.String(20), nullable=False, default="kg")  # kg, quintal, tonne, litre, dozen, piece
    price = db.Column(db.Float, nullable=False)  # Base price per unit in INR
    location = db.Column(db.String(150), nullable=False)
    village = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True, index=True)
    harvest_date = db.Column(db.Date, nullable=True)
    freshness_date = db.Column(db.Date, nullable=True)  # Best before / expected shelf life
    image_path = db.Column(db.String(255), nullable=True)
    is_available = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_surplus = db.Column(db.Boolean, default=False, nullable=False, index=True)
    discount_percentage = db.Column(db.Float, default=0.0, nullable=False)  # e.g., 20.0 for 20%
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    order_items = db.relationship("OrderItem", backref="product", lazy="dynamic")
    reports = db.relationship("Report", backref="product", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def effective_price(self):
        """Calculates price with surplus discount applied if active."""
        if self.is_surplus and self.discount_percentage > 0:
            discounted = self.price * (1.0 - (self.discount_percentage / 100.0))
            return round(max(discounted, 1.0), 2)
        return round(self.price, 2)

    @property
    def days_since_harvest(self):
        if self.harvest_date:
            today = date.today()
            return max(0, (today - self.harvest_date).days)
        return None

    @property
    def days_until_freshness_expiry(self):
        if self.freshness_date:
            today = date.today()
            return (self.freshness_date - today).days
        return None

    def __repr__(self):
        return f"<Product {self.name} - ₹{self.price}/{self.unit}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="Pending", nullable=False, index=True)
    # Valid statuses: Pending, Accepted, Ready for Dispatch, Completed, Rejected, Cancelled
    delivery_address_or_pickup_details = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), default="Cash on Delivery / Direct Settlement", nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    items = db.relationship("OrderItem", backref="order", lazy="joined", cascade="all, delete-orphan")

    VALID_STATUS_TRANSITIONS = {
        "Pending": ["Accepted", "Rejected", "Cancelled"],
        "Accepted": ["Ready for Dispatch", "Cancelled"],
        "Ready for Dispatch": ["Completed", "Cancelled"],
        "Completed": [],
        "Rejected": [],
        "Cancelled": []
    }

    def can_transition_to(self, new_status):
        return new_status in self.VALID_STATUS_TRANSITIONS.get(self.status, [])

    def __repr__(self):
        return f"<Order #{self.id} [{self.status}] Total: ₹{self.total_amount}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)  # Preserved historical price
    subtotal = db.Column(db.Float, nullable=False)

    farmer = db.relationship("User", foreign_keys=[farmer_id], backref="sales_items")

    def __repr__(self):
        return f"<OrderItem Order #{self.order_id}: Prod #{self.product_id} x {self.quantity}>"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    related_order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def __repr__(self):
        return f"<Notification for User #{self.user_id}: {self.message[:30]}...>"


class PriceReference(db.Model):
    __tablename__ = "price_references"

    id = db.Column(db.Integer, primary_key=True)
    product_category = db.Column(db.String(50), nullable=False, index=True)
    product_name = db.Column(db.String(100), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=False)  # District / State
    reference_price = db.Column(db.Float, nullable=False)  # Baseline reference ₹/kg
    unit = db.Column(db.String(20), default="kg", nullable=False)
    source_name = db.Column(db.String(150), default="Agmarknet Demo Reference Dataset", nullable=False)
    recorded_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    is_demo_data = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<PriceRef {self.product_name} in {self.location}: ₹{self.reference_price}/{self.unit}>"


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pending", nullable=False)  # Pending, Reviewed, Resolved, Dismissed
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def __repr__(self):
        return f"<Report #{self.id} for Product #{self.product_id} ({self.status})>"
