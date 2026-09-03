import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import HabitationTriage, RouteResponse

def run_suite():
    client = TestClient(app)
    results = {}
    print("=" * 80)
    print("ROLE B: PRE-DEMO ERROR SHIELDING & FINAL VERIFICATION SUITE")
    print("=" * 80)

    # 1. GET /api/zones: HTTP 200 with FeatureCollection
    try:
        res = client.get("/api/zones")
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("type") == "FeatureCollection", "Expected type FeatureCollection"
        features = data.get("features", [])
        assert len(features) >= 2, f"Expected >= 2 features, found {len(features)}"
        colors = [f.get("properties", {}).get("zone_color", "").upper() for f in features]
        assert "RED" in colors, "Missing RED hazard zone"
        assert "YELLOW" in colors, "Missing YELLOW hazard zone"
        results["1. GET /api/zones (HTTP 200 FeatureCollection)"] = f"PASS ({len(features)} features: {colors})"
    except Exception as e:
        results["1. GET /api/zones (HTTP 200 FeatureCollection)"] = f"FAIL: {e}"

    # 2. GET /api/triage: HTTP 200 with valid priority-ranked habitations
    try:
        res = client.get("/api/triage")
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, list) and len(data) > 0, "Expected non-empty list"
        validated = [HabitationTriage.model_validate(item) for item in data]
        ranks = [h.priority_rank for h in validated]
        results["2. GET /api/triage (HTTP 200 Priority Ranks)"] = f"PASS ({len(validated)} habitations: Ranks {ranks})"
    except Exception as e:
        results["2. GET /api/triage (HTTP 200 Priority Ranks)"] = f"FAIL: {e}"

    # 3. GET /api/route: HTTP 200 with valid LineString coordinates and distance
    try:
        res = client.get("/api/route?from_lat=11.55&from_lon=76.10&to_lat=11.60&to_lon=76.15&region=wayanad")
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        data = res.json()
        validated = RouteResponse.model_validate(data)
        assert len(validated.path_coordinates) >= 2, "Expected path coordinates"
        assert validated.distance_km > 0, "Expected distance > 0"
        results["3. GET /api/route (HTTP 200 LineString & Distance)"] = (
            f"PASS (Waypoints: {len(validated.path_coordinates)}, Distance: {validated.distance_km} km)"
        )
    except Exception as e:
        results["3. GET /api/route (HTTP 200 LineString & Distance)"] = f"FAIL: {e}"

    # 4. POST /api/manifest/hab_001/authorize: HTTP 200 returning valid PDF download link
    download_url = None
    try:
        payload = {
            "habitation_id": "hab_001",
            "authorized_by": "District Magistrate & Chairman, DDMA"
        }
        res = client.post("/api/manifest/hab_001/authorize", json=payload)
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("status") == "AUTHORIZED", "Expected status AUTHORIZED"
        download_url = data.get("download_url")
        assert download_url and download_url.startswith("/static/manifests/"), "Missing or invalid download_url"
        results["4. POST /api/manifest/hab_001/authorize (HTTP 200)"] = (
            f"PASS (Order Ref: {data.get('order_id')}, URL: {download_url})"
        )
    except Exception as e:
        results["4. POST /api/manifest/hab_001/authorize (HTTP 200)"] = f"FAIL: {e}"

    # 5. POST /api/alerts/dispatch: HTTP 200 returning valid CAP 1.2 XML and simulated SMS log
    try:
        alert_payload = {
            "habitation_ids": ["hab_001", "hab_002"],
            "message_local_language": "അടിയന്തിര ഒഴിപ്പിക്കൽ നിർദ്ദേശം: ദുരന്ത നിവാരണ അതോറിറ്റി."
        }
        res = client.post("/api/alerts/dispatch", json=alert_payload)
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("status") == "dispatched", "Expected status dispatched"
        assert "cap_xml" in data and "urn:oasis:names:tc:emergency:cap:1.2" in data["cap_xml"]
        assert data.get("sms_dispatch", {}).get("status") == "DELIVERED"
        results["5. POST /api/alerts/dispatch (HTTP 200 CAP & SMS)"] = (
            f"PASS (Dispatched: {data.get('alerts_count')}, SMS: {data['sms_dispatch']['status']})"
        )
    except Exception as e:
        results["5. POST /api/alerts/dispatch (HTTP 200 CAP & SMS)"] = f"FAIL: {e}"

    # 6. Static PDF download route: HTTP 200 serving application/pdf
    try:
        assert download_url is not None, "Missing download_url from check 4"
        res = client.get(download_url)
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        content_type = res.headers.get("content-type", "")
        assert "application/pdf" in content_type, f"Expected application/pdf, got {content_type}"
        assert res.content.startswith(b"%PDF-"), "Invalid PDF binary header"
        assert len(res.content) > 2048, "PDF size suspiciously small"
        results["6. Static PDF Route Download (HTTP 200 application/pdf)"] = (
            f"PASS (Content-Type: {content_type}, Size: {len(res.content)} bytes)"
        )
    except Exception as e:
        results["6. Static PDF Route Download (HTTP 200 application/pdf)"] = f"FAIL: {e}"

    # Defensive Edge-Case Sanity Check: Out-of-bounds coords & Unknown habitation
    try:
        # Bad latitude test
        bad_res = client.get("/api/route?from_lat=999.0&from_lon=76.10&to_lat=11.60&to_lon=76.15")
        assert bad_res.status_code in (400, 422), f"Expected 400/422 for invalid coords, got {bad_res.status_code}"
        
        # Unknown habitation ID test (graceful fallback)
        unknown_res = client.post("/api/manifest/hab_unknown_999/authorize", json={
            "habitation_id": "hab_unknown_999",
            "authorized_by": "District Magistrate"
        })
        assert unknown_res.status_code == 200, f"Expected 200 with fallback for unknown hab, got {unknown_res.status_code}"
        results["7. Defensive Edge-Case Handling (Bounds & Fallbacks)"] = "PASS (400/422 on bad bounds, 200 on unknown hab)"
    except Exception as e:
        results["7. Defensive Edge-Case Handling (Bounds & Fallbacks)"] = f"FAIL: {e}"

    # Print Table
    print("\n" + "-" * 80)
    print(f"{'PRE-DEMO VERIFICATION CHECK':<52} | {'STATUS':<25}")
    print("-" * 80)
    all_passed = True
    for check, status in results.items():
        pass_fail = "PASS" if status.startswith("PASS") else "FAIL"
        print(f"{check:<52} | {status}")
        if pass_fail != "PASS":
            all_passed = False
    print("-" * 80)
    print("FINAL PRE-DEMO STATUS:", "ALL CHECKS PASSED (100% PRODUCTION READY)" if all_passed else "CHECKS FAILED")
    print("=" * 80 + "\n")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_suite()
