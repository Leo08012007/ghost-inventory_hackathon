import os
import uuid
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.database import SessionLocal
from backend.models import UserModel, SellerProfileModel
from backend.services.auth import (
    hash_password, verify_password, create_session_token, 
    get_current_user, get_current_user_optional, SESSION_COOKIE_NAME
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LoginRequest(BaseModel):
    email: str
    password: str

class BuyerRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None

@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == payload.email.strip().lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_session_token(user.id, user.role)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_name": user.company_name
        }
    }

@router.post("/register/buyer")
def register_buyer(payload: BuyerRegisterRequest, response: Response, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    existing = db.query(UserModel).filter(UserModel.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = UserModel(
        email=email_clean,
        password_hash=hash_password(payload.password),
        role="buyer",
        full_name=payload.full_name,
        company_name=payload.company_name,
        phone=payload.phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session_token(user.id, user.role)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    return {
        "message": "Buyer registered successfully",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_name": user.company_name
        }
    }

@router.post("/register/seller")
async def register_seller(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    company_name: str = Form(...),
    phone: str = Form(...),
    business_address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    registration_type: str = Form(...),  # GSTIN, CIN, Udyam, ISO, License
    registration_number: str = Form(...),
    business_description: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    certificate_file: Optional[UploadFile] = File(None),
    response: Response = None,
    db: Session = Depends(get_db)
):
    email_clean = email.strip().lower()
    existing = db.query(UserModel).filter(UserModel.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    cert_path = None
    if certificate_file and certificate_file.filename:
        # Validate file type: PDF, JPG, PNG
        ext = os.path.splitext(certificate_file.filename)[1].lower()
        if ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
            raise HTTPException(status_code=400, detail="Invalid certificate file type. Allowed: PDF, JPG, PNG")
            
        file_bytes = await certificate_file.read()
        if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Certificate file size exceeds 10MB limit")

        # Save document securely outside public static folder
        os.makedirs("uploads/certificates", exist_ok=True)
        filename = f"cert_{uuid.uuid4().hex}{ext}"
        cert_path = os.path.join("uploads", "certificates", filename)
        with open(cert_path, "wb") as f:
            f.write(file_bytes)

    user = UserModel(
        email=email_clean,
        password_hash=hash_password(password),
        role="seller",
        full_name=full_name,
        company_name=company_name,
        phone=phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    seller_profile = SellerProfileModel(
        user_id=user.id,
        company_name=company_name,
        representative_name=full_name,
        business_email=email_clean,
        phone_number=phone,
        business_address=business_address,
        city=city,
        state=state,
        latitude=latitude,
        longitude=longitude,
        registration_type=registration_type,
        registration_number=registration_number,
        certificate_path=cert_path,
        business_description=business_description,
        verification_status="Pending",
        is_demo_verified=False
    )
    db.add(seller_profile)
    db.commit()

    token = create_session_token(user.id, user.role)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    return {
        "message": "Seller application submitted successfully. Verification status: Pending admin review.",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_name": user.company_name,
            "verification_status": "Pending"
        }
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_me(current_user: Optional[UserModel] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    if not current_user:
        return {"authenticated": False}

    result = {
        "authenticated": True,
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company_name": current_user.company_name,
        "phone": current_user.phone
    }

    if current_user.role == "seller" and current_user.seller_profile:
        sp = current_user.seller_profile
        result["seller_profile"] = {
            "id": sp.id,
            "company_name": sp.company_name,
            "representative_name": sp.representative_name,
            "business_address": sp.business_address,
            "city": sp.city,
            "state": sp.state,
            "latitude": sp.latitude,
            "longitude": sp.longitude,
            "registration_type": sp.registration_type,
            "registration_number": sp.registration_number,
            "verification_status": sp.verification_status,
            "is_demo_verified": sp.is_demo_verified,
            "verification_notes": sp.verification_notes
        }

    return result
