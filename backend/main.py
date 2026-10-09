import os
import cv2
import numpy as np
from fastapi import FastAPI, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import SessionLocal, engine, Base, init_and_migrate_db
from backend.models import PartModel
from backend.ai_modules.ocr import extract_text_from_image
from backend.ai_modules.matcher import find_best_matches

# Import modular API routers
from backend.routers import auth, admin, buyer, seller, transactions, reviews

# Run DB migration and initialization
init_and_migrate_db()

app = FastAPI(
    title="Ghost Inventory Platform API",
    description="Trust-Based Industrial Spare Parts Exchange with AI Matching & Confidential Trading",
    version="2.0.0"
)

# Mount static file directory for uploaded product images
os.makedirs("uploads/products", exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory="uploads"), name="static_uploads")

# Mount Jinja2 templates
templates = Jinja2Templates(directory="backend/templates")

# Include Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(buyer.router)
app.include_router(seller.router)
app.include_router(transactions.router)
app.include_router(reviews.router)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# PRESERVED ORIGINAL ROUTES AND DATA CONTRACTS
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/health")
def read_root():
    return {"message": "Ghost Inventory API Running 🚀"}

# Preserved Pydantic Models for original contracts
class Part(BaseModel):
    part_name: str
    material: str
    size: str
    base_price: float
    seller_name: str

class SearchRequest(BaseModel):
    query: str
    urgency_level: int

class ConfirmRequest(BaseModel):
    part_id: int

@app.post("/upload")
def upload_part(part: Part, db: Session = Depends(get_db)):
    db_part = PartModel(
        part_name=part.part_name,
        material=part.material,
        size=part.size,
        base_price=part.base_price,
        seller_name=part.seller_name,
        verification_status="Unverified"
    )
    db.add(db_part)
    db.commit()
    db.refresh(db_part)

    return {"message": "Part stored securely", "part_id": db_part.id}

@app.post("/search")
def search_part(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Preserved /search endpoint contract enhanced with full location, pricing, 
    and matching intelligence.
    """
    from backend.routers.buyer import buyer_search_marketplace, BuyerSearchRequest
    
    # Bridge to enhanced search service while supporting exact legacy response
    req = BuyerSearchRequest(
        query=request.query,
        urgency_level=request.urgency_level
    )
    search_res = buyer_search_marketplace(req, db)
    return search_res

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    extracted_text = extract_text_from_image(img)

    new_part = PartModel(
        part_name=extracted_text,
        material="Unknown",
        size="Unknown",
        base_price=500.0,
        seller_name="Image Seller",
        verification_status="Unverified"
    )

    db.add(new_part)
    db.commit()
    db.refresh(new_part)

    return {
        "message": "Part stored successfully from image",
        "detected_text": extracted_text,
        "part_id": new_part.id
    }

@app.post("/confirm-deal")
def confirm_deal(request: ConfirmRequest, db: Session = Depends(get_db)):
    part = db.query(PartModel).filter(PartModel.id == request.part_id).first()

    if not part:
        return {"error": "Part not found"}

    return {
        "message": "Deal confirmed. Seller details revealed.",
        "seller_name": part.seller_name,
        "part_name": part.part_name
    }
