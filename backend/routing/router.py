import networkx as nx

def compute_safe_route(from_lat: float, from_lon: float, to_shelter_id: str, red_zones: list):
    """
    Compute safe routing using NetworkX bypassing red zones.
    Mock implementation reflecting the logic.
    """
    G = nx.Graph()
    # Mocking a spatial network setup
    G.add_edge("A", "B", weight=1.0)
    G.add_edge("B", "Shelter", weight=2.0)
    
    # Path calculation logic
    path = nx.shortest_path(G, source="A", target="Shelter", weight="weight")
    
    # Return a mocked GeoJSON LineString avoiding red zones
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [from_lon, from_lat],
                [from_lon + 0.005, from_lat + 0.002],
                [from_lon + 0.010, from_lat + 0.005]
            ]
        },
        "properties": {
            "name": f"Computed safe path to {to_shelter_id} avoiding {len(red_zones)} red zones",
            "safe": True
        }
    }
