import json
from datetime import datetime
from backend.database import SessionLocal
from backend.models import (
    UserModel, SellerProfileModel, PartModel, 
    TransactionModel, ReviewModel
)
from backend.services.auth import hash_password

def seed_demo_data():
    db = SessionLocal()
    try:
        admin = db.query(UserModel).filter(UserModel.email == "admin@ghostinventory.com").first()
        buyer1 = db.query(UserModel).filter(UserModel.email == "buyer_mahindra@auto.com").first()

        sellers_info = [
            {
                "email": "demo_apex@industrial.com",
                "company": "Apex Industrial Components Demo",
                "rep": "Demo Rajesh",
                "target_rating": 4.9,
                "review_count": 35
            },
            {
                "email": "demo_precision@valvesupply.com",
                "company": "Precision Valve Supply Demo",
                "rep": "Demo Sanjay",
                "target_rating": 4.6,
                "review_count": 18
            },
            {
                "email": "demo_titanium@dynamics.com",
                "company": "Titanium Dynamics Demo",
                "rep": "Demo Anil",
                "target_rating": 4.3,
                "review_count": 8
            }
        ]

        created_sellers = []

        for sinfo in sellers_info:
            seller = db.query(UserModel).filter(UserModel.email == sinfo["email"]).first()
            if not seller:
                seller = UserModel(
                    email=sinfo["email"],
                    password_hash=hash_password("DemoSeller123!"),
                    role="seller",
                    full_name=sinfo["rep"],
                    phone="+91 90000 00000",
                    company_name=sinfo["company"]
                )
                db.add(seller)
                db.commit()
                db.refresh(seller)

                profile = SellerProfileModel(
                    user_id=seller.id,
                    company_name=sinfo["company"],
                    representative_name=sinfo["rep"],
                    business_email=sinfo["email"],
                    phone_number="+91 90000 00000",
                    business_address="Demo Industrial Park, Pune",
                    city="Pune",
                    state="Maharashtra",
                    latitude=18.6,
                    longitude=73.8,
                    registration_type="GSTIN",
                    registration_number="27DEMO1234A1Z5",
                    business_description="Authorized Demo supplier.",
                    verification_status="Verified",
                    is_demo_verified=True,
                    verification_notes="DEMO VERIFIED: Seeded hackathon verified seller account.",
                    verified_by_id=admin.id if admin else None,
                    verified_at=datetime.utcnow()
                )
                db.add(profile)
                db.commit()
            created_sellers.append((seller, sinfo))

        # Add parts
        parts_data = [
            {
                "part_name": "Titanium valve 12mm",
                "material": "Ti-6Al-4V Grade 5",
                "size": "12 mm Port Diameter",
                "base_price": 2800.0,
                "seller_name": "Apex Industrial Components Demo",
                "seller_id": created_sellers[0][0].id,
                "description": "High performance lightweight titanium alloy check valve for high pressure acid lines.",
                "manufacturer": "Swagelok",
                "model_number": "TI-CV-12M-APEX",
                "part_number": "SWAGE-TI12-A",
                "condition": "New",
                "available_quantity": 40,
                "location_city": "Pune",
                "location_state": "Maharashtra",
                "latitude": 18.6,
                "longitude": 73.8,
                "estimated_dispatch_days": 1,
                "verification_status": "Verified"
            },
            {
                "part_name": "Titanium valve 12mm (Flanged)",
                "material": "Titanium Grade 2",
                "size": "12 mm",
                "base_price": 2650.0,
                "seller_name": "Precision Valve Supply Demo",
                "seller_id": created_sellers[1][0].id,
                "description": "Corrosion resistant titanium flanged valve.",
                "manufacturer": "Parker",
                "model_number": "PV-12-TI",
                "part_number": "PARKER-12TI",
                "condition": "New",
                "available_quantity": 15,
                "location_city": "Pune",
                "location_state": "Maharashtra",
                "latitude": 18.6,
                "longitude": 73.8,
                "estimated_dispatch_days": 2,
                "verification_status": "Verified"
            },
            {
                "part_name": "Standard Titanium valve 12mm",
                "material": "Titanium Alloy",
                "size": "12 mm",
                "base_price": 2400.0,
                "seller_name": "Titanium Dynamics Demo",
                "seller_id": created_sellers[2][0].id,
                "description": "Standard 12mm titanium ball valve.",
                "manufacturer": "Dynamics",
                "model_number": "TD-V12",
                "part_number": "TD-001",
                "condition": "Unused Surplus",
                "available_quantity": 5,
                "location_city": "Pune",
                "location_state": "Maharashtra",
                "latitude": 18.6,
                "longitude": 73.8,
                "estimated_dispatch_days": 3,
                "verification_status": "Verified"
            }
        ]

        created_parts = []
        for pdata in parts_data:
            existing_part = db.query(PartModel).filter(
                PartModel.part_number == pdata["part_number"]
            ).first()
            if not existing_part:
                p = PartModel(**pdata, last_stock_confirmed_at=datetime.utcnow())
                db.add(p)
                db.commit()
                db.refresh(p)
                created_parts.append(p)
            else:
                created_parts.append(existing_part)

        # Generate fake reviews to set rating
        if buyer1:
            for i, (seller, sinfo) in enumerate(created_sellers):
                part = created_parts[i]
                target_avg = sinfo["target_rating"]
                total_cnt = sinfo["review_count"]

                # Only seed if they have no reviews
                existing_reviews = db.query(ReviewModel).filter(ReviewModel.seller_id == seller.id).count()
                if existing_reviews < total_cnt:
                    # Delete existing to reconstruct the exact target
                    db.query(ReviewModel).filter(ReviewModel.seller_id == seller.id).delete()
                    db.commit()

                    for r_idx in range(total_cnt):
                        if target_avg >= 4.9:
                            rating_val = 5
                        elif target_avg >= 4.6:
                            rating_val = 5 if r_idx < (total_cnt * 0.6) else 4
                        else:
                            rating_val = 5 if r_idx < (total_cnt * 0.3) else 4

                        t = TransactionModel(
                            buyer_id=buyer1.id,
                            seller_id=seller.id,
                            part_id=part.id,
                            quantity=1,
                            agreed_price=part.base_price,
                            status="Delivered",
                            delivery_address="Assembly Line 4",
                            urgency_level=1,
                            stock_confirmed_by_seller=True
                        )
                        db.add(t)
                        db.commit()
                        db.refresh(t)

                        r = ReviewModel(
                            transaction_id=t.id,
                            buyer_id=buyer1.id,
                            seller_id=seller.id,
                            rating=rating_val,
                            comment="Great seller.",
                            is_demo=True
                        )
                        db.add(r)
                    db.commit()

        print("Demo data seeded successfully!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
