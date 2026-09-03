import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from shapely.geometry import shape, LineString, Polygon
from app.main import app
from app.services.routing_engine import load_graph, remove_edges_in_red_zones, get_safe_route
from app.models.schemas import RouteResponse

def run_verification():
    results = {}
    print("=" * 70)
    print("STEP 3: ROLE B ROUTING ENGINE VERIFICATION REPORT")
    print("=" * 70)

    # 1. Verify load_graph("wayanad")
    try:
        G = load_graph("wayanad")
        node_count = len(G.nodes)
        edge_count = len(G.edges)
        assert node_count > 10000, f"Expected >10,000 nodes, found {node_count}"
        assert edge_count > 0, "No edges found in graph"
        results["1. Graph Cache Loading (Wayanad)"] = f"PASS ({node_count} nodes, {edge_count} edges)"
    except Exception as e:
        results["1. Graph Cache Loading (Wayanad)"] = f"FAIL: {e}"

    # 2. Direct function test: Compute route without red zones
    from_lat, from_lon = 11.55, 76.10
    to_lat, to_lon = 11.60, 76.15
    initial_route = None
    try:
        initial_route = get_safe_route("wayanad", from_lat, from_lon, to_lat, to_lon, red_zone_polygons=[])
        assert initial_route["distance_km"] > 0, "Distance should be > 0"
        assert len(initial_route["path_coordinates"]) >= 2, "Path coordinates should have at least 2 points"
        assert initial_route["avoids_red_zones"] is True
        results["2. Direct Route Computation (Base Network)"] = (
            f"PASS (Length: {len(initial_route['path_coordinates'])} points, Distance: {initial_route['distance_km']} km)"
        )
    except Exception as e:
        results["2. Direct Route Computation (Base Network)"] = f"FAIL: {e}"

    # 3. Dynamic avoidance test: Intercept path with dummy red polygon
    try:
        G = load_graph("wayanad")
        assert initial_route is not None, "Initial route needed for avoidance test"
        coords = initial_route["path_coordinates"]
        mid_idx = len(coords) // 2
        mid_lat, mid_lon = coords[mid_idx]

        # Construct dummy red polygon around the midpoint
        delta = 0.003
        dummy_poly = {
            "type": "Polygon",
            "coordinates": [[
                [mid_lon - delta, mid_lat - delta],
                [mid_lon + delta, mid_lat - delta],
                [mid_lon + delta, mid_lat + delta],
                [mid_lon - delta, mid_lat + delta],
                [mid_lon - delta, mid_lat - delta]
            ]]
        }
        shapely_poly = shape(dummy_poly)

        # Test edge removal
        G_avoid = remove_edges_in_red_zones(G, [dummy_poly])
        removed_edges = len(G.edges) - len(G_avoid.edges)
        assert removed_edges > 0, f"Expected edges to be eliminated, but removed {removed_edges}"

        # Test route computation bypassing the dummy polygon
        avoid_route = get_safe_route("wayanad", from_lat, from_lon, to_lat, to_lon, red_zone_polygons=[dummy_poly])
        assert len(avoid_route["path_coordinates"]) >= 2, "Avoidance path should be found"

        # Check that no edge in avoid_route intersects shapely_poly
        avoid_coords = avoid_route["path_coordinates"]
        has_intersection = False
        for i in range(len(avoid_coords) - 1):
            p1 = (avoid_coords[i][1], avoid_coords[i][0])      # (lon, lat)
            p2 = (avoid_coords[i+1][1], avoid_coords[i+1][0])  # (lon, lat)
            seg = LineString([p1, p2])
            if seg.crosses(shapely_poly) or shapely_poly.contains(seg):
                has_intersection = True
                break

        assert not has_intersection, "Computed path traverses through red hazard polygon"
        results["3. Dynamic Hazard Avoidance Test"] = (
            f"PASS (Removed {removed_edges} intersecting edges, new route successfully bypassed hazard)"
        )
    except Exception as e:
        results["3. Dynamic Hazard Avoidance Test"] = f"FAIL: {e}"

    # 4. API Test via TestClient(app)
    try:
        client = TestClient(app)
        url = f"/api/route?from_lat={from_lat}&from_lon={from_lon}&to_lat={to_lat}&to_lon={to_lon}&region=wayanad"
        res = client.get(url)
        assert res.status_code == 200, f"HTTP status: {res.status_code}, detail: {res.text}"
        data = res.json()
        validated = RouteResponse.model_validate(data)
        assert len(validated.path_coordinates) >= 2
        assert validated.distance_km > 0
        results["4. API GET /api/route Validation"] = (
            f"PASS (Status 200, Distance: {validated.distance_km} km, Avoids Red Zones: {validated.avoids_red_zones})"
        )
    except Exception as e:
        results["4. API GET /api/route Validation"] = f"FAIL: {e}"

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
