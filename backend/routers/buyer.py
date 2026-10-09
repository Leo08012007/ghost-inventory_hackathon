from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from backend.database import SessionLocal
from backend.models import PartModel, SellerProfileModel, UserModel, ReviewModel
from backend.services.geo import haversine_distance
from backend.services.pricing import calculate_suggested_price
from backend.ai_modules.matcher import find_best_matches_with_scores

router = APIRouter(prefix="/api/buyer", tags=["Buyer Marketplace"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class BuyerSearchRequest(BaseModel):
    query: str
    urgency_level: int = 1
    quantity_required: Optional[int] = 1
    buyer_lat: Optional[float] = None
    buyer_lon: Optional[float] = None
    buyer_location_name: Optional[str] = None
    search_radius_km: Optional[float] = None
    required_delivery_days: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    condition: Optional[str] = None
    verification_filter: Optional[str] = None  # verified_only, all

@router.post("/search")
def buyer_search_marketplace(payload: BuyerSearchRequest, db: Session = Depends(get_db)):
    query_str = payload.query.strip()
    urgency = max(1, min(5, payload.urgency_level))
    qty_req = payload.quantity_required or 1

    # Fetch parts matching basic availability criteria
    parts_query = db.query(PartModel)
    
    if payload.min_price is not None:
        parts_query = parts_query.filter(PartModel.base_price >= payload.min_price)
    if payload.max_price is not None:
        parts_query = parts_query.filter(PartModel.base_price <= payload.max_price)
    if payload.condition:
        parts_query = parts_query.filter(PartModel.condition == payload.condition)

    all_parts = parts_query.all()
    if not all_parts:
        return {"matches": [], "total": 0}

    # Prepare item structures for matcher
    item_list = []
    for p in all_parts:
        item_list.append({
            "part_name": p.part_name or "",
            "model_number": p.model_number or "",
            "part_number": p.part_number or "",
            "manufacturer": p.manufacturer or "",
            "material": p.material or "",
            "size": p.size or "",
            "description": p.description or ""
        })

    # Run semantic AI matcher
    matched_tuples = find_best_matches_with_scores(query_str, item_list, threshold=0.50)

    # Compute actual ratings dynamically from ReviewModel per seller
    seller_ratings = {}
    reviews_all = db.query(
        ReviewModel.seller_id,
        func.avg(ReviewModel.rating).label("avg_rating"),
        func.count(ReviewModel.id).label("count")
    ).group_by(ReviewModel.seller_id).all()
    
    for r in reviews_all:
        if r.seller_id:
            seller_ratings[r.seller_id] = {
                "avg_rating": round(float(r.avg_rating), 1),
                "count": int(r.count)
            }

    results = []
    for idx, score, raw_explanation in matched_tuples:
        part = all_parts[idx]

        # Quantity filter: exclude if insufficient stock
        avail_qty = part.available_quantity if part.available_quantity is not None else 1
        if avail_qty < qty_req:
            continue

        # Get seller verification details
        seller_user = db.query(UserModel).filter(UserModel.id == part.seller_id).first() if part.seller_id else None
        seller_profile = seller_user.seller_profile if seller_user else None

        seller_ver_status = seller_profile.verification_status if seller_profile else "Pending"
        is_demo_ver = seller_profile.is_demo_verified if seller_profile else False

        if payload.verification_filter == "verified_only":
            if seller_ver_status != "Verified":
                continue

        # Calculate Haversine distance
        part_lat = part.latitude or (seller_profile.latitude if seller_profile else None)
        part_lon = part.longitude or (seller_profile.longitude if seller_profile else None)
        
        dist_km = haversine_distance(payload.buyer_lat, payload.buyer_lon, part_lat, part_lon)

        # Radius filter
        if payload.search_radius_km and dist_km is not None:
            if dist_km > payload.search_radius_km:
                continue

        # Pricing suggestion (calculated separately for each listing from its own base_price)
        pricing = calculate_suggested_price(part.base_price, urgency)

        # Delivery feasibility calculation
        dispatch_days = part.estimated_dispatch_days or 1
        meets_deadline = True
        if payload.required_delivery_days is not None:
            if dispatch_days > payload.required_delivery_days:
                meets_deadline = False

        # Dynamic Seller rating lookup
        s_rating_data = seller_ratings.get(part.seller_id, {"avg_rating": 4.0, "count": 0}) if part.seller_id else {"avg_rating": 4.0, "count": 0}

        # Format seller verification badge label
        badge_label = "Unverified Seller"
        if seller_ver_status == "Verified":
            badge_label = "DEMO VERIFIED" if is_demo_ver else "Verified Seller"
        elif seller_ver_status == "Pending":
            badge_label = "VERIFICATION PENDING"
        elif seller_ver_status == "Under Review":
            badge_label = "UNDER REVIEW"
        elif seller_ver_status == "Rejected":
            badge_label = "REJECTED"

        # Generate realistic match explanation string
        explanation_parts = []
        if seller_ver_status == "Verified":
            explanation_parts.append(f"Recommended: Verified seller ({s_rating_data['avg_rating']}★ rating, {s_rating_data['count']} reviews)")
        elif seller_ver_status == "Pending":
            explanation_parts.append("Verification pending review")
        else:
            explanation_parts.append("Unverified supplier listing")

        if dist_km is not None:
            explanation_parts.append(f"{dist_km} km away")
        explanation_parts.append(f"Est. dispatch: {dispatch_days} day(s)")

        final_explanation = " · ".join(explanation_parts)

        # Check for primary product image if uploaded
        primary_img = None
        if part.images and len(part.images) > 0:
            primary_img = part.images[0].image_path

        card = {
            "part_id": part.id,
            "part_name": part.part_name,
            "material": part.material or "Industrial Spec",
            "size": part.size or "Standard Spec",
            "manufacturer": part.manufacturer or "OEM Manufacturer",
            "model_number": part.model_number or "N/A",
            "part_number": part.part_number or "N/A",
            "condition": part.condition or "New",
            "description": part.description or "Industrial spare part listing.",
            "base_price": part.base_price,
            "suggested_price": pricing["suggested_price"],
            "urgency_level": urgency,
            "available_quantity": avail_qty,
            "seller_name": part.seller_name or "Industrial Exchange Member",
            "seller_id": part.seller_id,
            "seller_verification_status": seller_ver_status,
            "seller_verification_badge": badge_label,
            "product_verification_status": part.verification_status or "Unverified",
            "distance_km": dist_km,
            "distance_label": f"{dist_km} km away" if dist_km is not None else "Location upon agreement",
            "estimated_dispatch_days": dispatch_days,
            "estimated_delivery_label": f"Est. Dispatch: {dispatch_days} day(s)",
            "meets_deadline": meets_deadline,
            "seller_avg_rating": s_rating_data["avg_rating"],
            "seller_review_count": s_rating_data["count"],
            "last_stock_confirmed_at": part.last_stock_confirmed_at.isoformat() if part.last_stock_confirmed_at else None,
            "match_score": round(score, 2),
            "match_explanation": final_explanation,
            "primary_image": primary_img
        }
        results.append(card)

    # SECTION 6 RANKING LOGIC:
    # 1. Filter out incompatible/unavailable (already done)
    # 2. Sort primarily by match relevance score (highest first)
    # 3. Prioritize deadline feasibility (meets_deadline)
    # 4. Prefer verified sellers (seller_verification_status == "Verified")
    # 5. Sort by seller rating, distance, and price
    def rank_sort_key(item):
        match_score = -item["match_score"]  # primary sorting by relevance
        deadline_penalty = 0 if item["meets_deadline"] else 1000
        verified_bonus = 0 if item["seller_verification_status"] == "Verified" else 100
        dist_val = item["distance_km"] if item["distance_km"] is not None else 9999
        rating_score = -item["seller_avg_rating"]
        price_val = item["base_price"]
        return (match_score, deadline_penalty, verified_bonus, rating_score, dist_val, price_val)

    results.sort(key=rank_sort_key)
    return {"matches": results, "total": len(results)}
