"""
Fair Price Assistant - AI/Heuristic Pricing Service
Provides transparent, explainable price recommendations for farmers.
Advisory only: The farmer always retains 100% control over the final listing price.
"""

from datetime import date
from typing import Dict, Any, Optional

# Synthetic baseline reference prices (₹ per kg) for demonstration and fallback
DEFAULT_COMMODITY_BASELINES = {
    "tomatoes": {"base": 28.0, "category": "Vegetables", "shelf_life_days": 7},
    "tomato": {"base": 28.0, "category": "Vegetables", "shelf_life_days": 7},
    "onions": {"base": 32.0, "category": "Vegetables", "shelf_life_days": 30},
    "onion": {"base": 32.0, "category": "Vegetables", "shelf_life_days": 30},
    "potatoes": {"base": 24.0, "category": "Vegetables", "shelf_life_days": 45},
    "potato": {"base": 24.0, "category": "Vegetables", "shelf_life_days": 45},
    "green chillies": {"base": 45.0, "category": "Vegetables", "shelf_life_days": 8},
    "chilli": {"base": 45.0, "category": "Vegetables", "shelf_life_days": 8},
    "spinach": {"base": 22.0, "category": "Vegetables", "shelf_life_days": 3},
    "leafy vegetables": {"base": 22.0, "category": "Vegetables", "shelf_life_days": 3},
    "bananas": {"base": 35.0, "category": "Fruits", "shelf_life_days": 6},
    "banana": {"base": 35.0, "category": "Fruits", "shelf_life_days": 6},
    "mangoes": {"base": 95.0, "category": "Fruits", "shelf_life_days": 10},
    "mango": {"base": 95.0, "category": "Fruits", "shelf_life_days": 10},
    "apples": {"base": 110.0, "category": "Fruits", "shelf_life_days": 20},
    "rice": {"base": 55.0, "category": "Grains", "shelf_life_days": 180},
    "basmati rice": {"base": 85.0, "category": "Grains", "shelf_life_days": 180},
    "wheat": {"base": 28.0, "category": "Grains", "shelf_life_days": 180},
    "toor dal": {"base": 125.0, "category": "Pulses", "shelf_life_days": 120},
    "moong dal": {"base": 115.0, "category": "Pulses", "shelf_life_days": 120},
    "mustard seeds": {"base": 70.0, "category": "Spices", "shelf_life_days": 180},
    "turmeric": {"base": 140.0, "category": "Spices", "shelf_life_days": 180},
}

CATEGORY_DEFAULT_BASELINES = {
    "Vegetables": 30.0,
    "Fruits": 60.0,
    "Grains": 40.0,
    "Pulses": 100.0,
    "Spices": 120.0,
    "Dairy & Honey": 75.0,
    "Other": 40.0
}

UNIT_MULTIPLIERS = {
    "kg": 1.0,
    "quintal": 100.0,
    "tonne": 1000.0,
    "litre": 1.0,
    "dozen": 1.5,   # Average approximation for fruits like bananas
    "piece": 2.0    # Coconuts, watermelons, etc.
}


