import json
import base64
import hmac
import hashlib
import time
import bcrypt
from typing import Optional, List
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import UserModel

SECRET_KEY = "ghost-inventory-secure-hackathon-key-change-in-prod-2026"
SESSION_COOKIE_NAME = "ghost_session"

def hash_password(password: str) -> str:
    # Ensure raw password is byte-truncated to max 72 bytes for bcrypt compliance
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_session_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + (24 * 3600)  # 24 hours
    }
    json_bytes = json.dumps(payload).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(json_bytes).decode("utf-8").rstrip("=")
    
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256
    ).digest()
    b64_sig = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    
    return f"{b64_payload}.{b64_sig}"

def decode_session_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, b64_sig = parts
        
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256
        ).digest()
        expected_b64_sig = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")
        
        if not hmac.compare_digest(b64_sig, expected_b64_sig):
            return None
            
        padded_b64 = b64_payload + "=" * (-len(b64_payload) % 4)
        json_bytes = base64.urlsafe_b64decode(padded_b64)
        payload = json.loads(json_bytes.decode("utf-8"))
        
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[UserModel]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        return None
        
    payload = decode_session_token(token)
    if not payload:
        return None
        
    user = db.query(UserModel).filter(UserModel.id == payload.get("user_id")).first()
    if not user or not user.is_active:
        return None
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserModel:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: UserModel = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Requires one of roles {allowed_roles}"
            )
        return current_user
    return role_checker
