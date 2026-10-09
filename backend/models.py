from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="buyer")  # buyer, seller, admin
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    seller_profile = relationship("SellerProfileModel", foreign_keys="SellerProfileModel.user_id", back_populates="user", uselist=False)
    parts = relationship("PartModel", back_populates="seller_user")
    buyer_transactions = relationship("TransactionModel", foreign_keys="TransactionModel.buyer_id", back_populates="buyer")
    seller_transactions = relationship("TransactionModel", foreign_keys="TransactionModel.seller_id", back_populates="seller")
    reviews_written = relationship("ReviewModel", foreign_keys="ReviewModel.buyer_id", back_populates="buyer")
    reviews_received = relationship("ReviewModel", foreign_keys="ReviewModel.seller_id", back_populates="seller")


class SellerProfileModel(Base):
    __tablename__ = "seller_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String, nullable=False)
    representative_name = Column(String, nullable=False)
    business_email = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    business_address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    registration_type = Column(String, nullable=False)  # GSTIN, CIN, Udyam, ISO, License
    registration_number = Column(String, nullable=False)
    certificate_path = Column(String, nullable=True)
    business_description = Column(Text, nullable=True)
    
    # Verification workflow: Pending, Under Review, Verified, Rejected
    verification_status = Column(String, default="Pending", nullable=False)
    is_demo_verified = Column(Boolean, default=False)  # DEMO VERIFIED label for hackathon data
    verification_notes = Column(Text, nullable=True)
    review_checklist_json = Column(Text, nullable=True)  # JSON string of manual verification checks
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", foreign_keys=[user_id], back_populates="seller_profile")
    verified_by = relationship("UserModel", foreign_keys=[verified_by_id])


class PartModel(Base):
    __tablename__ = "parts"

    # Preserved original columns
    id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String, index=True)
    material = Column(String, nullable=True)
    size = Column(String, nullable=True)
    base_price = Column(Float)
    seller_name = Column(String)

    # Extended columns
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    manufacturer = Column(String, nullable=True)
    model_number = Column(String, index=True, nullable=True)
    part_number = Column(String, index=True, nullable=True)
    condition = Column(String, default="New", nullable=True)  # New, Unused Surplus, Used, Refurbished
    available_quantity = Column(Integer, default=1, nullable=True)
    location_city = Column(String, nullable=True)
    location_state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    estimated_dispatch_days = Column(Integer, default=1, nullable=True)
    last_stock_confirmed_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    
    # Product verification status: Unverified, Pending Inspection, Verified, Rejected
    verification_status = Column(String, default="Unverified", nullable=True)

    seller_user = relationship("UserModel", back_populates="parts")
    images = relationship("ProductImageModel", back_populates="part", cascade="all, delete-orphan")
    transactions = relationship("TransactionModel", back_populates="part")
    product_reviews = relationship("ProductVerificationRecordModel", back_populates="part")


class ProductImageModel(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    image_path = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    part = relationship("PartModel", back_populates="images")


class ProductVerificationRecordModel(Base):
    __tablename__ = "product_verification_records"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    status = Column(String, nullable=False)  # Verified, Rejected, Pending Inspection
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    part = relationship("PartModel", back_populates="product_reviews")


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    agreed_price = Column(Float, nullable=False)
    
    # Statuses: Requested, Seller Confirmed, Accepted, Dispatched, Delivered, Cancelled, Disputed
    status = Column(String, default="Requested", nullable=False)
    delivery_address = Column(Text, nullable=True)
    buyer_latitude = Column(Float, nullable=True)
    buyer_longitude = Column(Float, nullable=True)
    required_delivery_days = Column(Integer, nullable=True)
    urgency_level = Column(Integer, default=1, nullable=False)
    stock_confirmed_by_seller = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = relationship("UserModel", foreign_keys=[buyer_id], back_populates="buyer_transactions")
    seller = relationship("UserModel", foreign_keys=[seller_id], back_populates="seller_transactions")
    part = relationship("PartModel", back_populates="transactions")
    status_history = relationship("TransactionStatusHistoryModel", back_populates="transaction", cascade="all, delete-orphan")
    review = relationship("ReviewModel", back_populates="transaction", uselist=False)


class TransactionStatusHistoryModel(Base):
    __tablename__ = "transaction_status_history"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    status = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("TransactionModel", back_populates="status_history")


class ReviewModel(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), unique=True, nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False)  # Clearly mark seeded demo reviews
    is_reported = Column(Boolean, default=False)
    report_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("TransactionModel", back_populates="review")
    buyer = relationship("UserModel", foreign_keys=[buyer_id], back_populates="reviews_written")
    seller = relationship("UserModel", foreign_keys=[seller_id], back_populates="reviews_received")