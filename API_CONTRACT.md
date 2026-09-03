# API Contract

## System Enums
- `operating_mode`: `"MOUNTAIN_CASCADE"` | `"PLAINS_INUNDATION"` | `"TRANSITIONAL"`
- `zone_color`: `"RED"` | `"YELLOW"` | `"GREEN"`
- `triage_priority`: `1` | `2` | `3`
- `authorization_status`: `"PENDING_REVIEW"` | `"AUTHORIZED"`

## Endpoints

### 1. GET /api/zones
- **Description:** Retrieve hazard zones based on region and parameters.
- **Parameters:**
  - `region` (string, required)
  - `rainfall_intensity` (float, required)
  - `construction_load` (float, required)
- **Response:** GeoJSON FeatureCollection

### 2. GET /api/triage
- **Description:** Retrieve ranked triage manifest.
- **Parameters:**
  - `region` (string, required)
- **Response:** Ranked triage manifest JSON

### 3. GET /api/route
- **Description:** Get safe route avoiding red zones.
- **Parameters:**
  - `from_lat` (float, required)
  - `from_lon` (float, required)
  - `to_shelter_id` (string, required)
- **Response:** Safe route GeoJSON Feature (LineString)

### 4. POST /api/manifest/authorize
- **Description:** Authorize a triage manifest.
- **Payload:** JSON payload with authorization details.
- **Response:** PDF/CSV link & order authorization status.

### 5. GET /api/alerts/cap-payload
- **Description:** Get NDMA Sachet/CAP compliant XML & SMS text.
- **Parameters:**
  - `habitation_id` (string, required)
- **Response:** JSON with CAP XML and SMS text
