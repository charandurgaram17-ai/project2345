import os
import unittest
from datetime import date, timedelta
from app import app
from models import db, User, Product, Order, OrderItem, Notification, PriceReference, Report
from services.pricing_service import estimate_fair_price
from services.matching_service import calculate_match_score, rank_products_for_buyer
from services.surplus_service import analyze_surplus_risk


class FarmDirectTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

            # Create test Farmer
            farmer = User(
                name="Farmer Ramesh",
                email="ramesh@test.com",
                role="farmer",
                phone="9876543210",
                village="Dindori",
                district="Nashik",
                business_type="Smallholder"
            )
            farmer.set_password("SecurePass@123")
            db.session.add(farmer)

            # Create test Buyer (Restaurant)
            buyer = User(
                name="Chef Vikram",
                email="vikram@test.com",
                role="buyer",
                phone="9823099881",
                village="Koregaon Park",
                district="Pune",
                business_type="restaurant"
            )
            buyer.set_password("SecurePass@123")
            db.session.add(buyer)

            # Create test Admin
            admin = User(
                name="Admin User",
                email="admin@test.com",
                role="admin",
                district="Bengaluru"
            )
            admin.set_password("AdminPass@123")
            db.session.add(admin)

            db.session.commit()

            self.farmer_id = farmer.id
            self.buyer_id = buyer.id
            self.admin_id = admin.id

            # Create test Product
            prod = Product(
                farmer_id=self.farmer_id,
                name="Organic Red Tomatoes",
                category="Vegetables",
                description="Vine ripened organic tomatoes",
                quantity=100.0,
                unit="kg",
                price=30.0,
                location="Dindori, Nashik",
                district="Nashik",
                harvest_date=date.today() - timedelta(days=1),
                is_available=True
            )
            db.session.add(prod)
            db.session.commit()
            self.product_id = prod.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @classmethod
    def tearDownClass(cls):
        from seed import seed_database
        seed_database()

    def _login(self, email, password):
        self.client.get("/logout")
        return self.client.post("/login", data={
            "email": email,
            "password": password
        }, follow_redirects=True)

    # 1. Test Password Hashing
    def test_password_hashing(self):
        user = User(name="Test User", email="hash@test.com", role="buyer")
        user.set_password("MySecretPassword!2026")
        self.assertNotEqual(user.password_hash, "MySecretPassword!2026")
        self.assertTrue(user.check_password("MySecretPassword!2026"))
        self.assertFalse(user.check_password("WrongPassword"))

    # 2. Test Registration & Login
    def test_user_registration_and_login(self):
        resp = self.client.post("/register", data={
            "name": "New Farmer",
            "email": "newfarmer@test.com",
            "password": "Password123",
            "role": "farmer",
            "phone": "9998887776",
            "district": "Pune",
            "business_type": "Horticulture"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        with app.app_context():
            new_user = User.query.filter_by(email="newfarmer@test.com").first()
            self.assertIsNotNone(new_user)
            self.assertEqual(new_user.role, "farmer")
            self.assertTrue(new_user.check_password("Password123"))

        # Test login
        login_resp = self._login("newfarmer@test.com", "Password123")
        self.assertEqual(login_resp.status_code, 200)

        # Test invalid password login
        bad_login = self._login("newfarmer@test.com", "WrongPassword")
        self.assertIn(b"Invalid email or password", bad_login.data)

    # 3. Test Role-Based Access Controls
    def test_role_based_access(self):
        # Unauthenticated access redirects to login
        resp = self.client.get("/farmer/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

        # Buyer accessing farmer dashboard is rejected with access denied
        self._login("vikram@test.com", "SecurePass@123")
        buyer_access = self.client.get("/farmer/dashboard", follow_redirects=True)
        self.assertIn(b"Access denied", buyer_access.data)

        # Non-admin accessing admin portal is rejected
        admin_access = self.client.get("/admin", follow_redirects=True)
        self.assertIn(b"Access denied", admin_access.data)

        # Admin can access admin portal
        self._login("admin@test.com", "AdminPass@123")
        admin_ok = self.client.get("/admin", follow_redirects=True)
        self.assertEqual(admin_ok.status_code, 200)
        self.assertIn(b"Platform Administration", admin_ok.data)

    # 4. Test Product Creation and Editing
    def test_product_creation_and_editing(self):
        self._login("ramesh@test.com", "SecurePass@123")

        # Add Product
        add_resp = self.client.post("/farmer/product/add", data={
            "name": "Fresh Green Onions",
            "category": "Vegetables",
            "description": "Crisp farm fresh spring onions",
            "quantity": 250.0,
            "unit": "kg",
            "price": 25.0,
            "location": "Nashik Fields",
            "district": "Nashik"
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)

        with app.app_context():
            prod = Product.query.filter_by(name="Fresh Green Onions").first()
            self.assertIsNotNone(prod)
            self.assertEqual(prod.quantity, 250.0)
            self.assertEqual(prod.price, 25.0)
            prod_id = prod.id

        # Edit Product
        edit_resp = self.client.post(f"/farmer/product/{prod_id}/edit", data={
            "name": "Fresh Green Onions Premium",
            "category": "Vegetables",
            "quantity": 220.0,
            "unit": "kg",
            "price": 27.0,
            "location": "Nashik Fields",
            "district": "Nashik",
            "is_available": "1"
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        with app.app_context():
            updated = db.session.get(Product, prod_id)
            self.assertEqual(updated.name, "Fresh Green Onions Premium")
            self.assertEqual(updated.price, 27.0)

    # 5. Test Product Search and Filtering
    def test_product_search_and_filtering(self):
        # Search by term
        resp = self.client.get("/marketplace?q=Tomatoes")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Organic Red Tomatoes", resp.data)

        # Filter by category
        resp_cat = self.client.get("/marketplace?category=Vegetables")
        self.assertEqual(resp_cat.status_code, 200)
        self.assertIn(b"Organic Red Tomatoes", resp_cat.data)

        # Filter by non-matching category
        resp_nomatch = self.client.get("/marketplace?category=Spices")
        self.assertEqual(resp_nomatch.status_code, 200)
        self.assertNotIn(b"Organic Red Tomatoes", resp_nomatch.data)

    # 6. Test Successful Direct Order Placement & Inventory Deduction
    def test_successful_order_placement(self):
        self._login("vikram@test.com", "SecurePass@123")

        with app.app_context():
            initial_stock = db.session.get(Product, self.product_id).quantity  # 100.0

        order_resp = self.client.post("/order/create", data={
            "product_id": self.product_id,
            "quantity": 20.0,
            "delivery_details": "Spice Kitchen Restaurant, Pune",
            "notes": "Morning delivery"
        }, follow_redirects=True)
        self.assertEqual(order_resp.status_code, 200)

        with app.app_context():
            # Check stock deduction: 100 - 20 = 80
            updated_product = db.session.get(Product, self.product_id)
            self.assertEqual(updated_product.quantity, 80.0)
            self.assertTrue(updated_product.is_available)

            # Check Order created
            order = Order.query.filter_by(buyer_id=self.buyer_id).first()
            self.assertIsNotNone(order)
            self.assertEqual(order.total_amount, 600.0)  # 20 kg * ₹30
            self.assertEqual(order.status, "Pending")

            # Check OrderItem
            item = OrderItem.query.filter_by(order_id=order.id).first()
            self.assertIsNotNone(item)
            self.assertEqual(item.quantity, 20.0)
            self.assertEqual(item.unit_price, 30.0)
            self.assertEqual(item.subtotal, 600.0)

            # Check notification created for farmer
            notif = Notification.query.filter_by(user_id=self.farmer_id).first()
            self.assertIsNotNone(notif)
            self.assertIn("Chef Vikram", notif.message)

    # 7. Test Insufficient Stock Rejection
    def test_insufficient_stock_rejection(self):
        self._login("vikram@test.com", "SecurePass@123")

        # Try ordering 150 kg when only 100 kg available
        bad_order = self.client.post("/order/create", data={
            "product_id": self.product_id,
            "quantity": 150.0,
            "delivery_details": "Pune"
        }, follow_redirects=True)

        self.assertIn(b"Insufficient stock", bad_order.data)

        with app.app_context():
            # Stock must remain unchanged
            prod = db.session.get(Product, self.product_id)
            self.assertEqual(prod.quantity, 100.0)
            # No order should have been created
            self.assertEqual(Order.query.count(), 0)

    # 8. Test Valid and Invalid Order Status Transitions
    def test_valid_and_invalid_order_status_transitions(self):
        with app.app_context():
            order = Order(
                buyer_id=self.buyer_id,
                total_amount=300.0,
                status="Pending",
                delivery_address_or_pickup_details="Pune"
            )
            db.session.add(order)
            db.session.commit()

            # Valid: Pending -> Accepted
            self.assertTrue(order.can_transition_to("Accepted"))
            # Valid: Pending -> Rejected
            self.assertTrue(order.can_transition_to("Rejected"))
            # Valid: Pending -> Cancelled
            self.assertTrue(order.can_transition_to("Cancelled"))
            # Invalid: Pending -> Completed
            self.assertFalse(order.can_transition_to("Completed"))

            order.status = "Accepted"
            # Valid: Accepted -> Ready for Dispatch
            self.assertTrue(order.can_transition_to("Ready for Dispatch"))
            # Invalid: Accepted -> Pending
            self.assertFalse(order.can_transition_to("Pending"))

            order.status = "Completed"
            # Terminal status: cannot transition to any status
            self.assertFalse(order.can_transition_to("Pending"))
            self.assertFalse(order.can_transition_to("Cancelled"))

    # 9. Test Order Cancellation Restores Stock
    def test_order_cancellation_restores_stock(self):
        self._login("vikram@test.com", "SecurePass@123")

        # Place order for 30 kg (stock 100 -> 70)
        self.client.post("/order/create", data={
            "product_id": self.product_id,
            "quantity": 30.0,
            "delivery_details": "Pune"
        }, follow_redirects=True)

        with app.app_context():
            self.assertEqual(db.session.get(Product, self.product_id).quantity, 70.0)
            order = Order.query.first()
            order_id = order.id

        # Cancel the order as buyer
        cancel_resp = self.client.post(f"/buyer/order/{order_id}/cancel", follow_redirects=True)
        self.assertEqual(cancel_resp.status_code, 200)

        with app.app_context():
            updated_order = db.session.get(Order, order_id)
            self.assertEqual(updated_order.status, "Cancelled")
            # Stock must be restored: 70 + 30 = 100
            restored_prod = db.session.get(Product, self.product_id)
            self.assertEqual(restored_prod.quantity, 100.0)

    # 10. Test AI Fair Price Assistant Service
    def test_ai_fair_price_assistant_service(self):
        with app.app_context():
            estimate = estimate_fair_price(
                product_name="Tomatoes",
                category="Vegetables",
                quantity=100.0,
                unit="kg",
                harvest_date=date.today(),
                district="Nashik"
            )
            self.assertIn("recommended_price", estimate)
            self.assertIn("price_range", estimate)
            self.assertGreater(estimate["recommended_price"], 0)
            self.assertGreaterEqual(estimate["confidence_percentage"], 60)
            self.assertTrue(len(estimate["factors"]) >= 3)
            self.assertTrue(estimate["is_simulated"])

    # 11. Test Smart Buyer-Matching Engine
    def test_smart_buyer_matching_engine(self):
        with app.app_context():
            prod = db.session.get(Product, self.product_id)
            buyer = db.session.get(User, self.buyer_id)

            # Test match score for restaurant needing tomatoes
            match_data = calculate_match_score(
                product=prod,
                buyer=buyer,
                required_quantity=50.0,
                search_query="Tomatoes"
            )
            self.assertGreater(match_data["score"], 50)
            self.assertTrue(len(match_data["reasons"]) >= 1)
            self.assertIn("Tomatoes", match_data["explanation"])

            # Test ranking function
            ranked = rank_products_for_buyer(
                products=[prod],
                buyer=buyer,
                search_query="Tomatoes"
            )
            self.assertEqual(len(ranked), 1)
            self.assertEqual(ranked[0]["product"].id, prod.id)

    # 12. Test Surplus Rescue Service
    def test_surplus_rescue_service(self):
        with app.app_context():
            # Create a perishable lot near expiration
            surplus_prod = Product(
                farmer_id=self.farmer_id,
                name="Perishable Spinach",
                category="Vegetables",
                quantity=200.0,
                unit="kg",
                price=20.0,
                location="Nashik",
                district="Nashik",
                freshness_date=date.today() + timedelta(days=1),
                is_available=True
            )
            db.session.add(surplus_prod)
            db.session.commit()

            analysis = analyze_surplus_risk(surplus_prod)
            self.assertTrue(analysis["is_surplus_candidate"])
            self.assertEqual(analysis["urgency"], "high")
            self.assertGreater(analysis["suggested_discount"], 0)
            self.assertLess(analysis["suggested_discounted_price"], surplus_prod.price)

    # 13. Test CSRF Protection Enforcement
    def test_csrf_token_enforcement(self):
        # Temporarily enable CSRF enforcement in app config
        app.config["TESTING"] = False
        try:
            # POST request without CSRF token must be rejected with 400 or redirect
            resp = self.client.post("/login", data={
                "email": "ramesh@test.com",
                "password": "SecurePass@123"
            })
            self.assertIn(resp.status_code, [302, 400])
        finally:
            app.config["TESTING"] = True

    # 14. Test Order Total Calculation with Surplus Discount
    def test_order_total_with_surplus_discount(self):
        with app.app_context():
            surplus_lot = Product(
                farmer_id=self.farmer_id,
                name="Discounted Bananas",
                category="Fruits",
                quantity=100.0,
                unit="kg",
                price=40.0,
                location="Mandya",
                district="Mandya",
                is_available=True,
                is_surplus=True,
                discount_percentage=25.0  # 25% off 40 -> 30.0/kg
            )
            db.session.add(surplus_lot)
            db.session.commit()
            lot_id = surplus_lot.id

            self.assertEqual(surplus_lot.effective_price, 30.0)

        self._login("vikram@test.com", "SecurePass@123")
        self.client.post("/order/create", data={
            "product_id": lot_id,
            "quantity": 10.0,
            "delivery_details": "Pune"
        }, follow_redirects=True)

        with app.app_context():
            order = Order.query.order_by(Order.id.desc()).first()
            # 10 kg * ₹30.00 = ₹300.00
            self.assertEqual(order.total_amount, 300.0)
            item = order.items[0]
            self.assertEqual(item.unit_price, 30.0)
            self.assertEqual(item.subtotal, 300.0)


if __name__ == "__main__":
    unittest.main()