def estimate_fair_price(
    product_name: str,
    category: str,
    quantity: float = 100.0,
    unit: str = "kg",
    harvest_date: Optional[date] = None,
    freshness_date: Optional[date] = None,
    current_price: Optional[float] = None,
    district: Optional[str] = None,
    price_ref_model=None
) -> Dict[str, Any]:
    """
    Computes an explainable fair price recommendation for a farmer's listing.
    """
    clean_name = product_name.strip().lower()
    clean_category = category.strip()
    clean_unit = unit.strip().lower()
    
    # Unit multiplier to scale relative to 1 kg baseline
    unit_multiplier = UNIT_MULTIPLIERS.get(clean_unit, 1.0)
    
    # 1. Base price lookup (from DB PriceReference or fallback table)
    baseline_price_kg = None
    data_source = "Demo Benchmark Dataset"
    confidence = 70
    
    # Try database lookup if price_ref_model is provided
    if price_ref_model:
        try:
            # First try exact match in same district
            query = price_ref_model.query.filter(
                price_ref_model.product_name.ilike(f"%{clean_name}%")
            )
            if district:
                dist_match = query.filter(price_ref_model.location.ilike(f"%{district}%")).first()
                if dist_match:
                    baseline_price_kg = dist_match.reference_price
                    data_source = f"{dist_match.source_name} ({dist_match.location})"
                    confidence = 90
            
            if not baseline_price_kg:
                any_match = query.first()
                if any_match:
                    baseline_price_kg = any_match.reference_price
                    data_source = f"{any_match.source_name} (Regional)"
                    confidence = 82
        except Exception:
            pass

    # Fallback to local commodity lookup
    if not baseline_price_kg:
        for key, info in DEFAULT_COMMODITY_BASELINES.items():
            if key in clean_name or clean_name in key:
                baseline_price_kg = info["base"]
                confidence = 80
                data_source = "Fictional Agmarknet Demo Baseline"
                break
                
    if not baseline_price_kg:
        baseline_price_kg = CATEGORY_DEFAULT_BASELINES.get(clean_category, 35.0)
        confidence = 65
        data_source = "Category Baseline Average (Fictional Demo Model)"

    # Base price for requested unit
    base_unit_price = baseline_price_kg * unit_multiplier

    # 2. Freshness Adjustment
    freshness_factor = 0.0
    freshness_explanation = "Freshness level standard for produce."
    today = date.today()
    
    if harvest_date:
        days_old = max(0, (today - harvest_date).days)
        if days_old <= 1:
            freshness_factor = +0.08  # +8% premium for ultra-fresh farm harvest
            freshness_explanation = "Fresh harvest (harvested within 24-48 hrs) earns an 8% quality premium."
        elif days_old <= 3:
            freshness_factor = +0.03
            freshness_explanation = "Very fresh produce (harvested 2-3 days ago), modest 3% premium."
        elif days_old >= 7 and clean_category in ["Vegetables", "Fruits"]:
            freshness_factor = -0.10
            freshness_explanation = "Produce harvested over a week ago; 10% markdown recommended for rapid clearance."
        else:
            freshness_explanation = f"Harvested {days_old} days ago; standard market tier applied."
    elif freshness_date:
        days_left = (freshness_date - today).days
        if days_left <= 2:
            freshness_factor = -0.15
            freshness_explanation = "Close to best-before date (<= 2 days); 15% clearance discount recommended."
        elif days_left >= 7:
            freshness_factor = +0.05
            freshness_explanation = "Extended shelf life available; +5% market confidence."

    # 3. Bulk Quantity Scale Adjustment
    bulk_factor = 0.0
    bulk_explanation = "Standard retail/wholesale lot size."
    effective_kg = quantity * unit_multiplier
    
    if effective_kg >= 1000:  # 1 tonne or more
        bulk_factor = -0.10
        bulk_explanation = "High wholesale volume (>= 1,000 kg). Bulk economies attract commercial and mandi buyers (-10%)."
    elif effective_kg >= 250:  # 250 kg to 999 kg
        bulk_factor = -0.05
        bulk_explanation = "Medium bulk volume (250-999 kg). Attracts restaurant and institutional buyers (-5%)."
    elif effective_kg <= 25:
        bulk_factor = +0.05
        bulk_explanation = "Direct retail micro-lot (<= 25 kg). Higher unit realization (+5%)."

    # 4. Regional Mandi Differential
    regional_factor = 0.0
    regional_explanation = "Standard regional pricing applied."
    if district:
        d_lower = district.lower()
        if any(metro in d_lower for metro in ["mumbai", "pune", "bengaluru", "delhi", "hyderabad", "chennai"]):
            regional_factor = +0.06
            regional_explanation = f"High-demand metro corridor ({district.title()}) commands +6% premium."
        elif any(rural in d_lower for rural in ["nashik", "sangli", "mandya", "guntur", "nagpur"]):
            regional_factor = -0.03
            regional_explanation = f"Primary production hub ({district.title()}); competitive sourcing rate (-3%)."

    # Combine multipliers
    total_multiplier = 1.0 + freshness_factor + bulk_factor + regional_factor
    recommended_price = round(max(base_unit_price * total_multiplier, 1.0), 2)
    
    min_price = round(max(recommended_price * 0.88, 1.0), 2)
    max_price = round(recommended_price * 1.15, 2)

    # Price comparison analysis if current price is provided
    comparison = None
    if current_price is not None and current_price > 0:
        diff_pct = round(((current_price - recommended_price) / recommended_price) * 100, 1)
        if abs(diff_pct) <= 5:
            comparison = {
                "status": "Optimal",
                "badge": "success",
                "message": f"Your price (₹{current_price}) is perfectly aligned with the AI benchmark."
            }
        elif diff_pct > 15:
            comparison = {
                "status": "Above Market",
                "badge": "warning",
                "message": f"Your price is {diff_pct}% above the benchmark. It may sell slower to wholesale buyers."
            }
        elif diff_pct > 5:
            comparison = {
                "status": "Slight Premium",
                "badge": "info",
                "message": f"Your price is {diff_pct}% above the benchmark. Ideal if produce is premium/organic."
            }
        else:
            comparison = {
                "status": "Competitive / Fast Sale",
                "badge": "success",
                "message": f"Your price is {abs(diff_pct)}% below average, which will attract rapid buyer orders."
            }

    factors = [
        {"name": "Base Reference", "impact": f"₹{base_unit_price:.2f}/{clean_unit}", "explanation": f"Sourced from {data_source}."},
        {"name": "Freshness Factor", "impact": f"{freshness_factor * 100:+.0f}%", "explanation": freshness_explanation},
        {"name": "Volume Scale", "impact": f"{bulk_factor * 100:+.0f}%", "explanation": bulk_explanation},
        {"name": "Regional Differential", "impact": f"{regional_factor * 100:+.0f}%", "explanation": regional_explanation}
    ]

    return {
        "product_name": product_name,
        "category": clean_category,
        "unit": clean_unit,
        "recommended_price": recommended_price,
        "price_range": {"min": min_price, "max": max_price},
        "confidence_percentage": confidence,
        "data_source": data_source,
        "factors": factors,
        "comparison": comparison,
        "is_simulated": True,
        "disclaimer": "Advisory benchmark calculated using synthetic demonstration baseline data and transparent heuristics. Farmers retain total control over final listing prices."
    }
