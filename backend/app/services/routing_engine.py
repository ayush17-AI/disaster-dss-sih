import os
import osmnx as ox
import networkx as nx
from shapely.geometry import shape, LineString
import shapely.ops

_graph_cache = {}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_graph(region: str):
    """
    Load a road network graph from disk cache or memory cache.
    """
    norm_region = region.lower().strip()
    if norm_region in _graph_cache:
        return _graph_cache[norm_region]
        
    filepath = os.path.join(DATA_DIR, f"{norm_region}_roads.graphml")
    if not os.path.exists(filepath):
        filepath = os.path.join(DATA_DIR, "wayanad_roads.graphml")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Road graph for '{region}' not found at {filepath}")
            
    G = ox.load_graphml(filepath=filepath)
    _graph_cache[norm_region] = G
    return G

def remove_edges_in_red_zones(G, red_zone_polygons):
    """
    Create a copy of G and remove edges intersecting any polygon in red_zone_polygons.
    """
    if not red_zone_polygons:
        return G.copy()
        
    polys = []
    for p in red_zone_polygons:
        if isinstance(p, dict):
            geom = shape(p)
        else:
            geom = p
        if geom.is_valid and not geom.is_empty:
            polys.append(geom)
            
    if not polys:
        return G.copy()
        
    combined_poly = shapely.ops.unary_union(polys)
    minx, miny, maxx, maxy = combined_poly.bounds
    
    G_working = G.copy()
    edges_to_remove = []
    
    for u, v, k in G_working.edges(keys=True):
        u_node = G_working.nodes[u]
        v_node = G_working.nodes[v]
        ux, uy = u_node["x"], u_node["y"]
        vx, vy = v_node["x"], v_node["y"]
        
        # Spatial bounding box quick rejection
        if max(ux, vx) < minx or min(ux, vx) > maxx or max(uy, vy) < miny or min(uy, vy) > maxy:
            continue
            
        edge_geom = LineString([(ux, uy), (vx, vy)])
        if edge_geom.intersects(combined_poly):
            edges_to_remove.append((u, v, k))
            
    if edges_to_remove:
        G_working.remove_edges_from(edges_to_remove)
        
    return G_working

def get_safe_route(region: str, from_lat: float, from_lon: float, to_lat: float, to_lon: float, red_zone_polygons: list = None):
    """
    Compute safe shortest path avoiding red zone polygons with fallback handling.
    """
    G = load_graph(region)
    G_working = remove_edges_in_red_zones(G, red_zone_polygons) if red_zone_polygons else G.copy()
    
    orig_node = ox.distance.nearest_nodes(G_working, from_lon, from_lat)
    dest_node = ox.distance.nearest_nodes(G_working, to_lon, to_lat)
    
    try:
        route = nx.shortest_path(G_working, orig_node, dest_node, weight="length")
        coords = [[G_working.nodes[n]["y"], G_working.nodes[n]["x"]] for n in route]
        distance_km = nx.shortest_path_length(G_working, orig_node, dest_node, weight="length") / 1000.0
        return {
            "path_coordinates": coords,
            "distance_km": round(distance_km, 2),
            "avoids_red_zones": True
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # Fallback to default graph
        try:
            orig_orig = ox.distance.nearest_nodes(G, from_lon, from_lat)
            dest_orig = ox.distance.nearest_nodes(G, to_lon, to_lat)
            route = nx.shortest_path(G, orig_orig, dest_orig, weight="length")
            coords = [[G.nodes[n]["y"], G.nodes[n]["x"]] for n in route]
            distance_km = nx.shortest_path_length(G, orig_orig, dest_orig, weight="length") / 1000.0
            return {
                "path_coordinates": coords,
                "distance_km": round(distance_km, 2),
                "avoids_red_zones": False
            }
        except Exception:
            return {
                "path_coordinates": [[from_lat, from_lon], [to_lat, to_lon]],
                "distance_km": 0.0,
                "avoids_red_zones": False
            }

class RoutingEngine:
    """Wrapper class providing routing engine interface."""
    def __init__(self, region: str = "wayanad"):
        self.region = region
        self.graph = load_graph(region)

    def find_safe_route(self, from_lat: float, from_lon: float, to_lat: float, to_lon: float, red_zones: list = None):
        return get_safe_route(self.region, from_lat, from_lon, to_lat, to_lon, red_zones)
