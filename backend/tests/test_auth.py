import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

# Example auth test skeleton - adjust endpoints and payloads to your actual auth
def test_login_password_skeleton():
    # This is a placeholder. Replace with real test credentials from your demo data.
    payload = {"phone": "+919999999010", "password": "Demo@123"}
    # response = client.post("/auth/login/password", json=payload)
    # assert response.status_code in (200, 401)  # 401 if not yet seeded
    pass
