import os
import sys

def verify():
    results = {}
    
    # 1. Check imports
    modules = [
        "fastapi", "uvicorn", "pydantic", "osmnx", "networkx",
        "geopandas", "shapely", "reportlab", "lxml", "apscheduler",
        "dotenv", "requests"
    ]
    import_failures = []
    for mod in modules:
        try:
            __import__(mod)
        except ModuleNotFoundError as e:
            import_failures.append((mod, str(e)))
        except Exception as e:
            import_failures.append((mod, str(e)))

    if not import_failures:
        results["1. Locked Libraries Import"] = "PASS"
    else:
        results["1. Locked Libraries Import"] = f"FAIL ({import_failures})"

    # 2. Pydantic major version 2.x
    try:
        import pydantic
        version = pydantic.__version__
        major = int(version.split(".")[0])
        if major == 2:
            results["2. Pydantic v2.x Check"] = f"PASS (v{version})"
        else:
            results["2. Pydantic v2.x Check"] = f"FAIL (found v{version}, expected 2.x)"
    except Exception as e:
        results["2. Pydantic v2.x Check"] = f"FAIL ({e})"

    # 3. Cached files exist on disk with size > 0
    wayanad_path = os.path.join("backend", "data", "wayanad_roads.graphml")
    assam_path = os.path.join("backend", "data", "assam_roads.graphml")
    
    w_exists = os.path.isfile(wayanad_path) and os.path.getsize(wayanad_path) > 0
    a_exists = os.path.isfile(assam_path) and os.path.getsize(assam_path) > 0

    if w_exists and a_exists:
        w_size = os.path.getsize(wayanad_path) / (1024 * 1024)
        a_size = os.path.getsize(assam_path) / (1024 * 1024)
        results["3. Cached GraphML Files on Disk"] = f"PASS (Wayanad: {w_size:.2f} MB, Assam: {a_size:.2f} MB)"
    else:
        results["3. Cached GraphML Files on Disk"] = f"FAIL (Wayanad exists: {w_exists}, Assam exists: {a_exists})"

    # 4. Load via ox.load_graphml() and verify nodes & edges > 0
    try:
        import osmnx as ox
        w_graph = ox.load_graphml(filepath=wayanad_path)
        w_nodes, w_edges = len(w_graph.nodes), len(w_graph.edges)
        
        a_graph = ox.load_graphml(filepath=assam_path)
        a_nodes, a_edges = len(a_graph.nodes), len(a_graph.edges)
        
        if w_nodes > 0 and w_edges > 0 and a_nodes > 0 and a_edges > 0:
            results["4. GraphML Topological Graph Validation"] = (
                f"PASS (Wayanad: {w_nodes} nodes, {w_edges} edges | Assam: {a_nodes} nodes, {a_edges} edges)"
            )
        else:
            results["4. GraphML Topological Graph Validation"] = (
                f"FAIL (Wayanad: {w_nodes} nodes, {w_edges} edges | Assam: {a_nodes} nodes, {a_edges} edges)"
            )
    except Exception as e:
        results["4. GraphML Topological Graph Validation"] = f"FAIL ({e})"

    # Print summary
    print("\n" + "="*70)
    print("STEP 1: ROLE B BACKEND VERIFICATION REPORT")
    print("="*70)
    all_pass = True
    for check, status in results.items():
        print(f"[{'PASS' if status.startswith('PASS') else 'FAIL'}] {check}: {status}")
        if not status.startswith("PASS"):
            all_pass = False
    print("="*70)
    print("OVERALL STATUS:", "ALL CHECKS PASSED" if all_pass else "CHECKS FAILED")
    print("="*70 + "\n")
    
    if not all_pass:
        sys.exit(1)

if __name__ == "__main__":
    verify()
