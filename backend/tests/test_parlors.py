import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)

# Delhi coordinates
DELHI_LAT = 28.6139
DELHI_LNG = 77.2090

# Mumbai
MUMBAI_LAT = 19.0760
MUMBAI_LNG = 72.8777

@pytest.mark.parametrize("lat,lng,radius,expected_min_results", [
    (DELHI_LAT, DELHI_LNG, 10, 1),
    (MUMBAI_LAT, MUMBAI_LNG, 15, 0),  # may have data or not
])
def test_nearby_search(lat, lng, radius, expected_min_results):
    response = client.get("/api/v1/home/nearby", params={
        "lat": lat,
        "lng": lng,
        "radius": radius * 1000,  # meters
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # In demo data there should be some parlors near Delhi
    if lat == DELHI_LAT:
        assert len(data) >= expected_min_results

def test_home_endpoint():
    response = client.get("/api/v1/home")
    assert response.status_code == 200
    data = response.json()
    assert "parlors" in data or isinstance(data, dict)

# TODO: Add tests for auth, booking, reels, etc.
