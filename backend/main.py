"""
FloodLens — FastAPI backend
Combines Shubham's Risk Engine + Samartha's Routing Engine
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from risk_engine.data import settlements
from risk_engine.risk_engine import calculate_risk

from routing_engine.graph_data import EDGES, NODES, DEFAULT_ROAD_STATUSES
from routing_engine.router import find_route

# ---------------------------------------------------------------------------
# App setup (single instance — fixes the duplicate-app bug)
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FloodLens API",
    description="Trust-weighted flood risk scoring + road routing for Kolhapur district",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "FloodLens API — Risk Engine + Routing Engine",
        "status": "running",
        "docs": "/docs",
    }


# ===========================================================================
# RISK ENGINE  (Shubham's endpoints — unchanged)
# ===========================================================================

@app.get("/api/settlements")
def get_settlements():
    result = []
    for settlement in settlements:
        risk = calculate_risk(settlement)
        result.append({
            "id": settlement["id"],
            "name": settlement["name"],
            "lat": settlement["lat"],
            "lng": settlement["lng"],
            "population": settlement["population"],
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "confidence_pct": risk["confidence_pct"],
        })
    return {"settlements": result}


@app.get("/api/settlements/{settlement_id}/risk")
def get_settlement_risk(settlement_id: str):
    settlement = next(
        (s for s in settlements if s["id"] == settlement_id), None
    )
    if settlement is None:
        raise HTTPException(status_code=404, detail="Settlement not found")

    risk = calculate_risk(settlement)
    return {
        "settlement": {
            "id": settlement["id"],
            "name": settlement["name"],
            "lat": settlement["lat"],
            "lng": settlement["lng"],
        },
        "risk": {
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "confidence_pct": risk["confidence_pct"],
        },
        "evidence": risk["evidence"],
    }


# ===========================================================================
# ROUTING ENGINE  (Samartha's endpoints)
# ===========================================================================

# ── GET /api/roads ─────────────────────────────────────────────────────────

@app.get("/api/roads")
def get_roads():
    """
    Return all road edges with their current status and node metadata.
    Frontend uses this to colour roads on the Leaflet map.
    """
    roads = []
    for edge in EDGES:
        from_node = NODES[edge["from_node"]]
        to_node   = NODES[edge["to_node"]]
        roads.append({
            "id": edge["id"],
            "name": edge["name"],
            "from_node": {
                "id":   edge["from_node"],
                "name": from_node["name"],
                "lat":  from_node["lat"],
                "lng":  from_node["lng"],
            },
            "to_node": {
                "id":   edge["to_node"],
                "name": to_node["name"],
                "lat":  to_node["lat"],
                "lng":  to_node["lng"],
            },
            "length_km": edge["length_km"],
            "status": edge["status"],
        })

    # Also expose node list (so frontend can render EC001 marker)
    nodes = [
        {
            "id": node_id,
            "name": attrs["name"],
            "lat": attrs["lat"],
            "lng": attrs["lng"],
            "type": attrs["type"],
        }
        for node_id, attrs in NODES.items()
    ]

    return {"roads": roads, "nodes": nodes}


# ── PATCH /api/roads/{id}/status ───────────────────────────────────────────

class RoadStatusUpdate(BaseModel):
    status: str  # "open" | "moderate" | "closed"


@app.patch("/api/roads/{road_id}/status")
def update_road_status(road_id: str, body: RoadStatusUpdate):
    """
    Manually set a road's status (used by Simulate Flood / manual override).
    """
    valid_statuses = {"open", "moderate", "closed"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{body.status}'. Must be one of: {valid_statuses}",
        )

    edge = next((e for e in EDGES if e["id"] == road_id), None)
    if edge is None:
        raise HTTPException(status_code=404, detail=f"Road '{road_id}' not found")

    old_status = edge["status"]
    edge["status"] = body.status

    return {
        "road_id": road_id,
        "name": edge["name"],
        "previous_status": old_status,
        "new_status": edge["status"],
    }


# ── POST /api/route ────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    from_node_id: str
    to_node_id: str


@app.post("/api/route")
def get_route(body: RouteRequest):
    """
    Find the shortest valid rescue route between two nodes, skipping any
    closed roads. Penalises moderate roads (2× cost).

    Response includes the full path, per-road evidence, and a 'valid' flag
    so the frontend can clearly show "No valid route" when blocked.
    """
    result = find_route(body.from_node_id, body.to_node_id)
    if not result["valid"]:
        # Still return 200 with valid=false — not a server error
        return result
    return result


# ===========================================================================
# SIMULATION ENDPOINTS  (Shubham's + road status wired in by Samartha)
# ===========================================================================

@app.post("/api/simulation/trigger-flood")
def trigger_flood():
    """
    Simulate a severe flood:
      - Raises rainfall for all settlements by 50 mm
      - Closes two flood-prone roads (R001 Shirol–Kurundwad, R002 Kurundwad–Hatkanangale)
      - Sets R003 Hatkanangale–Karveer to moderate
    """
    # Risk engine: bump rainfall
    for settlement in settlements:
        settlement["rainfall_mm_24h"] += 50

    # Routing engine: close flood-prone roads
    flood_road_changes = {
        "R001": "closed",    # Shirol–Kurundwad — low-lying, river crossing
        "R002": "closed",    # Kurundwad–Hatkanangale — historically flooded
        "R003": "moderate",  # Hatkanangale–Karveer — partially passable
    }
    for edge in EDGES:
        if edge["id"] in flood_road_changes:
            edge["status"] = flood_road_changes[edge["id"]]

    return {
        "message": "Flood simulation triggered — rainfall raised, 2 roads closed, 1 degraded",
        "road_changes": flood_road_changes,
        "settlements": [
            {
                "id": s["id"],
                "name": s["name"],
                "rainfall_mm_24h": s["rainfall_mm_24h"],
                "risk": calculate_risk(s),
            }
            for s in settlements
        ],
    }


@app.post("/api/simulation/reset")
def reset_simulation():
    """
    Reset rainfall and road statuses to their defaults.
    """
    default_rainfall = {
        "S001": 45,
        "S002": 40,
        "S003": 30,
        "S004": 25,
        "S005": 35,
    }

    # Reset risk engine
    for settlement in settlements:
        settlement["rainfall_mm_24h"] = default_rainfall[settlement["id"]]

    # Reset routing engine
    for edge in EDGES:
        edge["status"] = DEFAULT_ROAD_STATUSES[edge["id"]]

    return {
        "message": "Simulation reset — rainfall and road statuses restored to defaults",
        "roads": [{"id": e["id"], "status": e["status"]} for e in EDGES],
    }