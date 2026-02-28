from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi import UploadFile, File
from ai_modules.ocr import extract_text_from_image
import numpy as np
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal, engine, Base
from models import PartModel
from ai_modules.matcher import find_best_matches

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request Models
class Part(BaseModel):
    part_name: str
    material: str
    size: str
    base_price: float
    seller_name: str

class SearchRequest(BaseModel):
    query: str
    urgency_level: int

@app.get("/")
def read_root():
    return {"message": "Ghost Inventory API Running 🚀"}

@app.post("/upload")
def upload_part(part: Part, db: Session = Depends(get_db)):
    db_part = PartModel(
        part_name=part.part_name,
        material=part.material,
        size=part.size,
        base_price=part.base_price,
        seller_name=part.seller_name
    )
    db.add(db_part)
    db.commit()
    db.refresh(db_part)

    return {"message": "Part stored securely"}

@app.post("/search")
def search_part(request: SearchRequest, db: Session = Depends(get_db)):
    parts = db.query(PartModel).all()

    part_names = [item.part_name for item in parts]

    matched_indices = find_best_matches(request.query, part_names)

    matches = []

    for idx in matched_indices:
        item = parts[idx]

        downtime_factor = 50
        suggested_price = item.base_price + (
            request.urgency_level * downtime_factor
        )

        matches.append({
    "part_id": item.id,
    "part_name": item.part_name,
    "material": item.material,
    "size": item.size,
    "suggested_price": suggested_price
})

    return {"matches": matches}
import cv2
import numpy as np

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    image_bytes = await file.read()

    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)

    # Decode image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    extracted_text = extract_text_from_image(img)

    return {
        "detected_text": extracted_text
    }
class ConfirmRequest(BaseModel):
    part_id: int

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
