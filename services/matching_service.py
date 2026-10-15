"""
Smart Farmer-Buyer Matching Engine
Ranks suitable farmer listings for buyer needs based on multi-dimensional compatibility:
- Product relevance
- Quantity & stock sufficiency
- Geographic / district proximity
- Buyer persona requirements (Restaurant vs Wholesaler vs Retailer vs Consumer)
- Freshness & shelf life
- Price competitiveness
"""

from typing import List, Dict, Any, Optional
from datetime import date


def calculate_match_score(
    product,
    buyer,
    required_quantity: Optional[float] = None,
    max_budget_per_unit: Optional[float] = None,
    preferred_category: Optional[str] = None,
    search_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes a match score (0-100) and rationale for a single product listing relative to a buyer.
    """
    score = 0.0
    reasons = []
    
    # 1. Product Relevance (up to 30 pts)
    relevance_pts = 0
    if search_query:
        q = search_query.strip().lower()
        p_name = product.name.lower()
        p_cat = product.category.lower()
        if q == p_name:
            relevance_pts = 30
            reasons.append(f"Exact match for '{product.name}'")
        elif q in p_name or any(w in p_name for w in q.split()):
            relevance_pts = 26
            reasons.append(f"Strong name match for '{product.name}'")
        elif q in p_cat:
            relevance_pts = 20
            reasons.append(f"Category match ({product.category})")
        else:
            relevance_pts = 5
    elif preferred_category:
        if preferred_category.lower() == product.category.lower():
            relevance_pts = 30
            reasons.append(f"Category matches your preference ({product.category})")
        else:
            relevance_pts = 10
    else:
        # Default relevance if browsing all
        relevance_pts = 25

    score += relevance_pts

    # 2. Stock and Quantity Sufficiency (up to 25 pts)
    stock_pts = 0
    req_qty = required_quantity if (required_quantity and required_quantity > 0) else None
    
    if req_qty:
        if product.quantity >= req_qty:
            stock_pts = 25
            ratio = product.quantity / req_qty
            if ratio < 1.5:
                reasons.append(f"Exact stock match ({product.quantity} {product.unit} available for {req_qty} {product.unit} order)")
            else:
                reasons.append(f"Surplus capacity ({product.quantity} {product.unit} available)")
        else:
            pct_fulfillable = (product.quantity / req_qty) * 100
            stock_pts = max(5, int(20 * (product.quantity / req_qty)))
            reasons.append(f"Partial lot ({product.quantity} {product.unit} available, {pct_fulfillable:.0f}% of need)")
    else:
        # General stock availability
        if product.quantity > 50:
            stock_pts = 25
            reasons.append("Ample stock available")
        elif product.quantity > 10:
            stock_pts = 20
        else:
            stock_pts = 10
            reasons.append("Limited stock remaining")

    score += stock_pts

    # 3. Location / District Proximity (up to 20 pts)
    loc_pts = 0
    buyer_district = (buyer.district or "").strip().lower() if buyer else ""
    product_district = (product.district or product.location or "").strip().lower()
    
    if buyer_district and product_district:
        if buyer_district in product_district or product_district in buyer_district:
            loc_pts = 20
            reasons.append(f"Direct local sourcing within your district ({buyer.district.title()})")
        else:
            loc_pts = 8
            reasons.append("Regional dispatch available")
    else:
        loc_pts = 12

    score += loc_pts

    # 4. Buyer Persona Alignment (up to 15 pts)
    persona_pts = 0
    business_type = (buyer.business_type or "consumer").lower() if buyer else "consumer"
    
    if business_type == "restaurant":
        # Restaurants value harvest freshness and medium bulk
        days_old = product.days_since_harvest
        if days_old is not None and days_old <= 2:
            persona_pts = 15
            reasons.append("Peak kitchen freshness (harvested within 48h)")
        elif product.quantity >= 20:
            persona_pts = 12
            reasons.append("Optimal batch size for daily restaurant prep")
        else:
            persona_pts = 8

    elif business_type == "wholesaler":
        # Wholesalers value massive volume and unit rates
        if product.quantity >= 200 or product.unit in ["quintal", "tonne"]:
            persona_pts = 15
            reasons.append("Wholesale-scale lot suitable for bulk distribution")
        elif product.quantity >= 50:
            persona_pts = 10
        else:
            persona_pts = 5

    elif business_type == "retailer":
        # Retailers value steady lot sizes and clean grading
        if 20 <= product.quantity <= 300:
            persona_pts = 15
            reasons.append("Pack size suited for retail grocery shelving")
        else:
            persona_pts = 10

    else:  # Consumer
        if product.quantity >= 1:
            persona_pts = 14
            reasons.append("Farm-direct home consumer quantity")
        else:
            persona_pts = 8

    score += persona_pts

    # 5. Price & Budget Feasibility (up to 10 pts)
    price_pts = 0
    eff_price = product.effective_price
    if max_budget_per_unit and max_budget_per_unit > 0:
        if eff_price <= max_budget_per_unit:
            price_pts = 10
            diff = max_budget_per_unit - eff_price
            if diff > 0:
                reasons.append(f"Within budget (₹{diff:.2f} below your limit)")
            else:
                reasons.append("Exactly within target budget")
        else:
            price_pts = max(1, 10 - int(((eff_price - max_budget_per_unit) / max_budget_per_unit) * 10))
            reasons.append("Priced slightly above preferred budget")
    else:
        if product.is_surplus and product.discount_percentage > 0:
            price_pts = 10
            reasons.append(f"Special surplus deal ({product.discount_percentage:.0f}% off)")
        else:
            price_pts = 8

    score += price_pts

    # Bound score between 0 and 100
    final_score = int(min(100, max(0, score)))
    
    # Generate unified summary explanation
    explanation = "; ".join(reasons[:3]) if reasons else "Good general product match."

    return {
        "score": final_score,
        "reasons": reasons,
        "explanation": explanation,
        "is_bulk_suitable": product.quantity >= 50 or product.unit in ["quintal", "tonne"]
    }


def rank_products_for_buyer(
    products: List[Any],
    buyer: Optional[Any],
    required_quantity: Optional[float] = None,
    max_budget_per_unit: Optional[float] = None,
    preferred_category: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 12
) -> List[Dict[str, Any]]:
    """
    Ranks available products by match score for a given buyer.
    """
    scored_products = []
    
    for prod in products:
        if not prod.is_available or prod.quantity <= 0:
            continue
            
        match_data = calculate_match_score(
            product=prod,
            buyer=buyer,
            required_quantity=required_quantity,
            max_budget_per_unit=max_budget_per_unit,
            preferred_category=preferred_category,
            search_query=search_query
        )
        
        scored_products.append({
            "product": prod,
            "match_score": match_data["score"],
            "reasons": match_data["reasons"],
            "explanation": match_data["explanation"],
            "is_bulk_suitable": match_data["is_bulk_suitable"]
        })
        
    scored_products.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_products[:limit]
