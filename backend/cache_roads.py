import os
import sys
import osmnx as ox

# Configure osmnx settings
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.timeout = 300

os.makedirs("backend/data", exist_ok=True)

targets = [
    ("Wayanad, Kerala, India", "backend/data/wayanad_roads.graphml"),
    ("Kamrup, Assam, India", "backend/data/assam_roads.graphml")
]

for place, filepath in targets:
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        print(f"Already cached: {filepath}")
        continue
    print(f"Downloading road network for: {place} ...")
    try:
        G = ox.graph_from_place(place, network_type="drive", simplify=True)
        ox.save_graphml(G, filepath=filepath)
        print(f"Successfully saved {place} to {filepath} (nodes: {len(G.nodes)}, edges: {len(G.edges)})")
    except Exception as e:
        print(f"Failed to download {place}: {e}", file=sys.stderr)
        sys.exit(1)

print("Road network caching completed successfully.")
