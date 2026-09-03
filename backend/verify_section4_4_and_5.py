import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lxml.etree as etree
from fastapi.testclient import TestClient
from app.main import app
from app.services.cap_alert_builder import build_cap_alert, build_simulated_sms
from app.models.schemas import HabitationTriage, RouteResponse

def run_verification():
    client = TestClient(app)
    results = {}
    print("=" * 80)
    print("SECTIONS 4.4 & 4.5: ROLE B END-TO-END WIRE & CAP-XML AUDIT REPORT")
    print("=" * 80)

    # 1. Direct Test: CAP Alert Builder
    try:
        xml_output = build_cap_alert(
            habitation_name="Mundakkai Settlement",
            message="അടിയന്തിര ഒഴിപ്പിക്കൽ മുന്നറിയിപ്പ്: മണ്ണിടിച്ചിൽ സാധ്യത അതീവ ഗുരുതരം.",
            lat=11.538,
            lon=76.155
        )
        assert 'xmlns="urn:oasis:names:tc:emergency:cap:1.2"' in xml_output, "Missing CAP 1.2 default namespace"
        assert "<identifier>DRR-Mundakkai_Settlement-" in xml_output, "Missing or invalid identifier"
        assert "<circle>11.53800,76.15500 2.0</circle>" in xml_output, "Missing or invalid circle geometry"
        
        # Test clean parsing via lxml.etree.fromstring
        parsed_root = etree.fromstring(xml_output.encode("utf-8"))
        assert parsed_root.tag.endswith("alert"), f"Invalid root tag: {parsed_root.tag}"
        results["1. CAP Alert Builder (Direct XML & Parse Validation)"] = "PASS (Valid CAP 1.2 XML tree)"
    except Exception as e:
        results["1. CAP Alert Builder (Direct XML & Parse Validation)"] = f"FAIL: {e}"

    # 2. Test POST /api/alerts/dispatch
    try:
        alert_payload = {
            "habitation_ids": ["hab_001", "hab_002"],
            "message_local_language": "അടിയന്തിര ഒഴിപ്പിക്കൽ മുന്നറിയിപ്പ്: താലൂക്ക് കൺട്രോൾ റൂം."
        }
        res = client.post("/api/alerts/dispatch", json=alert_payload)
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("status") == "dispatched", f"Expected dispatched, got {data.get('status')}"
        assert data.get("alerts_count") == 2, f"Expected 2 alerts, got {data.get('alerts_count')}"
        assert "cap_xml" in data and len(data["cap_xml"]) > 100, "CAP XML missing or too short"
        assert data.get("sms_dispatch", {}).get("status") == "DELIVERED", "SMS dispatch status mismatch"
        results["2. API POST /api/alerts/dispatch (CAP & SMS Output)"] = (
            f"PASS (Status: {data['status']}, Dispatched: {data['alerts_count']}, SMS Target: {data['sms_dispatch']['target']})"
        )
    except Exception as e:
        results["2. API POST /api/alerts/dispatch (CAP & SMS Output)"] = f"FAIL: {e}"

    # 3. End-to-End Suite: All 5 core routers
    # 3a. GET /api/zones
    try:
        res = client.get("/api/zones")
        assert res.status_code == 200, f"HTTP {res.status_code}"
        geojson = res.json()
        assert geojson.get("type") == "FeatureCollection"
        results["3a. E2E GET /api/zones (Hazard Polygons)"] = (
            f"PASS (HTTP 200, Features: {len(geojson.get('features', []))})"
        )
    except Exception as e:
        results["3a. E2E GET /api/zones (Hazard Polygons)"] = f"FAIL: {e}"

    # 3b. GET /api/triage
    try:
        res = client.get("/api/triage")
        assert res.status_code == 200, f"HTTP {res.status_code}"
        triage_list = res.json()
        validated_triage = [HabitationTriage.model_validate(h) for h in triage_list]
        results["3b. E2E GET /api/triage (Ranked Habitations)"] = (
            f"PASS (HTTP 200, Validated: {len(validated_triage)} habitations)"
        )
    except Exception as e:
        results["3b. E2E GET /api/triage (Ranked Habitations)"] = f"FAIL: {e}"

    # 3c. GET /api/route
    try:
        res = client.get("/api/route?from_lat=11.55&from_lon=76.10&to_lat=11.60&to_lon=76.15&region=wayanad")
        assert res.status_code == 200, f"HTTP {res.status_code}"
        route_data = res.json()
        validated_route = RouteResponse.model_validate(route_data)
        assert len(validated_route.path_coordinates) >= 2
        assert validated_route.avoids_red_zones is True
        results["3c. E2E GET /api/route (Safe Topological Bypass)"] = (
            f"PASS (HTTP 200, Distance: {validated_route.distance_km} km, Avoids Red: {validated_route.avoids_red_zones})"
        )
    except Exception as e:
        results["3c. E2E GET /api/route (Safe Topological Bypass)"] = f"FAIL: {e}"

    # 3d. POST /api/manifest/{hab_id}/authorize
    try:
        manifest_payload = {
            "habitation_id": "hab_001",
            "authorized_by": "District Magistrate & Chairman, DDMA"
        }
        res = client.post("/api/manifest/hab_001/authorize", json=manifest_payload)
        assert res.status_code == 200, f"HTTP {res.status_code}"
        man_data = res.json()
        assert man_data.get("status") == "AUTHORIZED"
        dl_url = man_data.get("download_url")
        assert dl_url is not None
        
        # Verify static file download
        pdf_res = client.get(dl_url)
        assert pdf_res.status_code == 200
        assert pdf_res.headers.get("content-type") == "application/pdf"
        assert pdf_res.content[:5] == b"%PDF-"
        results["3d. E2E POST /api/manifest/authorize & Download"] = (
            f"PASS (HTTP 200, Order: {man_data['order_id']}, PDF: {len(pdf_res.content)} bytes)"
        )
    except Exception as e:
        results["3d. E2E POST /api/manifest/authorize & Download"] = f"FAIL: {e}"

    # 3e. POST /api/alerts/dispatch
    try:
        alert_payload = {
            "habitation_ids": ["hab_001"],
            "message_local_language": "അടിയന്തിര ഒഴിപ്പിക്കൽ നിർദ്ദേശം: സുരക്ഷിത താവളങ്ങളിലേക്ക് മാറുക."
        }
        res = client.post("/api/alerts/dispatch", json=alert_payload)
        assert res.status_code == 200, f"HTTP {res.status_code}"
        alt_data = res.json()
        assert alt_data.get("status") == "dispatched"
        assert "cap_xml" in alt_data and "alert" in alt_data["cap_xml"]
        results["3e. E2E POST /api/alerts/dispatch (CAP XML & SMS)"] = (
            f"PASS (HTTP 200, Status: {alt_data['status']}, Dispatched: {alt_data['alerts_count']})"
        )
    except Exception as e:
        results["3e. E2E POST /api/alerts/dispatch (CAP XML & SMS)"] = f"FAIL: {e}"

    # 4. Print Summary Table
    print("\n" + "-" * 80)
    print(f"{'CORE MODULE AUDIT':<52} | {'STATUS':<25}")
    print("-" * 80)
    all_passed = True
    for check, status in results.items():
        pass_fail = "PASS" if status.startswith("PASS") else "FAIL"
        print(f"{check:<52} | {status}")
        if pass_fail != "PASS":
            all_passed = False
    print("-" * 80)
    print("OVERALL STATUS:", "ALL CHECKS PASSED (100%)" if all_passed else "CHECKS FAILED")
    print("=" * 80 + "\n")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
