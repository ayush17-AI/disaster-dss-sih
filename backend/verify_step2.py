import sys
import os

# Ensure backend directory is in sys.path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import HabitationTriage, RouteResponse

def run_verification():
    client = TestClient(app)
    results = {}
    
    print("=" * 70)
    print("STEP 2: ROLE B BACKEND VERIFICATION REPORT")
    print("=" * 70)

    # 1. GET /api/zones
    try:
        res = client.get("/api/zones")
        assert res.status_code == 200, f"Status code {res.status_code}"
        data = res.json()
        assert data.get("type") == "FeatureCollection", "Missing type: FeatureCollection"
        assert len(data.get("features", [])) >= 2, "Expected at least 2 features"
        colors = [f["properties"].get("zone_color") for f in data["features"]]
        assert "RED" in colors and "YELLOW" in colors, f"Missing RED or YELLOW zone in {colors}"
        results["1. GET /api/zones (GeoJSON FeatureCollection)"] = "PASS"
    except Exception as e:
        results["1. GET /api/zones (GeoJSON FeatureCollection)"] = f"FAIL: {e}"

    # 2. GET /api/triage
    try:
        res = client.get("/api/triage")
        assert res.status_code == 200, f"Status code {res.status_code}"
        data = res.json()
        assert isinstance(data, list) and len(data) > 0, "Expected non-empty list"
        validated = [HabitationTriage.model_validate(item) for item in data]
        results["2. GET /api/triage (Validated list[HabitationTriage])"] = f"PASS ({len(validated)} habitations)"
    except Exception as e:
        results["2. GET /api/triage (Validated list[HabitationTriage])"] = f"FAIL: {e}"

    # 3. POST /api/manifest/hab_001/authorize
    try:
        payload = {"habitation_id": "hab_001", "authorized_by": "District Magistrate"}
        res = client.post("/api/manifest/hab_001/authorize", json=payload)
        assert res.status_code == 200, f"Status code {res.status_code}"
        data = res.json()
        assert data.get("status") == "PENDING_DM_AUTHORIZATION", f"Unexpected status: {data.get('status')}"
        results["3. POST /api/manifest/hab_001/authorize (ManifestRequest)"] = "PASS"
    except Exception as e:
        results["3. POST /api/manifest/hab_001/authorize (ManifestRequest)"] = f"FAIL: {e}"

    # 4. GET /api/route
    try:
        res = client.get("/api/route?from_lat=11.5&from_lon=76.1&to_lat=11.6&to_lon=76.2")
        assert res.status_code == 200, f"Status code {res.status_code}"
        data = res.json()
        route = RouteResponse.model_validate(data)
        assert len(route.path_coordinates) >= 2, "Expected valid coordinates"
        assert route.avoids_red_zones is True
        results["4. GET /api/route (Validated RouteResponse)"] = f"PASS (Distance: {route.distance_km} km)"
    except Exception as e:
        results["4. GET /api/route (Validated RouteResponse)"] = f"FAIL: {e}"

    # 5. POST /api/alerts/dispatch
    try:
        alert_payload = {
            "habitation_ids": ["hab_001", "hab_002"],
            "message_local_language": "അടിയന്തിര ഒഴിപ്പിക്കൽ മുന്നറിയിപ്പ്: മണ്ണിടിച്ചിൽ സാധ്യത."
        }
        res = client.post("/api/alerts/dispatch", json=alert_payload)
        assert res.status_code == 200, f"Status code {res.status_code}"
        data = res.json()
        assert data.get("status") == "dispatched"
        assert data.get("count") == 2
        results["5. POST /api/alerts/dispatch (AlertRequest)"] = "PASS (Dispatched 2 alerts)"
    except Exception as e:
        results["5. POST /api/alerts/dispatch (AlertRequest)"] = f"FAIL: {e}"

    # 6. Verify CORS headers
    try:
        res = client.get("/api/zones", headers={"Origin": "http://localhost:3000"})
        cors_header = res.headers.get("access-control-allow-origin")
        assert cors_header in ("*", "http://localhost:3000"), f"CORS header missing or unexpected: {cors_header}"
        assert res.headers.get("access-control-allow-credentials") == "true"
        results["6. CORS Headers Verification (Access-Control-Allow-Origin)"] = f"PASS (Origin: {cors_header})"
    except Exception as e:
        results["6. CORS Headers Verification (Access-Control-Allow-Origin)"] = f"FAIL: {e}"

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
