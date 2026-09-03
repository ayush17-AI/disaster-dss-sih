import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from shapely.geometry import shape, LineString
from app.main import app
from app.services.routing_engine import load_graph, remove_edges_in_red_zones, get_safe_route
from app.models.schemas import RouteResponse

def run_verification():
    results = {}
    print("=" * 75)
    print("SECTION 4.2: ROLE B ROUTING ENGINE AUDIT REPORT")
    print("=" * 75)

    # 1. Load cached graph wayanad and verify node count > 5,000
    try:
        G = load_graph("wayanad")
        node_count = len(G.nodes)
        edge_count = len(G.edges)
        assert node_count > 5000, f"Expected >5000 nodes, got {node_count}"
        assert edge_count > 0, "No edges in graph"
        results["1. Graph Cache Loading (Wayanad)"] = f"PASS ({node_count} nodes, {edge_count} edges)"
    except Exception as e:
        results["1. Graph Cache Loading (Wayanad)"] = f"FAIL: {e}"

    # 2. Direct calculation test: compute route with zero red zones; assert distance > 0
    from_lat, from_lon = 11.55, 76.10
    to_lat, to_lon = 11.60, 76.15
    initial_route = None
    try:
        initial_route = get_safe_route("wayanad", from_lat, from_lon, to_lat, to_lon, red_zone_polygons=[])
        assert initial_route["distance_km"] > 0, "Route distance should be > 0"
        assert len(initial_route["path_coordinates"]) >= 2, "Path coordinates should have >= 2 points"
        assert initial_route["avoids_red_zones"] is True, "Expected avoids_red_zones to be True"
        results["2. Direct Route Calculation (Zero Red Zones)"] = (
            f"PASS ({len(initial_route['path_coordinates'])} waypoints, {initial_route['distance_km']} km)"
        )
    except Exception as e:
        results["2. Direct Route Calculation (Zero Red Zones)"] = f"FAIL: {e}"

    # 3. Hazard avoidance test: supply polygon intercepting path; assert edges removed and path routes around hazard
    try:
        G = load_graph("wayanad")
        assert initial_route is not None, "Baseline route is required for avoidance testing"
        coords = initial_route["path_coordinates"]
        mid_idx = len(coords) // 2
        mid_lat, mid_lon = coords[mid_idx]

        # Construct intercepting polygon around the midpoint
        delta = 0.003
        intercepting_poly = {
            "type": "Polygon",
            "coordinates": [[
                [mid_lon - delta, mid_lat - delta],
                [mid_lon + delta, mid_lat - delta],
                [mid_lon + delta, mid_lat + delta],
                [mid_lon - delta, mid_lat + delta],
                [mid_lon - delta, mid_lat - delta]
            ]]
        }
        shapely_poly = shape(intercepting_poly)

        # Confirm edges are removed
        G_filtered = remove_edges_in_red_zones(G, [intercepting_poly])
        eliminated_edges = len(G.edges) - len(G_filtered.edges)
        assert eliminated_edges > 0, f"Expected eliminated edges > 0, got {eliminated_edges}"

        # Compute safe detour path
        safe_route = get_safe_route("wayanad", from_lat, from_lon, to_lat, to_lon, red_zone_polygons=[intercepting_poly])
        assert len(safe_route["path_coordinates"]) >= 2, "Safe route should contain waypoints"

        # Check that no edge segment in safe route traverses through intercepting_poly
        safe_coords = safe_route["path_coordinates"]
        intersects_hazard = False
        for i in range(len(safe_coords) - 1):
            p1 = (safe_coords[i][1], safe_coords[i][0])      # (lon, lat)
            p2 = (safe_coords[i+1][1], safe_coords[i+1][0])  # (lon, lat)
            segment = LineString([p1, p2])
            if segment.crosses(shapely_poly) or shapely_poly.contains(segment):
                intersects_hazard = True
                break

        assert not intersects_hazard, "Computed path still intersects the hazard zone"
        results["3. Dynamic Hazard Avoidance Test"] = (
            f"PASS (Eliminated {eliminated_edges} edges, path rerouted without intersecting hazard)"
        )
    except Exception as e:
        results["3. Dynamic Hazard Avoidance Test"] = f"FAIL: {e}"

    # 4. API test: GET /api/route via TestClient(app)
    try:
        client = TestClient(app)
        query = f"/api/route?from_lat={from_lat}&from_lon={from_lon}&to_lat={to_lat}&to_lon={to_lon}&region=wayanad"
        res = client.get(query)
        assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
        data = res.json()
        validated = RouteResponse.model_validate(data)
        assert len(validated.path_coordinates) >= 2, "Expected >= 2 coordinates in response"
        assert validated.distance_km > 0, "Distance should be > 0"
        results["4. API Endpoint GET /api/route Verification"] = (
            f"PASS (HTTP 200, Distance: {validated.distance_km} km, Avoids Red Zones: {validated.avoids_red_zones})"
        )
    except Exception as e:
        results["4. API Endpoint GET /api/route Verification"] = f"FAIL: {e}"

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
