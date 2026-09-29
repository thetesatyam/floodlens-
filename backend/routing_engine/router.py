"""
FloodLens — Routing Engine (Samartha's module)

Builds a NetworkX undirected graph from graph_data.EDGES, treating "closed"
edges as impassable.  Exposes:
    build_graph(exclude_closed)  → nx.Graph
    find_route(from_id, to_id)   → dict with path, distance, validity
"""

from typing import Optional
import networkx as nx

from routing_engine.graph_data import EDGES, NODES


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(exclude_closed: bool = True) -> nx.Graph:
    """
    Build an undirected weighted graph from the current EDGES state.

    If exclude_closed is True (default), edges whose status == "closed"
    are omitted so Dijkstra can never traverse them.

    Edges with status == "moderate" are included but their effective weight
    is doubled to represent higher traversal cost / risk.
    """
    G = nx.Graph()

    # Add all nodes
    for node_id, attrs in NODES.items():
        G.add_node(node_id, **attrs)

    # Add edges
    for edge in EDGES:
        if exclude_closed and edge["status"] == "closed":
            continue  # hard block — never route through closed roads

        weight = edge["length_km"]
        if edge["status"] == "moderate":
            weight *= 2.0  # penalise degraded roads

        G.add_edge(
            edge["from_node"],
            edge["to_node"],
            road_id=edge["id"],
            name=edge["name"],
            length_km=edge["length_km"],
            status=edge["status"],
            weight=weight,
        )

    return G


# ---------------------------------------------------------------------------
# Route finder
# ---------------------------------------------------------------------------

def find_route(from_id: str, to_id: str) -> dict:
    """
    Find the shortest valid path between two node IDs using Dijkstra's
    algorithm, automatically skipping closed roads.

    Returns a dict with:
        valid         : bool
        message       : str (human-readable result or error)
        path          : list[str] — ordered node IDs (empty if no route)
        path_names    : list[str] — human-readable node names
        roads_used    : list[dict] — edge details for each road on the path
        total_distance_km : float
        has_moderate_roads: bool — warning flag for partially degraded route
    """
    # Validate node IDs
    if from_id not in NODES:
        return _no_route(f"Unknown origin node '{from_id}'")
    if to_id not in NODES:
        return _no_route(f"Unknown destination node '{to_id}'")
    if from_id == to_id:
        return _no_route("Origin and destination are the same node")

    G = build_graph(exclude_closed=True)

    # Check both nodes are actually in the graph (they might be isolated)
    if from_id not in G.nodes or to_id not in G.nodes:
        return _no_route("One or both nodes are completely isolated (all connecting roads closed)")

    try:
        path = nx.dijkstra_path(G, from_id, to_id, weight="weight")
        total_dist = nx.dijkstra_path_length(G, from_id, to_id, weight="weight")
    except nx.NetworkXNoPath:
        return _no_route(
            f"No valid route from '{NODES[from_id]['name']}' to "
            f"'{NODES[to_id]['name']}' — all paths are blocked by closed roads."
        )
    except nx.NodeNotFound as e:
        return _no_route(str(e))

    # Build per-road details for the path
    roads_used = []
    has_moderate = False
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G[u][v]
        if edge_data["status"] == "moderate":
            has_moderate = True
        roads_used.append({
            "road_id": edge_data["road_id"],
            "name": edge_data["name"],
            "from_node": u,
            "to_node": v,
            "length_km": edge_data["length_km"],
            "status": edge_data["status"],
        })

    return {
        "valid": True,
        "message": "Route found successfully"
        + (" (contains moderate-risk roads)" if has_moderate else ""),
        "path": path,
        "path_names": [NODES[n]["name"] for n in path],
        "roads_used": roads_used,
        "total_distance_km": round(total_dist, 2),
        "has_moderate_roads": has_moderate,
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _no_route(message: str) -> dict:
    return {
        "valid": False,
        "message": message,
        "path": [],
        "path_names": [],
        "roads_used": [],
        "total_distance_km": 0.0,
        "has_moderate_roads": False,
    }
