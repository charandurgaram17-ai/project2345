"""
Seed script for FarmDirect AI.
Populates SQLite database with realistic Indian agricultural demonstration data:
- Demo Farmers across agricultural regions (Maharashtra, Punjab, Karnataka, Tamil Nadu)
- Demo Buyers (Restaurant, Retailer, Wholesaler, Individual Consumer)
- Protected Demo Admin
- Authentic produce listings with prices in INR (Tomatoes, Onions, Potatoes, Mangoes, Rice, etc.)
- Demo benchmark price references (National Agmarknet Mandi Baseline)
- Pre-populated orders, notifications, and surplus stock deals for a rich out-of-the-box demo.
"""

from datetime import date, datetime, timedelta, timezone
from app import app
from models import db, User, Product, Order, OrderItem, Notification, PriceReference, Report


def seed_database():
    with app.app_context():
        # Clean slate for clean seeding
        db.drop_all()
        db.create_all()

        print("--- Seeding Users ---")
        demo_password = "Password@123"

        # 1. Admin
        admin = User(
            name="System Administrator",
            email="admin@farmdirect.ai",
            role="admin",
            phone="+91 98765 00001",
            village="Cyber City",
            district="Bengaluru",
            business_type="Platform Operations"
        )
        admin.set_password(demo_password)
        db.session.add(admin)

        # 2. Farmers
        farmer1 = User(
            name="Rameshwar Patel",
            email="farmer.ramesh@farmdirect.demo",
            role="farmer",
            phone="+91 98220 11223",
            village="Dindori",
            district="Nashik",
            business_type="Smallholder Farmer",
            farm_details="12 acres organic certified vegetable farm specializing in vine-ripened tomatoes, red onions, and seedless green chillies. Uses solar drip irrigation."
        )
        farmer1.set_password(demo_password)
        db.session.add(farmer1)

        farmer2 = User(
            name="Sardar Balvinder Singh",
            email="farmer.balvinder@farmdirect.demo",
            role="farmer",
            phone="+91 98140 44556",
            village="Samrala",
            district="Ludhiana",
            business_type="Progressive Farmer",
            farm_details="40 acres multi-crop farm producing aromatic 1121 Basmati Rice and Sharbati Wheat with zero stubble burning and eco-friendly soil mulching."
        )
        farmer2.set_password(demo_password)
        db.session.add(farmer2)

        farmer3 = User(
            name="Suresh Kumar Gowda",
            email="farmer.suresh@farmdirect.demo",
            role="farmer",
            phone="+91 94480 77889",
            village="Srirangapatna",
            district="Mandya",
            business_type="Horticulture Farmer",
            farm_details="15 acres river-fed orchard producing GI-tagged Yelakki Bananas, tender coconuts, and fresh jaggery."
        )
        farmer3.set_password(demo_password)
        db.session.add(farmer3)

        farmer4 = User(
            name="Venkatesh Rao",
            email="farmer.venkat@farmdirect.demo",
            role="farmer",
            phone="+91 97000 33445",
            village="Tenali",
            district="Guntur",
            business_type="Spice Cultivator",
            farm_details="8 acres export-grade Teja Red Chilli and natural turmeric fields."
        )
        farmer4.set_password(demo_password)
        db.session.add(farmer4)

        # 3. Buyers
        buyer_restaurant = User(
            name="Chef Vikram (Spice Kitchen)",
            email="spicekitchen@demo.com",
            role="buyer",
            phone="+91 98230 99881",
            village="Koregaon Park",
            district="Pune",
            business_type="restaurant",
            farm_details="Casual fine-dining restaurant requiring 80-120 kg of fresh farm vegetables and chillies every 3 days."
        )
        buyer_restaurant.set_password(demo_password)
        db.session.add(buyer_restaurant)

        buyer_wholesaler = User(
            name="AgroMega Wholesale Hub",
            email="agromega@demo.com",
            role="buyer",
            phone="+91 98200 44332",
            village="Vashi APMC",
            district="Navi Mumbai",
            business_type="wholesaler",
            farm_details="Regional wholesale trader procuring 5-20 tonne grain and onion consignments for supermarket chains."
        )
        buyer_wholesaler.set_password(demo_password)
        db.session.add(buyer_wholesaler)

        buyer_retailer = User(
            name="Daily Fresh Supermarket",
            email="dailyfresh@demo.com",
            role="buyer",
            phone="+91 99001 22334",
            village="Indiranagar",
            district="Bengaluru",
            business_type="retailer",
            farm_details="Neighborhood organic and farm-fresh grocery store serving 500+ households."
        )
        buyer_retailer.set_password(demo_password)
        db.session.add(buyer_retailer)

        buyer_consumer = User(
            name="Anita Sharma",
            email="anita.consumer@demo.com",
            role="buyer",
            phone="+91 98110 55667",
            village="Hauz Khas",
            district="Delhi",
            business_type="consumer",
            farm_details="Individual health-conscious consumer ordering seasonal farm produce directly."
        )
        buyer_consumer.set_password(demo_password)
        db.session.add(buyer_consumer)

        db.session.commit()
        print("Users seeded successfully.")

        # ==========================================
        # 4. PRICE REFERENCE DATA (Demo Mandi Baseline)
        # ==========================================
        print("--- Seeding Benchmark Price References ---")
        price_refs = [
            PriceReference(product_category="Vegetables", product_name="Tomatoes", location="Nashik", reference_price=26.0, unit="kg", source_name="Agmarknet Demo Mandi Baseline"),
            PriceReference(product_category="Vegetables", product_name="Tomatoes", location="Pune", reference_price=28.0, unit="kg", source_name="Agmarknet Demo Mandi Baseline"),
            PriceReference(product_category="Vegetables", product_name="Onions", location="Nashik", reference_price=30.0, unit="kg", source_name="Lasalgaon Mandi Demo Reference"),
            PriceReference(product_category="Vegetables", product_name="Potatoes", location="Agra", reference_price=22.0, unit="kg", source_name="Agmarknet Demo Mandi Baseline"),
            PriceReference(product_category="Vegetables", product_name="Green Chillies", location="Guntur", reference_price=42.0, unit="kg", source_name="Guntur Mirchi Yard Demo Baseline"),
            PriceReference(product_category="Vegetables", product_name="Organic Spinach", location="Pune", reference_price=20.0, unit="kg", source_name="Regional Krishi Kendra"),
            PriceReference(product_category="Fruits", product_name="Yelakki Bananas", location="Mandya", reference_price=38.0, unit="kg", source_name="APMC Mysore Demo Data"),
            PriceReference(product_category="Fruits", product_name="Alphonso Mangoes", location="Ratnagiri", reference_price=110.0, unit="dozen", source_name="Konkan Horticulture Reference"),
            PriceReference(product_category="Grains", product_name="1121 Basmati Rice", location="Ludhiana", reference_price=82.0, unit="kg", source_name="Punjab Mandi Board Demo"),
            PriceReference(product_category="Grains", product_name="Sharbati Wheat", location="Ludhiana", reference_price=28.0, unit="kg", source_name="Punjab Mandi Board Demo"),
            PriceReference(product_category="Pulses", product_name="Desi Toor Dal", location="Gulbarga", reference_price=120.0, unit="kg", source_name="Karnataka Pulse Board Demo"),
            PriceReference(product_category="Spices", product_name="Salem Turmeric", location="Erode", reference_price=135.0, unit="kg", source_name="Spices Board Demo Reference"),
        ]
        db.session.add_all(price_refs)
        db.session.commit()

        # ==========================================
        # 5. AGRICULTURAL PRODUCE LISTINGS
        # ==========================================
        print("--- Seeding Product Listings ---")
        today = date.today()

        p1 = Product(
            farmer_id=farmer1.id,
            name="Vine-Ripened Hybrid Red Tomatoes",
            category="Vegetables",
            description="Grade-A naturally grown firm red tomatoes. Freshly picked at dawn. Ideal for gravies, purées, and restaurant kitchen consumption. Zero chemical ripeners.",
            quantity=350.0,
            unit="kg",
            price=28.0,
            location="Dindori, Nashik",
            village="Dindori",
            district="Nashik",
            harvest_date=today - timedelta(days=1),
            freshness_date=today + timedelta(days=6),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        p2 = Product(
            farmer_id=farmer1.id,
            name="Nashik Red Storage Onions (Garwa Quality)",
            category="Vegetables",
            description="Well-cured medium to large red onions with dry outer skin. Long shelf life of over 45 days. Perfect for bulk restaurant and retail sourcing.",
            quantity=1200.0,
            unit="kg",
            price=31.0,
            location="Dindori, Nashik",
            village="Dindori",
            district="Nashik",
            harvest_date=today - timedelta(days=5),
            freshness_date=today + timedelta(days=40),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        p3 = Product(
            farmer_id=farmer1.id,
            name="Crisp Green Chillies (G-4 Variety)",
            category="Vegetables",
            description="Dark green pungent chillies, unbruised and hand-graded. Ready for immediate kitchen and spice processing dispatch.",
            quantity=80.0,
            unit="kg",
            price=44.0,
            location="Dindori, Nashik",
            village="Dindori",
            district="Nashik",
            harvest_date=today - timedelta(days=1),
            freshness_date=today + timedelta(days=7),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        p4 = Product(
            farmer_id=farmer1.id,
            name="Farm Surplus Fresh Spinach (Palak) - Clearance Lot",
            category="Vegetables",
            description="Hydro-washed nutrient-dense tender spinach leaves. Harvested 2 days ago. Discounted for immediate clearance before freshness declines.",
            quantity=120.0,
            unit="kg",
            price=24.0,
            location="Dindori, Nashik",
            village="Dindori",
            district="Nashik",
            harvest_date=today - timedelta(days=2),
            freshness_date=today + timedelta(days=2),
            is_available=True,
            is_surplus=True,
            discount_percentage=25.0  # 25% surplus discount -> effective ₹18.00/kg
        )

        p5 = Product(
            farmer_id=farmer2.id,
            name="Aged Royal 1121 Basmati Rice (Steam Grade)",
            category="Grains",
            description="Extra-long grain aromatic Basmati rice, aged for 14 months for non-sticky, fluffiest grains upon cooking. Suitable for biryanis and wholesale trade.",
            quantity=2500.0,
            unit="kg",
            price=85.0,
            location="Samrala, Ludhiana",
            village="Samrala",
            district="Ludhiana",
            harvest_date=today - timedelta(days=90),
            freshness_date=today + timedelta(days=270),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        p6 = Product(
            farmer_id=farmer2.id,
            name="Natural Sharbati Whole Wheat (MP Quality)",
            category="Grains",
            description="Golden heavy-grain wheat with sweet natural aroma and superior gluten strength for softest rotis. Machine cleaned and double sorted.",
            quantity=1800.0,
            unit="kg",
            price=29.0,
            location="Samrala, Ludhiana",
            village="Samrala",
            district="Ludhiana",
            harvest_date=today - timedelta(days=60),
            freshness_date=today + timedelta(days=300),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        p7 = Product(
            farmer_id=farmer3.id,
            name="GI-Tagged Sweet Yelakki Bananas",
            category="Fruits",
            description="Small aromatic Mysore Yelakki bananas naturally ripened with paddy straw. Sweet, thin skinned, rich in potassium.",
            quantity=450.0,
            unit="kg",
            price=39.0,
            location="Srirangapatna, Mandya",
            village="Srirangapatna",
            district="Mandya",
            harvest_date=today - timedelta(days=1),
            freshness_date=today + timedelta(days=5),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        p8 = Product(
            farmer_id=farmer3.id,
            name="Surplus Ripe Yelakki Bananas - Bulk Bakeries & Juices",
            category="Fruits",
            description="Fully ripe sweet bananas with sugar spots. High brix content, perfect for banana breads, purees, juice stalls, and bakeries. 30% discount.",
            quantity=200.0,
            unit="kg",
            price=36.0,
            location="Srirangapatna, Mandya",
            village="Srirangapatna",
            district="Mandya",
            harvest_date=today - timedelta(days=3),
            freshness_date=today + timedelta(days=2),
            is_available=True,
            is_surplus=True,
            discount_percentage=30.0  # effective ₹25.20/kg
        )

        p9 = Product(
            farmer_id=farmer4.id,
            name="Guntur Teja Hot Red Chillies (Stemless)",
            category="Spices",
            description="Sun-dried fiery red chillies with high SHU heat index and vibrant red color. Moisture level below 10%. Packaged in moisture-proof gunny bags.",
            quantity=600.0,
            unit="kg",
            price=145.0,
            location="Tenali, Guntur",
            village="Tenali",
            district="Guntur",
            harvest_date=today - timedelta(days=20),
            freshness_date=today + timedelta(days=180),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        p10 = Product(
            farmer_id=farmer4.id,
            name="Unpolished Desi Toor Dal (Pigeon Pea)",
            category="Pulses",
            description="Traditional farm-processed yellow pigeon peas. High protein, unpolished, zero artificial talc coating or dyes.",
            quantity=850.0,
            unit="kg",
            price=128.0,
            location="Tenali, Guntur",
            village="Tenali",
            district="Guntur",
            harvest_date=today - timedelta(days=35),
            freshness_date=today + timedelta(days=150),
            is_available=True,
            is_surplus=False,
            discount_percentage=0.0
        )

        db.session.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10])
        db.session.commit()
        print("Product listings seeded successfully.")

        # ==========================================
        # 6. DEMO ORDERS & ORDER ITEMS
        # ==========================================
        print("--- Seeding Demo Orders ---")
        # Completed Order 1
        now_utc = datetime.now(timezone.utc)
        order1 = Order(
            buyer_id=buyer_restaurant.id,
            total_amount=1400.0,
            status="Completed",
            delivery_address_or_pickup_details="Spice Kitchen Restaurant, 42 Lane 5, Koregaon Park, Pune, Maharashtra 411001",
            payment_method="Cash on Delivery / Direct Settlement",
            notes="Please dispatch early morning around 7 AM.",
            created_at=now_utc - timedelta(days=3),
            updated_at=now_utc - timedelta(days=2)
        )
        db.session.add(order1)
        db.session.flush()

        item1 = OrderItem(
            order_id=order1.id,
            product_id=p1.id,
            farmer_id=farmer1.id,
            quantity=50.0,
            unit_price=28.0,
            subtotal=1400.0
        )
        db.session.add(item1)

        # In-Progress Order 2 (Ready for Dispatch)
        order2 = Order(
            buyer_id=buyer_wholesaler.id,
            total_amount=15500.0,
            status="Ready for Dispatch",
            delivery_address_or_pickup_details="Sector 19, APMC Yard Gate 3, Vashi, Navi Mumbai, Maharashtra 400703",
            payment_method="Cash on Delivery / Direct Settlement",
            notes="Consignment pickup via commercial tempo.",
            created_at=now_utc - timedelta(days=1),
            updated_at=now_utc - timedelta(hours=6)
        )
        db.session.add(order2)
        db.session.flush()

        item2 = OrderItem(
            order_id=order2.id,
            product_id=p2.id,
            farmer_id=farmer1.id,
            quantity=500.0,
            unit_price=31.0,
            subtotal=15500.0
        )
        db.session.add(item2)

        # Pending Order 3 (Awaiting Farmer Acceptance)
        order3 = Order(
            buyer_id=buyer_retailer.id,
            total_amount=3900.0,
            status="Pending",
            delivery_address_or_pickup_details="Daily Fresh Grocery, 100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038",
            payment_method="Cash on Delivery / Direct Settlement",
            notes="Urgent stock requirement for weekend retail rush.",
            created_at=now_utc - timedelta(hours=3),
            updated_at=now_utc - timedelta(hours=3)
        )
        db.session.add(order3)
        db.session.flush()

        item3 = OrderItem(
            order_id=order3.id,
            product_id=p7.id,
            farmer_id=farmer3.id,
            quantity=100.0,
            unit_price=39.0,
            subtotal=3900.0
        )
        db.session.add(item3)

        # 7. Notifications
        notif1 = Notification(
            user_id=farmer1.id,
            message="Order #1 for 50 kg of Vine-Ripened Hybrid Red Tomatoes was marked Completed. Earnings: ₹1,400.00.",
            related_order_id=order1.id,
            is_read=True
        )
        notif2 = Notification(
            user_id=farmer1.id,
            message="Order #2 for 500 kg of Nashik Red Storage Onions is currently Ready for Dispatch.",
            related_order_id=order2.id,
            is_read=False
        )
        notif3 = Notification(
            user_id=farmer3.id,
            message="New Order #3 received: Daily Fresh Supermarket requested 100 kg of GI-Tagged Sweet Yelakki Bananas.",
            related_order_id=order3.id,
            is_read=False
        )
        db.session.add_all([notif1, notif2, notif3])

        # 8. Demo Safety Report
        report1 = Report(
            reporter_id=buyer_wholesaler.id,
            product_id=p9.id,
            reason="Sample query regarding moisture percentage certification.",
            status="Reviewed"
        )
        db.session.add(report1)

        db.session.commit()
        print("=== Database Seed Completed Successfully! ===")
        print(f"Users created: {User.query.count()}")
        print(f"Products created: {Product.query.count()}")
        print(f"Orders created: {Order.query.count()}")
        print(f"Benchmark price references: {PriceReference.query.count()}")


if __name__ == "__main__":
    seed_database()
