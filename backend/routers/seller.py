import os
import uuid
import cv2
import numpy as np
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import SessionLocal
from backend.models import PartModel, ProductImageModel, UserModel
from backend.services.auth import get_current_user, require_roles
from backend.ai_modules.ocr import extract_text_from_image, extract_structured_ocr

router = APIRouter(prefix="/api/products", tags=["Seller Products & OCR"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PartCreateRequest(BaseModel):
    part_name: str
    material: Optional[str] = "Steel"
    size: Optional[str] = "Standard"
    base_price: float
    seller_name: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    part_number: Optional[str] = None
    condition: Optional[str] = "New"
    available_quantity: Optional[int] = 1
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    estimated_dispatch_days: Optional[int] = 1

@router.post("/ocr-preview")
async def ocr_label_preview(file: UploadFile = File(...)):
    """Extract label text using EasyOCR and return parsed text for seller inspection/edit preview."""
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Image file is required")

    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image format")

    ocr_result = extract_structured_ocr(img)
    return {
        "message": "OCR text extracted successfully",
        "detected_text": ocr_result["text"],
        "words": ocr_result["words"],
        "details": ocr_result["details"]
    }

@router.post("/create")
async def create_product_listing(
    part_name: str = Form(...),
    base_price: float = Form(...),
    material: Optional[str] = Form("Steel"),
    size: Optional[str] = Form("Standard"),
    description: Optional[str] = Form(None),
    manufacturer: Optional[str] = Form(None),
    model_number: Optional[str] = Form(None),
    part_number: Optional[str] = Form(None),
    condition: Optional[str] = Form("New"),
    available_quantity: Optional[int] = Form(1),
    location_city: Optional[str] = Form(None),
    location_state: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    estimated_dispatch_days: Optional[int] = Form(1),
    images: List[UploadFile] = File([]),
    current_user: UserModel = Depends(require_roles(["seller", "admin"])),
    db: Session = Depends(get_db)
):
    seller_org = current_user.company_name or current_user.full_name
    
    # Auto fill location from seller profile if missing
    if current_user.seller_profile:
        sp = current_user.seller_profile
        location_city = location_city or sp.city
        location_state = location_state or sp.state
        latitude = latitude if latitude is not None else sp.latitude
        longitude = longitude if longitude is not None else sp.longitude

    part = PartModel(
        part_name=part_name,
        material=material,
        size=size,
        base_price=base_price,
        seller_name=seller_org,
        seller_id=current_user.id,
        description=description,
        manufacturer=manufacturer,
        model_number=model_number,
        part_number=part_number,
        condition=condition,
        available_quantity=available_quantity,
        location_city=location_city,
        location_state=location_state,
        latitude=latitude,
        longitude=longitude,
        estimated_dispatch_days=estimated_dispatch_days,
        last_stock_confirmed_at=datetime.utcnow(),
        verification_status="Unverified"
    )
    db.add(part)
    db.commit()
    db.refresh(part)

    # Handle image uploads
    saved_images = []
    os.makedirs("uploads/products", exist_ok=True)
    for idx, img_file in enumerate(images):
        if img_file and img_file.filename:
            ext = os.path.splitext(img_file.filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                fname = f"prod_{part.id}_{uuid.uuid4().hex[:8]}{ext}"
                fpath = os.path.join("uploads", "products", fname)
                img_bytes = await img_file.read()
                with open(fpath, "wb") as f:
                    f.write(img_bytes)
                
                prod_img = ProductImageModel(
                    part_id=part.id,
                    image_path=f"static/uploads/products/{fname}",
                    is_primary=(idx == 0)
                )
                db.add(prod_img)
                saved_images.append(prod_img.image_path)

    db.commit()

    return {
        "message": "Part listing created successfully",
        "part_id": part.id,
        "part_name": part.part_name,
        "base_price": part.base_price,
        "images": saved_images
    }

@router.get("/my-listings")
def get_my_listings(
    current_user: UserModel = Depends(require_roles(["seller", "admin"])),
    db: Session = Depends(get_db)
):
    parts = db.query(PartModel).filter(PartModel.seller_id == current_user.id).order_by(PartModel.id.desc()).all()
    results = []
    for p in parts:
        results.append({
            "id": p.id,
            "part_name": p.part_name,
            "material": p.material,
            "size": p.size,
            "base_price": p.base_price,
            "manufacturer": p.manufacturer,
            "model_number": p.model_number,
            "part_number": p.part_number,
            "condition": p.condition,
            "available_quantity": p.available_quantity,
            "verification_status": p.verification_status or "Unverified",
            "last_stock_confirmed_at": p.last_stock_confirmed_at.isoformat() if p.last_stock_confirmed_at else None
        })
    return {"listings": results}

@router.post("/{part_id}/confirm-stock")
def confirm_part_stock(
    part_id: int,
    current_user: UserModel = Depends(require_roles(["seller", "admin"])),
    db: Session = Depends(get_db)
):
    part = db.query(PartModel).filter(PartModel.id == part_id, PartModel.seller_id == current_user.id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized")

    part.last_stock_confirmed_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Stock confirmation timestamp updated successfully",
        "part_id": part.id,
        "last_stock_confirmed_at": part.last_stock_confirmed_at.isoformat()
    }
