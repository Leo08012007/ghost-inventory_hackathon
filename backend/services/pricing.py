from typing import Dict, Any, Optional

DEFAULT_URGENCY_RATE = 50.0  # ₹50 per urgency level baseline

def calculate_suggested_price(
    base_price: float,
    urgency_level: int,
    urgency_rate: float = DEFAULT_URGENCY_RATE
) -> Dict[str, Any]:
    """
    Calculate urgency-adjusted suggested price based on transparent baseline formula:
    suggested_price = base_price + (urgency_level * urgency_rate)
    
    Validates urgency_level between 1 and 5.
    Returns dictionary with breakdown for transparent buyer/seller visibility.
    """
    # Clamp and validate urgency_level
    clamped_urgency = max(1, min(5, int(urgency_level)))
    
    price = float(base_price) if base_price is not None else 0.0
    urgency_premium = clamped_urgency * urgency_rate
    suggested_price = round(price + urgency_premium, 2)
    
    return {
        "base_price": price,
        "urgency_level": clamped_urgency,
        "urgency_rate": urgency_rate,
        "urgency_premium": urgency_premium,
        "suggested_price": suggested_price,
        "is_ml_predicted": False,  # Explicitly transparent that this is baseline rule
        "label": "Urgency-adjusted suggested price"
    }

def estimate_market_price_ml_stub(
    base_price: float,
    urgency_level: int,
    historical_features: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Extensible stub for future trained regression pricing models.
    Falls back to transparent baseline pricing engine.
    """
    return calculate_suggested_price(base_price, urgency_level)
