import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.services.manifest_generator import generate_manifest_pdf, STATIC_MANIFESTS_DIR

def run_verification():
    results = {}
    print("=" * 75)
    print("SECTION 4.3: ROLE B MANIFEST GENERATION AUDIT REPORT")
    print("=" * 75)

    test_pdf_path = os.path.join(STATIC_MANIFESTS_DIR, "audit_test_manifest.pdf")
    
    # 1. Direct service call generates valid PDF > 2 KB
    try:
        sample_hab = {
            "habitation_id": "hab_001",
            "name": "Mundakkai Settlement",
            "priority_rank": 1,
            "rts_score": 0.88,
            "struct_load": 1.35,
            "tti_hours": 2.5,
            "svi": 0.74,
            "demo_exposure": 420.0,
            "lat": 11.538,
            "lon": 76.155
        }
        res = generate_manifest_pdf(sample_hab, test_pdf_path, "District Magistrate, Wayanad")
        assert os.path.exists(test_pdf_path), "Generated PDF file does not exist on disk"
        size_bytes = os.path.getsize(test_pdf_path)
        assert size_bytes > 2048, f"File size too small ({size_bytes} bytes), expected > 2048 bytes (>2KB)"
        results["1. Direct PDF Generation (Size > 2 KB)"] = f"PASS ({size_bytes} bytes, order_id: {res['order_id']})"
    except Exception as e:
        results["1. Direct PDF Generation (Size > 2 KB)"] = f"FAIL: {e}"

    # 2. File header verification: confirm %PDF- magic bytes
    try:
        with open(test_pdf_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-", f"Invalid PDF header: {header}"
        results["2. PDF File Header Magic Bytes (%PDF-)"] = f"PASS (Magic Header: {header.decode()})"
    except Exception as e:
        results["2. PDF File Header Magic Bytes (%PDF-)"] = f"FAIL: {e}"

    # 3. API test via TestClient(app): POST /api/manifest/hab_001/authorize
    client = TestClient(app)
    download_url = None
    try:
        payload = {
            "habitation_id": "hab_001",
            "authorized_by": "District Magistrate, Wayanad"
        }
        api_res = client.post("/api/manifest/hab_001/authorize", json=payload)
        assert api_res.status_code == 200, f"HTTP {api_res.status_code}: {api_res.text}"
        data = api_res.json()
        assert data.get("status") == "AUTHORIZED", f"Expected status AUTHORIZED, got {data.get('status')}"
        assert "order_id" in data and len(data["order_id"]) > 0, "Missing order_id"
        download_url = data.get("download_url")
        assert download_url and download_url.startswith("/static/manifests/"), f"Invalid download_url: {download_url}"
        results["3. API POST /api/manifest/{hab_id}/authorize"] = (
            f"PASS (Status 200, Order: {data['order_id']}, URL: {download_url})"
        )
    except Exception as e:
        results["3. API POST /api/manifest/{hab_id}/authorize"] = f"FAIL: {e}"

    # 4. Static route download test: GET download_url
    try:
        assert download_url is not None, "Missing download_url from previous check"
        dl_res = client.get(download_url)
        assert dl_res.status_code == 200, f"HTTP {dl_res.status_code}: {dl_res.text}"
        content_type = dl_res.headers.get("content-type", "")
        assert "application/pdf" in content_type, f"Expected application/pdf, got {content_type}"
        assert len(dl_res.content) > 2048, f"Downloaded content too small ({len(dl_res.content)} bytes)"
        assert dl_res.content[:5] == b"%PDF-", "Downloaded file magic bytes mismatch"
        results["4. Static File Download (content-type: application/pdf)"] = (
            f"PASS (HTTP 200, Content-Type: {content_type}, Size: {len(dl_res.content)} bytes)"
        )
    except Exception as e:
        results["4. Static File Download (content-type: application/pdf)"] = f"FAIL: {e}"

    # 5. Print summary table
    print("\n" + "-" * 75)
    print(f"{'CHECK':<48} | {'STATUS':<20}")
    print("-" * 75)
    all_passed = True
    for check, status in results.items():
        pass_fail = "PASS" if status.startswith("PASS") else "FAIL"
        print(f"{check:<48} | {status}")
        if pass_fail != "PASS":
            all_passed = False
    print("-" * 75)
    print("OVERALL STATUS:", "ALL CHECKS PASSED (100%)" if all_passed else "CHECKS FAILED")
    print("=" * 75 + "\n")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
