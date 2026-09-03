# Hazard Red-Zoning, Carrying Capacity & Relocation Triage Decision Support System (DSS)

## Overview
This repository contains the source code for the Disaster DSS SIH project.

## Git Branch Guidance
We follow a 3-role workflow for development:
- `main` (Protected) - Production ready code.
- `role-a-geo` (Owns `/backend/geo_engine`) - Focuses on geospatial formulas and algorithms.
- `role-b-backend` (Owns `/backend/api`, `/backend/routing`) - Focuses on API endpoints, routing logic, and backend infrastructure.
- `role-c-frontend` (Owns `/frontend`) - Focuses on the user interface and client-side logic.
