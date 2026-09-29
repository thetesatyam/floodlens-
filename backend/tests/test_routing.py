"""
FloodLens — Routing Engine Tests (Samartha)
Run with:  python -m pytest tests/test_routing.py -v
           (from the backend/ directory)
"""

import pytest
import sys
import os

# Make sure backend/ is on the path when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from routing_engine.graph_data import EDGES, NODES, DEFAULT_ROAD_STATUSES
from routing_engine.router import find_route


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reset_all_roads():
    """Restore every edge to its default status before each test."""
    for edge in EDGES:
        edge["status"] = DEFAULT_ROAD_STATUSES[edge["id"]]


def set_road_status(road_id: str, status: str):
    for edge in EDGES:
        if edge["id"] == road_id:
            edge["status"] = status
            return
    raise ValueError(f"Road {road_id!r} not found")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_roads():
    """Auto-reset road statuses before every test."""
    reset_all_roads()
    yield
    reset_all_roads()


# ---------------------------------------------------------------------------
# Test 1: Basic happy-path route (all roads open)
# ---------------------------------------------------------------------------

def test_basic_route_found():
    result = find_route("S001", "EC001")
    assert result["valid"] is True
    assert len(result["path"]) >= 2
    assert result["path"][0] == "S001"
    assert result["path"][-1] == "EC001"
    assert result["total_distance_km"] > 0


# ---------------------------------------------------------------------------
# Test 2: Route never uses a closed road
# ---------------------------------------------------------------------------

def test_route_avoids_closed_roads():
    # Close the direct Shirol–Kurundwad link and Shirol–Hatkanangale bypass
    set_road_status("R001", "closed")   # S001 ↔ S002
    set_road_status("R007", "closed")   # S001 ↔ S003

    # S001 is now completely isolated → no route should exist
    result = find_route("S001", "EC001")
    assert result["valid"] is False
    assert result["path"] == []
    assert result["total_distance_km"] == 0.0

    # Confirm the message is informative
    assert "blocked" in result["message"].lower() or "no valid route" in result["message"].lower()


# ---------------------------------------------------------------------------
# Test 3: Closed roads are never in the returned path
# ---------------------------------------------------------------------------

def test_path_contains_no_closed_road_edges():
    # Close R001 but leave alternatives open
    set_road_status("R001", "closed")   # S001 ↔ S002 direct link

    result = find_route("S001", "S002")
    # Route should still be found via S001→S003→S002 (if that path exists) or similar
    if result["valid"]:
        closed_road_ids = {e["id"] for e in EDGES if e["status"] == "closed"}
        for road in result["roads_used"]:
            assert road["road_id"] not in closed_road_ids, (
                f"Route includes closed road {road['road_id']}"
            )


# ---------------------------------------------------------------------------
# Test 4: "No valid route" when graph is fully disconnected
# ---------------------------------------------------------------------------

def test_no_route_when_fully_disconnected():
    # Close every road connecting S001 to the rest of the network
    set_road_status("R001", "closed")   # S001 ↔ S002
    set_road_status("R007", "closed")   # S001 ↔ S003

    result = find_route("S001", "EC001")
    assert result["valid"] is False
    assert result["path"] == []


# ---------------------------------------------------------------------------
# Test 5: Moderate roads are included but flagged
# ---------------------------------------------------------------------------

def test_moderate_road_included_and_flagged():
    # Make R001 moderate
    set_road_status("R001", "moderate")

    result = find_route("S001", "S002")
    assert result["valid"] is True
    # At least one road should be moderate (Dijkstra might still pick it)
    road_statuses = {r["status"] for r in result["roads_used"]}
    # has_moderate_roads flag must be consistent with roads_used
    has_mod_in_roads = "moderate" in road_statuses
    assert result["has_moderate_roads"] == has_mod_in_roads


# ---------------------------------------------------------------------------
# Test 6: Same origin and destination
# ---------------------------------------------------------------------------

def test_same_origin_destination():
    result = find_route("S001", "S001")
    assert result["valid"] is False
    assert "same" in result["message"].lower()


# ---------------------------------------------------------------------------
# Test 7: Unknown node IDs
# ---------------------------------------------------------------------------

def test_unknown_node_id():
    result = find_route("INVALID", "EC001")
    assert result["valid"] is False

    result2 = find_route("S001", "BADNODE")
    assert result2["valid"] is False


# ---------------------------------------------------------------------------
# Test 8: Emergency center is reachable from all settlements by default
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("settlement_id", ["S001", "S002", "S003", "S004", "S005"])
def test_all_settlements_reach_emergency_center(settlement_id):
    result = find_route(settlement_id, "EC001")
    assert result["valid"] is True, (
        f"{settlement_id} cannot reach EC001: {result['message']}"
    )


# ---------------------------------------------------------------------------
# Test 9: Closing flood simulation roads blocks low-lying settlements
# ---------------------------------------------------------------------------

def test_flood_simulation_road_closure():
    # Simulate the same road changes as /api/simulation/trigger-flood
    set_road_status("R001", "closed")   # Shirol–Kurundwad
    set_road_status("R002", "closed")   # Kurundwad–Hatkanangale
    set_road_status("R003", "moderate") # Hatkanangale–Karveer

    # S001 loses R001 and R007-based paths need to be checked
    result_s001 = find_route("S001", "EC001")
    # Either finds alternate or reports no route — never uses R001 or R002
    for road in result_s001.get("roads_used", []):
        assert road["road_id"] not in ("R001", "R002"), (
            "Route used a closed flood road"
        )

    # S002 loses both direct connections
    result_s002 = find_route("S002", "EC001")
    for road in result_s002.get("roads_used", []):
        assert road["road_id"] not in ("R001", "R002"), (
            "Route used a closed flood road"
        )
