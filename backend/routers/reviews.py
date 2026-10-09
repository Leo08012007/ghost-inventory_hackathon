from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from backend.database import SessionLocal
from backend.models import ReviewModel, TransactionModel, UserModel
from backend.services.auth import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["Ratings & Reviews"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ReviewSubmitRequest(BaseModel):
    transaction_id: int
    rating: int  # 1 to 5
    comment: Optional[str] = None

class ReportReviewRequest(BaseModel):
    reason: str

@router.post("/submit")
def submit_review(
    payload: ReviewSubmitRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5 stars")

    tx = db.query(TransactionModel).filter(TransactionModel.id == payload.transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Eligibility check: Only buyer of transaction can review
    if tx.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the buyer associated with this transaction can submit a review")

    # Transaction status check: Only completed (Delivered) transactions can be reviewed
    if tx.status != "Delivered":
        raise HTTPException(status_code=400, detail="Reviews can only be submitted for completed/delivered transactions")

    # One review per transaction check
    existing = db.query(ReviewModel).filter(ReviewModel.transaction_id == tx.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="A review has already been submitted for this transaction")

    rev = ReviewModel(
        transaction_id=tx.id,
        buyer_id=current_user.id,
        seller_id=tx.seller_id,
        rating=payload.rating,
        comment=payload.comment,
        is_demo=False
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)

    return {
        "message": "Review submitted successfully",
        "review_id": rev.id,
        "rating": rev.rating
    }

@router.get("/seller/{seller_id}")
def get_seller_reviews(seller_id: int, db: Session = Depends(get_db)):
    reviews = db.query(ReviewModel).filter(
        ReviewModel.seller_id == seller_id,
        ReviewModel.is_reported == False
    ).order_by(ReviewModel.id.desc()).all()

    stats = db.query(
        func.avg(ReviewModel.rating).label("avg_rating"),
        func.count(ReviewModel.id).label("total_count")
    ).filter(
        ReviewModel.seller_id == seller_id,
        ReviewModel.is_reported == False
    ).first()

    avg_rating = round(float(stats.avg_rating), 1) if stats and stats.avg_rating else 5.0
    total_count = int(stats.total_count) if stats and stats.total_count else 0

    results = []
    for r in reviews:
        buyer = db.query(UserModel).filter(UserModel.id == r.buyer_id).first()
        comment_text = r.comment or ""
        if r.is_demo and "(Demo Review)" not in comment_text:
            comment_text += " (Demo Review)"

        results.append({
            "id": r.id,
            "rating": r.rating,
            "comment": comment_text,
            "is_demo": r.is_demo,
            "buyer_name": buyer.full_name if buyer else "Verified Industrial Buyer",
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return {
        "seller_id": seller_id,
        "average_rating": avg_rating,
        "total_reviews": total_count,
        "reviews": results
    }

@router.post("/{review_id}/report")
def report_review(
    review_id: int,
    payload: ReportReviewRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rev = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")

    rev.is_reported = True
    rev.report_reason = f"Reported by {current_user.email}: {payload.reason}"
    db.commit()

    return {"message": "Review reported to platform moderation team successfully"}
