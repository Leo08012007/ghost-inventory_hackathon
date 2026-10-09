from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import SessionLocal
from backend.models import (
    TransactionModel, TransactionStatusHistoryModel, 
    PartModel, UserModel, ReviewModel
)
from backend.services.auth import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["Transactions Workflow"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TransactionCreateRequest(BaseModel):
    part_id: int
    quantity: int = 1
    urgency_level: int = 1
    delivery_address: Optional[str] = None
    buyer_latitude: Optional[float] = None
    buyer_longitude: Optional[float] = None
    required_delivery_days: Optional[int] = None

class StatusUpdateRequest(BaseModel):
    status: str  # Requested, Seller Confirmed, Accepted, Dispatched, Delivered, Cancelled, Disputed
    notes: Optional[str] = None

@router.post("/request")
def create_transaction_request(
    payload: TransactionCreateRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    part = db.query(PartModel).filter(PartModel.id == payload.part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Product not found")

    if part.available_quantity and part.available_quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds available stock")

    # Seller user lookup
    seller_id = part.seller_id
    if not seller_id:
        # Fallback: link to default seller if part was created via old endpoint
        seller_user = db.query(UserModel).filter(UserModel.role == "seller").first()
        seller_id = seller_user.id if seller_user else current_user.id

    if seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot purchase your own listed product")

    # Calculate price based on urgency
    downtime_factor = 50.0
    suggested_price = part.base_price + (payload.urgency_level * downtime_factor)
    total_agreed = suggested_price * payload.quantity

    tx = TransactionModel(
        buyer_id=current_user.id,
        seller_id=seller_id,
        part_id=part.id,
        quantity=payload.quantity,
        agreed_price=round(total_agreed, 2),
        status="Requested",
        delivery_address=payload.delivery_address,
        buyer_latitude=payload.buyer_latitude,
        buyer_longitude=payload.buyer_longitude,
        required_delivery_days=payload.required_delivery_days,
        urgency_level=payload.urgency_level,
        stock_confirmed_by_seller=False
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    # Status history entry
    hist = TransactionStatusHistoryModel(
        transaction_id=tx.id,
        status="Requested",
        notes=f"Buyer initiated transaction for {payload.quantity} unit(s).",
        created_by_id=current_user.id
    )
    db.add(hist)
    db.commit()

    return {
        "message": "Transaction request created successfully. Awaiting seller stock confirmation.",
        "transaction_id": tx.id,
        "status": tx.status,
        "agreed_price": tx.agreed_price
    }

@router.get("/my-transactions")
def get_my_transactions(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "buyer":
        txs = db.query(TransactionModel).filter(TransactionModel.buyer_id == current_user.id).order_by(TransactionModel.id.desc()).all()
    elif current_user.role == "seller":
        txs = db.query(TransactionModel).filter(TransactionModel.seller_id == current_user.id).order_by(TransactionModel.id.desc()).all()
    else:  # Admin
        txs = db.query(TransactionModel).order_by(TransactionModel.id.desc()).all()

    results = []
    for t in txs:
        part = t.part
        buyer_user = t.buyer
        seller_user = t.seller
        seller_prof = seller_user.seller_profile if seller_user else None

        # Reveal contact details ONLY if transaction is in 'Seller Confirmed', 'Accepted', 'Dispatched', 'Delivered'
        reveal_contact = t.status in ["Seller Confirmed", "Accepted", "Dispatched", "Delivered"]
        
        seller_contact_info = None
        if reveal_contact and seller_user:
            seller_contact_info = {
                "seller_name": part.seller_name or seller_user.company_name or seller_user.full_name,
                "company_name": seller_user.company_name,
                "phone": seller_user.phone,
                "email": seller_user.email,
                "address": seller_prof.business_address if seller_prof else "Location details available"
            }

        # Review state check
        existing_review = db.query(ReviewModel).filter(ReviewModel.transaction_id == t.id).first()

        results.append({
            "id": t.id,
            "part_id": t.part_id,
            "part_name": part.part_name if part else "Industrial Component",
            "quantity": t.quantity,
            "agreed_price": t.agreed_price,
            "status": t.status,
            "stock_confirmed_by_seller": t.stock_confirmed_by_seller,
            "delivery_address": t.delivery_address,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "buyer_name": buyer_user.full_name if buyer_user else "Buyer",
            "seller_contact_info": seller_contact_info,
            "is_review_eligible": (t.status == "Delivered" and not existing_review and current_user.role == "buyer" and current_user.id == t.buyer_id),
            "has_reviewed": bool(existing_review)
        })

    return {"transactions": results}

@router.post("/{transaction_id}/confirm-stock")
def seller_confirm_stock(
    transaction_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if current_user.role != "admin" and tx.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to confirm stock for this transaction")

    tx.stock_confirmed_by_seller = True
    tx.status = "Seller Confirmed"
    tx.part.last_stock_confirmed_at = datetime.utcnow()

    hist = TransactionStatusHistoryModel(
        transaction_id=tx.id,
        status="Seller Confirmed",
        notes="Seller confirmed stock availability. Seller contact info revealed to buyer.",
        created_by_id=current_user.id
    )
    db.add(hist)
    db.commit()

    return {
        "message": "Stock confirmed by seller. Transaction updated to 'Seller Confirmed'.",
        "transaction_id": tx.id,
        "status": tx.status
    }

@router.post("/{transaction_id}/update-status")
def update_transaction_status(
    transaction_id: int,
    payload: StatusUpdateRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Authorization check
    is_buyer = (current_user.id == tx.buyer_id)
    is_seller = (current_user.id == tx.seller_id)
    is_admin = (current_user.role == "admin")

    if not (is_buyer or is_seller or is_admin):
        raise HTTPException(status_code=403, detail="Unauthorized to update this transaction")

    valid_statuses = ["Requested", "Seller Confirmed", "Accepted", "Dispatched", "Delivered", "Cancelled", "Disputed"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    tx.status = payload.status
    tx.updated_at = datetime.utcnow()

    hist = TransactionStatusHistoryModel(
        transaction_id=tx.id,
        status=payload.status,
        notes=payload.notes or f"Status updated by {current_user.full_name} ({current_user.role})",
        created_by_id=current_user.id
    )
    db.add(hist)
    db.commit()

    return {
        "message": f"Transaction status updated to '{tx.status}'",
        "transaction_id": tx.id,
        "status": tx.status
    }
