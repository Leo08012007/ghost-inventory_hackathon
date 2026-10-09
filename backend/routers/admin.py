import os
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Response, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import SessionLocal
from backend.models import UserModel, SellerProfileModel, PartModel, ProductVerificationRecordModel
from backend.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/admin", tags=["Admin Verification & Management"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SellerVerifyRequest(BaseModel):
    status: str  # Verified, Rejected, Under Review, Pending
    notes: Optional[str] = None
    checklist: Optional[dict] = None  # e.g. {"gstin_check": true, "address_check": true}

class ProductVerifyRequest(BaseModel):
    status: str  # Verified, Rejected, Pending Inspection, Unverified
    notes: Optional[str] = None

@router.get("/sellers")
def list_seller_applications(
    status_filter: Optional[str] = None,
    current_user: UserModel = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    query = db.query(SellerProfileModel)
    if status_filter:
        query = query.filter(SellerProfileModel.verification_status == status_filter)
    
    sellers = query.order_by(SellerProfileModel.created_at.desc()).all()
    
    results = []
    for s in sellers:
        checklist = {}
        if s.review_checklist_json:
            try:
                checklist = json.loads(s.review_checklist_json)
            except Exception:
                pass
                
        results.append({
            "id": s.id,
            "user_id": s.user_id,
            "company_name": s.company_name,
            "representative_name": s.representative_name,
            "business_email": s.business_email,
            "phone_number": s.phone_number,
            "business_address": s.business_address,
            "city": s.city,
            "state": s.state,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "registration_type": s.registration_type,
            "registration_number": s.registration_number,
            "has_certificate": bool(s.certificate_path and os.path.exists(s.certificate_path)),
            "certificate_filename": os.path.basename(s.certificate_path) if s.certificate_path else None,
            "business_description": s.business_description,
            "verification_status": s.verification_status,
            "is_demo_verified": s.is_demo_verified,
            "verification_notes": s.verification_notes,
            "review_checklist": checklist,
            "verified_at": s.verified_at.isoformat() if s.verified_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None
        })
    return {"sellers": results}

@router.post("/sellers/{seller_id}/verify")
def verify_seller(
    seller_id: int,
    payload: SellerVerifyRequest,
    current_user: UserModel = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    profile = db.query(SellerProfileModel).filter(SellerProfileModel.id == seller_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found")

    valid_statuses = ["Verified", "Rejected", "Under Review", "Pending"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    profile.verification_status = payload.status
    profile.verification_notes = payload.notes
    profile.verified_by_id = current_user.id
    profile.verified_at = datetime.utcnow()
    
    if payload.checklist:
        profile.review_checklist_json = json.dumps(payload.checklist)

    db.commit()
    db.refresh(profile)

    return {
        "message": f"Seller verification status updated to '{profile.verification_status}'",
        "seller_id": profile.id,
        "status": profile.verification_status,
        "reviewer": current_user.full_name,
        "verified_at": profile.verified_at.isoformat()
    }

@router.get("/certificate/{filename}")
def download_certificate_file(
    filename: str,
    current_user: UserModel = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    # Security check: sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join("uploads", "certificates", safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Certificate document not found")

    return FileResponse(file_path, filename=safe_filename)

@router.get("/products")
def list_products_admin(
    status_filter: Optional[str] = None,
    current_user: UserModel = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    query = db.query(PartModel)
    if status_filter:
        query = query.filter(PartModel.verification_status == status_filter)
        
    parts = query.order_by(PartModel.id.desc()).all()
    results = []
    for p in parts:
        results.append({
            "id": p.id,
            "part_name": p.part_name,
            "manufacturer": p.manufacturer,
            "model_number": p.model_number,
            "part_number": p.part_number,
            "condition": p.condition,
            "base_price": p.base_price,
            "seller_name": p.seller_name,
            "location_city": p.location_city,
            "verification_status": p.verification_status or "Unverified"
        })
    return {"products": results}

@router.post("/products/{part_id}/verify")
def verify_product(
    part_id: int,
    payload: ProductVerifyRequest,
    current_user: UserModel = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    part = db.query(PartModel).filter(PartModel.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Product not found")

    valid_statuses = ["Verified", "Rejected", "Pending Inspection", "Unverified"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    part.verification_status = payload.status
    
    rec = ProductVerificationRecordModel(
        part_id=part.id,
        status=payload.status,
        reviewer_id=current_user.id,
        review_notes=payload.notes
    )
    db.add(rec)
    db.commit()
    db.refresh(part)

    return {
        "message": f"Product verification status updated to '{part.verification_status}'",
        "part_id": part.id,
        "verification_status": part.verification_status,
        "reviewer": current_user.full_name
    }
