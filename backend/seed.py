import os
import json
from datetime import datetime, timedelta
from backend.database import SessionLocal, init_and_migrate_db, engine
from backend.models import (
    UserModel, SellerProfileModel, PartModel, ProductImageModel, 
    TransactionModel, TransactionStatusHistoryModel, ReviewModel,
    ProductVerificationRecordModel
)
from backend.services.auth import hash_password

def seed_database():
    os.makedirs("uploads/certificates", exist_ok=True)
    os.makedirs("uploads/products", exist_ok=True)
    
    init_and_migrate_db()
    db = SessionLocal()
    try:
        # 1. ADMIN USER
        admin = db.query(UserModel).filter(UserModel.email == "admin@ghostinventory.com").first()
        if not admin:
            admin = UserModel(
                email="admin@ghostinventory.com",
                password_hash=hash_password("Admin123!"),
                role="admin",
                full_name="System Chief Auditor",
                phone="+91 98000 00000",
                company_name="Ghost Inventory Platform Admin"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # 2. BUYER USER
        buyer1 = db.query(UserModel).filter(UserModel.email == "buyer_mahindra@auto.com").first()
        if not buyer1:
            buyer1 = UserModel(
                email="buyer_mahindra@auto.com",
                password_hash=hash_password("Buyer123!"),
                role="buyer",
                full_name="Vikram Patel",
                phone="+91 98112 33445",
                company_name="Auto Assembly Plant #4"
            )
            db.add(buyer1)
            db.commit()
            db.refresh(buyer1)

        # 3. SELLER 1: Apex Precision Components Ltd (Verified, Rating ~4.8)
        seller1 = db.query(UserModel).filter(UserModel.email == "apex_spares@industrial.com").first()
        if not seller1:
            seller1 = UserModel(
                email="apex_spares@industrial.com",
                password_hash=hash_password("Seller123!"),
                role="seller",
                full_name="Rajesh Sharma",
                phone="+91 98230 11223",
                company_name="Apex Precision Components Ltd"
            )
            db.add(seller1)
            db.commit()
            db.refresh(seller1)

            profile1 = SellerProfileModel(
                user_id=seller1.id,
                company_name="Apex Precision Components Ltd",
                representative_name="Rajesh Sharma",
                business_email="apex_spares@industrial.com",
                phone_number="+91 98230 11223",
                business_address="Plot 45, MIDC Industrial Area, Pimpri",
                city="Pune",
                state="Maharashtra",
                latitude=18.6298,
                longitude=73.7997,
                registration_type="GSTIN",
                registration_number="27AAACA1234A1Z5",
                certificate_path="uploads/certificates/demo_apex_gstin.pdf",
                business_description="Authorized distributor and surplus stock holder for industrial bearings, hydraulics, and Siemens automation modules.",
                verification_status="Verified",
                is_demo_verified=True,
                verification_notes="DEMO VERIFIED: Seeded hackathon verified seller account.",
                review_checklist_json=json.dumps({"gstin_format_check": True, "address_match_check": True, "certificate_clarity_check": True}),
                verified_by_id=admin.id,
                verified_at=datetime.utcnow()
            )
            db.add(profile1)
            db.commit()

        # 4. SELLER 2: BoltTech Engineering Solutions (Pending, Rating ~4.5)
        seller2 = db.query(UserModel).filter(UserModel.email == "bolt_tech@factory.com").first()
        if not seller2:
            seller2 = UserModel(
                email="bolt_tech@factory.com",
                password_hash=hash_password("Seller123!"),
                role="seller",
                full_name="Amit Deshmukh",
                phone="+91 98990 44556",
                company_name="BoltTech Engineering Solutions"
            )
            db.add(seller2)
            db.commit()
            db.refresh(seller2)

            profile2 = SellerProfileModel(
                user_id=seller2.id,
                company_name="BoltTech Engineering Solutions",
                representative_name="Amit Deshmukh",
                business_email="bolt_tech@factory.com",
                phone_number="+91 98990 44556",
                business_address="Unit 12, Industrial Estate, Andheri East",
                city="Mumbai",
                state="Maharashtra",
                latitude=19.0760,
                longitude=72.8777,
                registration_type="Udyam",
                registration_number="UDYAM-MH-12-0098765",
                certificate_path="uploads/certificates/demo_bolttech_udyam.pdf",
                business_description="Precision hydraulic valves and heavy industrial hardware spares.",
                verification_status="Pending",
                is_demo_verified=False,
                verification_notes="Awaiting admin review of submitted registration document."
            )
            db.add(profile2)
            db.commit()

        # 5. SELLER 3: Precision Tech Alloys & Fasteners (Verified, Rating ~4.2)
        seller3 = db.query(UserModel).filter(UserModel.email == "precision_tech@alloys.com").first()
        if not seller3:
            seller3 = UserModel(
                email="precision_tech@alloys.com",
                password_hash=hash_password("Seller123!"),
                role="seller",
                full_name="Sanjay Kulkarni",
                phone="+91 98770 22334",
                company_name="Precision Tech Alloys & Fasteners"
            )
            db.add(seller3)
            db.commit()
            db.refresh(seller3)

            profile3 = SellerProfileModel(
                user_id=seller3.id,
                company_name="Precision Tech Alloys & Fasteners",
                representative_name="Sanjay Kulkarni",
                business_email="precision_tech@alloys.com",
                phone_number="+91 98770 22334",
                business_address="Gat 88, Ambad MIDC",
                city="Nashik",
                state="Maharashtra",
                latitude=19.9975,
                longitude=73.7898,
                registration_type="GSTIN",
                registration_number="27BBBCA5678B1Z9",
                certificate_path="uploads/certificates/demo_precision_gstin.pdf",
                business_description="Specialist manufacturer and holder of titanium valves, CNC brackets, and aerospace-grade fittings.",
                verification_status="Verified",
                is_demo_verified=True,
                verification_notes="DEMO VERIFIED: Seeded verified seller account.",
                review_checklist_json=json.dumps({"gstin_format_check": True, "address_match_check": True, "certificate_clarity_check": True}),
                verified_by_id=admin.id,
                verified_at=datetime.utcnow()
            )
            db.add(profile3)
            db.commit()

        # 6. SELLER 4: ElectroSensor Industrial Systems (Under Review / Unverified, Rating ~3.9)
        seller4 = db.query(UserModel).filter(UserModel.email == "electrosensor@automation.com").first()
        if not seller4:
            seller4 = UserModel(
                email="electrosensor@automation.com",
                password_hash=hash_password("Seller123!"),
                role="seller",
                full_name="Pooja Mehta",
                phone="+91 98110 99887",
                company_name="ElectroSensor Industrial Systems"
            )
            db.add(seller4)
            db.commit()
            db.refresh(seller4)

            profile4 = SellerProfileModel(
                user_id=seller4.id,
                company_name="ElectroSensor Industrial Systems",
                representative_name="Pooja Mehta",
                business_email="electrosensor@automation.com",
                phone_number="+91 98110 99887",
                business_address="Sector 4, Wagle Estate",
                city="Thane",
                state="Maharashtra",
                latitude=19.2183,
                longitude=72.9781,
                registration_type="CIN",
                registration_number="U29253MH2021PTC365432",
                certificate_path=None,
                business_description="Supplier of pressure sensors, switches, gaskets, and industrial automation transmitters.",
                verification_status="Under Review",
                is_demo_verified=False,
                verification_notes="Document clarity check pending."
            )
            db.add(profile4)
            db.commit()

        # 7. SEED DIVERSIFIED PRODUCTS IF FEWER THAN 10 EXIST
        part_count = db.query(PartModel).count()
        if part_count < 10:
            # Delete old repetitive entries if needed to replace with diverse catalogue
            if part_count > 0 and part_count < 10:
                db.query(ReviewModel).delete()
                db.query(TransactionModel).delete()
                db.query(PartModel).delete()
                db.commit()

            parts_data = [
                {
                    "part_name": "SKF Deep Groove Ball Bearing 6205-2RSH",
                    "material": "Chrome Steel",
                    "size": "25x52x15 mm",
                    "base_price": 450.0,
                    "seller_name": "Apex Precision Components Ltd",
                    "seller_id": seller1.id,
                    "description": "High-precision sealed deep groove ball bearing suitable for electric motors, industrial pumps, and gearboxes.",
                    "manufacturer": "SKF",
                    "model_number": "6205-2RSH",
                    "part_number": "SKF-6205-2RSH",
                    "condition": "New",
                    "available_quantity": 45,
                    "location_city": "Pune",
                    "location_state": "Maharashtra",
                    "latitude": 18.6298,
                    "longitude": 73.7997,
                    "estimated_dispatch_days": 1,
                    "verification_status": "Verified"
                },
                {
                    "part_name": "Stainless Steel Industrial Bearing — 25 mm Shaft",
                    "material": "316 Stainless Steel",
                    "size": "25x52x15 mm",
                    "base_price": 650.0,
                    "seller_name": "Apex Precision Components Ltd",
                    "seller_id": seller1.id,
                    "description": "Corrosion-resistant stainless steel ball bearing designed for chemical and food processing equipment.",
                    "manufacturer": "NSK",
                    "model_number": "SS6205-2RS",
                    "part_number": "NSK-SS6205",
                    "condition": "New",
                    "available_quantity": 30,
                    "location_city": "Pune",
                    "location_state": "Maharashtra",
                    "latitude": 18.6298,
                    "longitude": 73.7997,
                    "estimated_dispatch_days": 1,
                    "verification_status": "Verified"
                },
                {
                    "part_name": "Siemens S7-1200 PLC CPU 1214C DC/DC/DC",
                    "material": "Polycarbonate Housing",
                    "size": "110x100x75 mm",
                    "base_price": 18500.0,
                    "seller_name": "Apex Precision Components Ltd",
                    "seller_id": seller1.id,
                    "description": "Unused surplus compact PLC controller with 14 DI, 10 DQ, 2 AI onboard. Ethernet PROFINET port.",
                    "manufacturer": "Siemens",
                    "model_number": "6ES7214-1AG40-0XB0",
                    "part_number": "S7-1200-CPU1214C",
                    "condition": "Unused Surplus",
                    "available_quantity": 3,
                    "location_city": "Pune",
                    "location_state": "Maharashtra",
                    "latitude": 18.6298,
                    "longitude": 73.7997,
                    "estimated_dispatch_days": 1,
                    "verification_status": "Verified"
                },
                {
                    "part_name": "Heavy Duty Modular Conveyor Belt Cleats",
                    "material": "Food Grade Polypropylene",
                    "size": "500 mm Width x 10 m",
                    "base_price": 3400.0,
                    "seller_name": "Apex Precision Components Ltd",
                    "seller_id": seller1.id,
                    "description": "Modular plastic belt with 2-inch flights for high temperature bottling & packaging lines.",
                    "manufacturer": "Intralox",
                    "model_number": "Series 900",
                    "part_number": "INT-S900-BELT",
                    "condition": "New",
                    "available_quantity": 12,
                    "location_city": "Pune",
                    "location_state": "Maharashtra",
                    "latitude": 18.6298,
                    "longitude": 73.7997,
                    "estimated_dispatch_days": 1,
                    "verification_status": "Verified"
                },
                {
                    "part_name": "Bosch Rexroth 4WE6 Directional Hydraulic Control Valve",
                    "material": "Cast Iron / Nitrile Seals",
                    "size": "NG6 / CETOP 3",
                    "base_price": 6200.0,
                    "seller_name": "BoltTech Engineering Solutions",
                    "seller_id": seller2.id,
                    "description": "Solenoid operated directional spool valve, 24V DC coil, max pressure 350 bar.",
                    "manufacturer": "Bosch Rexroth",
                    "model_number": "4WE6E6X/EG24N9K4",
                    "part_number": "REX-4WE6",
                    "condition": "Refurbished",
                    "available_quantity": 8,
                    "location_city": "Mumbai",
                    "location_state": "Maharashtra",
                    "latitude": 19.0760,
                    "longitude": 72.8777,
                    "estimated_dispatch_days": 2,
                    "verification_status": "Pending Inspection"
                },
                {
                    "part_name": "Hydraulic Pump Seal Kit — Heavy Duty Nitrile",
                    "material": "High Temp Nitrile Rubber",
                    "size": "Standard Kit (50 mm Shaft)",
                    "base_price": 1250.0,
                    "seller_name": "BoltTech Engineering Solutions",
                    "seller_id": seller2.id,
                    "description": "Complete replacement seal kit for industrial axial piston hydraulic pumps.",
                    "manufacturer": "Parker Hannifin",
                    "model_number": "SK-F11-050",
                    "part_number": "PARKER-SK050",
                    "condition": "New",
                    "available_quantity": 20,
                    "location_city": "Mumbai",
                    "location_state": "Maharashtra",
                    "latitude": 19.0760,
                    "longitude": 72.8777,
                    "estimated_dispatch_days": 2,
                    "verification_status": "Unverified"
                },
                {
                    "part_name": "Titanium Valve — Grade 5, 12 mm Flange",
                    "material": "Ti-6Al-4V Grade 5 Titanium",
                    "size": "12 mm Port Diameter",
                    "base_price": 2800.0,
                    "seller_name": "Precision Tech Alloys & Fasteners",
                    "seller_id": seller3.id,
                    "description": "High performance lightweight titanium alloy check valve for high pressure acid lines.",
                    "manufacturer": "Swagelok",
                    "model_number": "TI-CV-12M",
                    "part_number": "SWAGE-TI12",
                    "condition": "New",
                    "available_quantity": 15,
                    "location_city": "Nashik",
                    "location_state": "Maharashtra",
                    "latitude": 19.9975,
                    "longitude": 73.7898,
                    "estimated_dispatch_days": 1,
                    "verification_status": "Verified"
                },
                {
                    "part_name": "Aluminium CNC Mounting Bracket",
                    "material": "6061-T6 Billet Aluminium",
                    "size": "120x80x40 mm",
                    "base_price": 850.0,
                    "seller_name": "Precision Tech Alloys & Fasteners",
                    "seller_id": seller3.id,
                    "description": "Precision CNC milled mounting bracket with anodized finish for industrial servo motors.",
                    "manufacturer": "PrecisionTech",
                    "model_number": "BRK-6061-NEMA34",
                    "part_number": "PTA-BRK34",
                    "condition": "New",
                    "available_quantity": 50,
                    "location_city": "Nashik",
                    "location_state": "Maharashtra",
                    "latitude": 19.9975,
                    "longitude": 73.7898,
                    "estimated_dispatch_days": 1,
                    "verification_status": "Verified"
                },
                {
                    "part_name": "Industrial Pressure Sensor — 24V DC 4-20mA",
                    "material": "Stainless Steel 316L Diaphragm",
                    "size": "G 1/4 Threaded Connection",
                    "base_price": 3950.0,
                    "seller_name": "ElectroSensor Industrial Systems",
                    "seller_id": seller4.id,
                    "description": "Piezoresistive pressure transmitter for hydraulic line monitoring, range 0-100 bar.",
                    "manufacturer": "Danfoss",
                    "model_number": "MBS 3000",
                    "part_number": "DANFOSS-MBS3000",
                    "condition": "New",
                    "available_quantity": 6,
                    "location_city": "Thane",
                    "location_state": "Maharashtra",
                    "latitude": 19.2183,
                    "longitude": 72.9781,
                    "estimated_dispatch_days": 2,
                    "verification_status": "Pending Inspection"
                },
                {
                    "part_name": "High-Temperature Silicone Gasket Set",
                    "material": "Vulcanized Silicone Rubber",
                    "size": "DN50 Flange Size (Max 300°C)",
                    "base_price": 650.0,
                    "seller_name": "ElectroSensor Industrial Systems",
                    "seller_id": seller4.id,
                    "description": "Thermal-resistant gasket ring set for boiler piping and high temp steam manifolds.",
                    "manufacturer": "Flexitallic",
                    "model_number": "SIL-DN50-HT",
                    "part_number": "FLEX-DN50",
                    "condition": "New",
                    "available_quantity": 100,
                    "location_city": "Thane",
                    "location_state": "Maharashtra",
                    "latitude": 19.2183,
                    "longitude": 72.9781,
                    "estimated_dispatch_days": 1,
                    "verification_status": "Unverified"
                }
            ]

            created_parts = []
            for pdata in parts_data:
                p = PartModel(**pdata, last_stock_confirmed_at=datetime.utcnow())
                db.add(p)
                created_parts.append(p)
            db.commit()

            # 8. SEED TRANSACTIONS & DEMO REVIEWS FOR DYNAMIC SELLER RATINGS
            # Target Ratings: Seller 1 -> 4.8 (24 reviews), Seller 2 -> 4.5 (12 reviews), Seller 3 -> 4.2 (8 reviews), Seller 4 -> 3.9 (5 reviews)
            seller_targets = [
                (seller1.id, created_parts[0].id, 4.8, 24, "Apex Precision Components Ltd"),
                (seller2.id, created_parts[4].id, 4.5, 12, "BoltTech Engineering Solutions"),
                (seller3.id, created_parts[6].id, 4.2, 8, "Precision Tech Alloys"),
                (seller4.id, created_parts[8].id, 3.9, 5, "ElectroSensor Systems")
            ]

            for s_id, p_id, target_avg, total_cnt, s_name in seller_targets:
                # Calculate number of 5, 4, 3 star reviews to hit exact target average
                for r_idx in range(total_cnt):
                    # Pick rating to match target average
                    if s_id == seller1.id:
                        rating_val = 5 if r_idx < 19 else 4
                    elif s_id == seller2.id:
                        rating_val = 5 if r_idx < 6 else 4
                    elif s_id == seller3.id:
                        rating_val = 5 if r_idx < 2 else (4 if r_idx < 7 else 3)
                    else:  # seller4
                        rating_val = 4 if r_idx < 4 else 3

                    # Create dummy completed transaction
                    t = TransactionModel(
                        buyer_id=buyer1.id,
                        seller_id=s_id,
                        part_id=p_id,
                        quantity=1,
                        agreed_price=500.0,
                        status="Delivered",
                        delivery_address="Assembly Line 4, MIDC",
                        urgency_level=1,
                        stock_confirmed_by_seller=True
                    )
                    db.add(t)
                    db.commit()
                    db.refresh(t)

                    r = ReviewModel(
                        transaction_id=t.id,
                        buyer_id=buyer1.id,
                        seller_id=s_id,
                        rating=rating_val,
                        comment=f"Verified transaction review for {s_name}. Delivery & part quality response satisfactory. (Demo Review)",
                        is_demo=True
                    )
                    db.add(r)
                db.commit()

        print("Database successfully populated with diverse sellers, varied products, distinct prices, and dynamic ratings!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
