import sys, os

print('=' * 60)
print('FINAL SANITY AUDIT: STEP 1 RE-CHECK')
print('=' * 60)

# 1. Branch verification
import subprocess
branch = subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()
print(f'[CHECK 1] Active Git Branch: {branch}')
assert branch == 'role-b-backend', f'Wrong branch: {branch}'

# 2. Dependency & Version checks
import pydantic, fastapi, uvicorn, osmnx, networkx, geopandas, shapely, reportlab, lxml, apscheduler, dotenv, requests
print(f'[CHECK 2] Locked Dependencies Import: SUCCESS')
pydantic_major = int(pydantic.__version__.split('.')[0])
print(f'[CHECK 3] Pydantic Version: {pydantic.__version__} (Major >= 2: {pydantic_major >= 2})')
assert pydantic_major >= 2, 'Pydantic is not v2.x'

# 3. GraphML disk check
wayanad_path = 'backend/data/wayanad_roads.graphml'
assam_path = 'backend/data/assam_roads.graphml'

assert os.path.exists(wayanad_path), f'Missing: {wayanad_path}'
assert os.path.exists(assam_path), f'Missing: {assam_path}'

w_size = os.path.getsize(wayanad_path) / (1024 * 1024)
a_size = os.path.getsize(assam_path) / (1024 * 1024)
print(f'[CHECK 4] Cached Road Graphs on Disk:')
print(f'         - Wayanad ({w_size:.2f} MB): FOUND')
print(f'         - Assam ({a_size:.2f} MB): FOUND')

# 4. In-memory topological graph sanity
G_w = osmnx.load_graphml(wayanad_path)
G_a = osmnx.load_graphml(assam_path)
print(f'[CHECK 5] In-Memory Topology Validation:')
print(f'         - Wayanad Graph Nodes: {len(G_w)}, Edges: {len(G_w.edges)}')
print(f'         - Assam Graph Nodes: {len(G_a)}, Edges: {len(G_a.edges)}')
assert len(G_w) > 5000 and len(G_a) > 3000, 'Graph nodes count suspiciously low'

print('=' * 60)
print('RESULT: STEP 1 AUDIT FULLY VERIFIED & 100% READY FOR STEP 2')
print('=' * 60)
