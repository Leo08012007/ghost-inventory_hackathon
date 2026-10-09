import pytest
import os
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, init_and_migrate_db
from backend.models import UserModel, PartModel, SellerProfileModel, TransactionModel, ReviewModel
from backend.services.geo import haversine_distance
from backend.services.pricing import calculate_suggested_price

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_and_migrate_db()

def test_health_check():
    """Verify health check endpoint contract."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "Ghost Inventory API Running 🚀"}

def test_legacy_upload_contract():
    """Verify original /upload endpoint contract remains functional."""
    payload = {
        "part_name": "Legacy Test Bearing 6000",
        "material": "Steel",
        "size": "10x26x8 mm",
        "base_price": 250.0,
        "seller_name": "Test Legacy Seller"
    }
    response = client.post("/upload", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "part_id" in data
    assert data["message"] == "Part stored securely"

def test_legacy_confirm_deal():
    """Verify original /confirm-deal endpoint contract."""
    db = SessionLocal()
    part = db.query(PartModel).first()
    db.close()

    if part:
        response = client.post("/confirm-deal", json={"part_id": part.id})
        assert response.status_code == 200
        data = response.json()
        assert "seller_name" in data
        assert "part_name" in data

def test_haversine_distance_calculation():
    """Verify Haversine formula distance between Pune (18.5204, 73.8567) and Mumbai (19.0760, 72.8777)."""
    dist = haversine_distance(18.5204, 73.8567, 19.0760, 72.8777)
    assert dist is not None
    assert 110.0 <= dist <= 135.0  # Approx 120 km

def test_urgency_pricing_service():
    """Verify transparent urgency pricing baseline formula: base + urgency * 50."""
    p1 = calculate_suggested_price(1000.0, 1)
    assert p1["suggested_price"] == 1050.0
    
    p5 = calculate_suggested_price(1000.0, 5)
    assert p5["suggested_price"] == 1250.0

def test_buyer_search_matching():
    """Verify search endpoint returns matches with distance and urgency price."""
    payload = {
        "query": "Bearing",
        "urgency_level": 3
    }
    response = client.post("/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert isinstance(data["matches"], list)

def test_auth_login_demo_admin():
    """Verify admin user login."""
    response = client.post("/api/auth/login", json={
        "email": "admin@ghostinventory.com",
        "password": "Admin123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "admin"
    assert "token" in data

def test_auth_unauthorized_admin_endpoint():
    """Verify non-admin cannot access admin endpoints."""
    # Reset client cookies
    test_client = TestClient(app)
    response = test_client.get("/api/admin/sellers")
    assert response.status_code in [401, 403]
