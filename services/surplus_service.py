"""
Surplus Rescue AI Service
Assists farmers in preventing agricultural waste and recovering revenue from excess stock.
Suggests advisory, farmer-controlled discounts.
"""

from datetime import date
from typing import Dict, Any, List

def analyze_surplus_risk(product) -> Dict[str, Any]:
    """
    Evaluates whether a product is at risk of surplus waste and suggests an advisory discount.
    """
    today = date.today()
    reasons = []
    urgency = "low"  # low, medium, high
    suggested_discount = 0.0
    
    # 1. Freshness date check
    if product.freshness_date:
        days_left = (product.freshness_date - today).days
        if days_left <= 0:
            urgency = "high"
            reasons.append("Best-before date reached today. Immediate liquidation recommended.")
            suggested_discount = 35.0
        elif days_left <= 2:
            urgency = "high"
            reasons.append(f"Only {days_left} day(s) left of optimal freshness window.")
            suggested_discount = 25.0
        elif days_left <= 4:
            urgency = "medium"
            reasons.append(f"{days_left} days left of peak shelf life.")
            suggested_discount = 15.0

    # 2. Harvest date check (for perishable vegetables/fruits without explicit freshness date)
    elif product.harvest_date and product.category in ["Vegetables", "Fruits"]:
        days_old = (today - product.harvest_date).days
        if days_old >= 6:
            urgency = "high"
            reasons.append(f"Harvested {days_old} days ago. Perishable freshness declining.")
            suggested_discount = 25.0
        elif days_old >= 4:
            urgency = "medium"
            reasons.append(f"Harvested {days_old} days ago. Expedited sales recommended.")
            suggested_discount = 15.0

    # 3. High remaining stock check
    if product.quantity >= 150 and urgency != "low":
        reasons.append(f"High remaining volume ({product.quantity} {product.unit}) increases waste risk.")
        suggested_discount = min(40.0, suggested_discount + 5.0)

    is_surplus_candidate = urgency in ["medium", "high"]

    # Calculate discounted price if applied
    discounted_price = round(product.price * (1.0 - (suggested_discount / 100.0)), 2) if suggested_discount > 0 else product.price

    return {
        "product_id": product.id,
        "product_name": product.name,
        "is_surplus_candidate": is_surplus_candidate,
        "urgency": urgency,
        "reasons": reasons,
        "suggested_discount": suggested_discount,
        "original_price": product.price,
        "suggested_discounted_price": discounted_price,
        "message": "; ".join(reasons) if reasons else "Product shelf life is optimal. No surplus intervention required."
    }


def get_farmer_surplus_alerts(farmer_products: List[Any]) -> List[Dict[str, Any]]:
    """
    Scans a farmer's inventory to generate actionable surplus alerts.
    """
    alerts = []
    for prod in farmer_products:
        if not prod.is_available or prod.quantity <= 0:
            continue
        analysis = analyze_surplus_risk(prod)
        if analysis["is_surplus_candidate"] and not prod.is_surplus:
            alerts.append(analysis)
    return alerts
