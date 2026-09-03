import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import HabitationTriage, RouteResponse

def run_verification():
    client = TestClient(app)
    results = {}
    
    print("=" * 70)
    print("SECTION 4.1: ROLE B BACKEND VERIFICATION REPORT")
    print("=" * 70)

    # 1. GET /api/zones
    try:
        res = client.get("/api/zones")
        assert res.status_code == 200, f"Status code {res.status_code}"
        data = res.json()
        assert data.get("type") == "FeatureCollection", "Missing type: FeatureCollection"
        features = data.get("features", [])
        assert len(features) >= 2, f"Expected >= 2 features, found {len(features)}"
        colors = [f.get("properties", {}).get("zone_color", "").upper() for f in features]
        assert "RED" in colors, "Missing RED zone"
        assert "YELLOW" in colors, "Missing YELLOW zone"
        results["1. GET /api/zones (200 & Valid GeoJSON)"] = f"PASS ({len(features)} features: {colors})"
    except Exception as e:
        results["1. GET /api/zones (200 & Valid GeoJSON)"] = f"FAIL: {e}"

    # 2. GET /api/triage
    try:
        res = client.get("/api/triage")
        assert res.status_code == 200, f"Status code {res.status_code}"
        data = res.json()
        assert isinstance(data, list) and len(data) > 0, "Expected non-empty list"
        validated = [HabitationTriage.model_validate(item) for item in data]
        results["2. GET /api/triage (200 & Valid Triage List)"] = f"PASS ({len(validated)} habitations validated)"
    except Exception as e:
        results["2. GET /api/triage (200 & Valid Triage List)"] = f"FAIL: {e}"

    # 3. GET /api/route
    try:
        res = client.get("/api/route")
        assert res.status_code == 200, f"Status code {res.status_code}: {res.text}"
        data = res.json()
        validated = RouteResponse.model_validate(data)
        assert len(validated.path_coordinates) >= 2, "Expected path coordinates"
        assert validated.distance_km > 0, "Expected distance > 0"
        results["3. GET /api/route (200 & Valid RouteResponse)"] = (
            f"PASS (Distance: {validated.distance_km} km, Avoids Red Zones: {validated.avoids_red_zones})"
        )
    except Exception as e:
        results["3. GET /api/route (200 & Valid RouteResponse)"] = f"FAIL: {e}"

    # 4. CORS headers are present
    try:
        res = client.get("/api/zones", headers={"Origin": "http://localhost:3000"})
        cors_header = res.headers.get("access-control-allow-origin")
        assert cors_header is not None, "Missing Access-Control-Allow-Origin header"
        assert cors_header in ("*", "http://localhost:3000"), f"Unexpected CORS origin: {cors_header}"
        assert res.headers.get("access-control-allow-credentials") == "true"
        results["4. CORS Headers Verification"] = f"PASS (Access-Control-Allow-Origin: {cors_header})"
    except Exception as e:
        results["4. CORS Headers Verification"] = f"FAIL: {e}"

    # Summary Output
    all_passed = True
    for check, status in results.items():
        pass_fail = "PASS" if status.startswith("PASS") else "FAIL"
        print(f"[{pass_fail}] {check}: {status}")
        if pass_fail != "PASS":
            all_passed = False

    print("=" * 70)
    print("OVERALL STATUS:", "ALL CHECKS PASSED (100%)" if all_passed else "CHECKS FAILED")
    print("=" * 70)

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
