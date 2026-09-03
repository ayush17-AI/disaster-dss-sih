from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import zones, triage, manifest, routing, alerts

app = FastAPI(title="DRR Triage Backend")

# Add CORSMiddleware BEFORE registering routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all 5 routers with prefix "/api"
app.include_router(zones.router, prefix="/api", tags=["Hazard Zones"])
app.include_router(triage.router, prefix="/api", tags=["Triage Manifest"])
app.include_router(manifest.router, prefix="/api", tags=["Relocation Manifest"])
app.include_router(routing.router, prefix="/api", tags=["Safe Routing"])
app.include_router(alerts.router, prefix="/api", tags=["CAP Alerts"])

@app.get("/")
def root():
    return {"status": "ok", "service": "DRR Triage Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
