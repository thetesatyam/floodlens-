"""
FloodLens — Road Network Graph Data (Kolhapur District)
Nodes : S001–S005 (settlements, aligned with risk_engine/data.py) + EC001 (Emergency Center)
Edges : ~9 roads, each with a length_km and a mutable status field
"""

# ---------------------------------------------------------------------------
# Nodes — settlements mirror risk_engine/data.py IDs exactly
# ---------------------------------------------------------------------------
NODES = {
    "S001": {"name": "Shirol",          "lat": 16.7804, "lng": 74.6056, "type": "settlement"},
    "S002": {"name": "Kurundwad",       "lat": 16.6850, "lng": 74.5880, "type": "settlement"},
    "S003": {"name": "Hatkanangale",    "lat": 16.7450, "lng": 74.3470, "type": "settlement"},
    "S004": {"name": "Panhala",         "lat": 16.8120, "lng": 74.1110, "type": "settlement"},
    "S005": {"name": "Karveer",         "lat": 16.7050, "lng": 74.2430, "type": "settlement"},
    "EC001": {"name": "Kolhapur Emergency Center", "lat": 16.7050, "lng": 74.2432, "type": "emergency_center"},
}

# ---------------------------------------------------------------------------
# Edges — list of dicts; each edge is UNDIRECTED (stored once, treated both ways)
# status: "open" | "moderate" | "closed"
# ---------------------------------------------------------------------------
EDGES = [
    {
        "id": "R001",
        "from_node": "S001",
        "to_node": "S002",
        "name": "Shirol–Kurundwad Road",
        "length_km": 11.2,
        "status": "open",
    },
    {
        "id": "R002",
        "from_node": "S002",
        "to_node": "S003",
        "name": "Kurundwad–Hatkanangale Road",
        "length_km": 26.5,
        "status": "open",
    },
    {
        "id": "R003",
        "from_node": "S003",
        "to_node": "S005",
        "name": "Hatkanangale–Karveer Road",
        "length_km": 14.8,
        "status": "open",
    },
    {
        "id": "R004",
        "from_node": "S005",
        "to_node": "S004",
        "name": "Karveer–Panhala Road",
        "length_km": 20.3,
        "status": "open",
    },
    {
        "id": "R005",
        "from_node": "S005",
        "to_node": "EC001",
        "name": "Karveer–Emergency Center Link",
        "length_km": 0.3,
        "status": "open",
    },
    {
        "id": "R006",
        "from_node": "S003",
        "to_node": "EC001",
        "name": "Hatkanangale–Emergency Center Road",
        "length_km": 15.2,
        "status": "open",
    },
    {
        "id": "R007",
        "from_node": "S001",
        "to_node": "S003",
        "name": "Shirol–Hatkanangale Bypass",
        "length_km": 38.4,
        "status": "open",
    },
    {
        "id": "R008",
        "from_node": "S002",
        "to_node": "EC001",
        "name": "Kurundwad–Emergency Center Road",
        "length_km": 41.6,
        "status": "open",
    },
    {
        "id": "R009",
        "from_node": "S004",
        "to_node": "EC001",
        "name": "Panhala–Emergency Center Road",
        "length_km": 29.1,
        "status": "open",
    },
]

# ---------------------------------------------------------------------------
# Default snapshot — used by /api/simulation/reset
# ---------------------------------------------------------------------------
DEFAULT_ROAD_STATUSES = {edge["id"]: edge["status"] for edge in EDGES}
