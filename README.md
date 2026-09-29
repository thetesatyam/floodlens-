# FloodLens — Trust-Weighted Flood Warning & Response Coordination Platform

**Hack Matrix 5.0 · Round 1 Submission**

## Problem Statement
Communities may receive a flood warning without knowing which roads are still
usable or where help is needed first. FloodLens connects hazard warnings with
affected settlements and road accessibility, using environmental data and
citizen ground reports, to explain each alert and help response teams
prioritize action.

**Scope:** Flood hazard · Kolhapur district, Maharashtra · historical/simulated data

## What makes this different
Most flood dashboards stop at "risk: high." FloodLens shows **why** — every
alert ships with its rainfall, elevation, historical-risk, and ground-report
evidence, plus a confidence percentage. Citizen reports are **trust-weighted**:
each report's reliability is scored from corroboration with nearby reports and
agreement with rainfall data, and that trust score feeds directly into both
alert confidence and route safety.

## Architecture
Rainfall + Terrain Data → Risk Engine → Affected Settlements
→ Road Accessibility + Trust-Weighted Ground Reports
→ Evidence & Confidence → Response Priority
→ Route Planning (Dijkstra, avoids closed roads)
→ Dashboard


## Tech Stack
- **Frontend:** HTML + Leaflet + OpenStreetMap tiles
- **Backend:** FastAPI (Python)
- **Routing:** NetworkX (Dijkstra), closed roads always excluded
- **Scoring:** transparent, rule-based (no black-box ML) — see "AI/ML roadmap" below

## Project Structure
backend/
main.py — FastAPI app, all endpoints
risk_engine/
data.py — 5 Kolhapur settlements (hardcoded for MVP)
risk_engine.py — risk scoring + trust-score formula
routing_engine/
graph_data.py — road network (nodes + edges)
router.py — Dijkstra routing, closed-road avoidance
tests/
test_routing.py — route validity test suite
index.html — Leaflet map (settlements, roads, simulation controls)
report.html — citizen ground-report submission form
sim-controls.js — wires Simulate Flood / Reset buttons to the backend


## Running it locally
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend runs at `http://localhost:8000` (interactive docs at `/docs`).

Then open `index.html` (via VS Code Live Server or `python -m http.server`)
with `USE_LIVE_BACKEND = true` set near the top of the script.

## API Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/settlements` | List all settlements with current risk |
| GET | `/api/settlements/{id}/risk` | Evidence + confidence for one settlement |
| GET | `/api/roads` | All road edges + status, plus node list |
| PATCH | `/api/roads/{id}/status` | Manually change a road's status |
| POST | `/api/route` | Shortest valid route, avoiding closed roads |
| POST | `/api/reports` | Submit a citizen ground report, get a trust score |
| POST | `/api/simulation/trigger-flood` | Demo: raise rainfall, close roads |
| POST | `/api/simulation/reset` | Restore baseline conditions |

## Testing
```bash
cd backend
python -m pytest tests/test_routing.py -v
```
Covers: routes never use closed roads, "no valid route" when disconnected,
moderate-road penalty, all settlements reachable from the emergency center.

## AI/ML Roadmap (Round 2)
The current risk/trust engine is intentionally rule-based and explainable for
the MVP. Round 2 extends the same pipeline with an ML classifier (rainfall +
terrain + report-text features) to refine the flood-risk score, and
NLP-based validation of report text to strengthen trust-weighting — without
changing the architecture.

## Team
- [Shubham Ugale] — Backend: Risk Engine
- [Samarth Toge] — Backend: Routing Engine
- [Satyam Thete] — Frontend: Map
- [Sanket Tendulkar] — Ground Reports UI, Simulation Wiring, Integration

## Known limitations (Round 1 scope)
- Data is in-memory only (resets on backend restart) — no persistent database yet
- 5 settlements and ~9 road edges, hand-curated for one district (Kolhapur)
- Rainfall/historical data is replayed/simulated, clearly not live