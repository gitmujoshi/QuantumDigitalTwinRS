"""
Google OR-Tools VRP on lat/lon manifests (classical — not quantum).

Used by domain_mocks.logistics_qaoa in Real-world mode.
"""

from __future__ import annotations

import math
from typing import Any

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    pywrapcp = None  # type: ignore[assignment,misc]
    routing_enums_pb2 = None  # type: ignore[assignment,misc]

KM_PER_DEGREE = 111.0


def _dist_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1]) * KM_PER_DEGREE


def _build_distance_matrix(
    depot: tuple[float, float],
    coords: list[tuple[float, float]],
) -> list[list[int]]:
    """Integer meters for OR-Tools (avoids float issues)."""
    points = [depot] + list(coords)
    n = len(points)
    matrix: list[list[int]] = []
    for i in range(n):
        row: list[int] = []
        for j in range(n):
            if i == j:
                row.append(0)
            else:
                row.append(int(_dist_km(points[i], points[j]) * 1000))
        matrix.append(row)
    return matrix


def solve_vrp_ortools(
    depot: tuple[float, float],
    coords: list[tuple[float, float]],
    num_vehicles: int,
    *,
    demands_kg: list[int] | None = None,
    vehicle_capacity_kg: int | None = None,
    time_limit_s: int = 10,
) -> tuple[list[list[int]], dict[str, Any]]:
    """
    Solve capacitated VRP. Returns (routes per vehicle as stop indices, metadata).

    Node 0 in the matrix is depot; stop indices in routes are 0..len(coords)-1.
    """
    if not ORTOOLS_AVAILABLE:
        raise ImportError(
            "OR-Tools not installed. Install with: pip install 'twinsentry-rs[logistics]'"
        )

    n = len(coords)
    if n == 0:
        return [[] for _ in range(num_vehicles)], {"solver": "ortools_vrp", "status": "empty"}

    num_vehicles = max(1, min(num_vehicles, n))
    matrix = _build_distance_matrix(depot, coords)

    manager = pywrapcp.RoutingIndexManager(len(matrix), num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        f = manager.IndexToNode(from_index)
        t = manager.IndexToNode(to_index)
        return matrix[f][t]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    meta: dict[str, Any] = {"solver": "ortools_vrp", "capacity_enabled": False}

    if demands_kg and len(demands_kg) == n:
        if vehicle_capacity_kg is None:
            total = sum(demands_kg)
            vehicle_capacity_kg = max(max(demands_kg), int(math.ceil(total / num_vehicles * 1.15)))
        demands = [0] + [int(d) for d in demands_kg]

        def demand_callback(from_index: int) -> int:
            return demands[manager.IndexToNode(from_index)]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            [int(vehicle_capacity_kg)] * num_vehicles,
            True,
            "Capacity",
        )
        meta["capacity_enabled"] = True
        meta["vehicle_capacity_kg"] = vehicle_capacity_kg

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(time_limit_s)

    solution = routing.SolveWithParameters(search_parameters)
    if solution is None:
        raise RuntimeError("OR-Tools VRP found no solution")

    routes: list[list[int]] = []
    for vehicle_id in range(num_vehicles):
        route: list[int] = []
        index = routing.Start(vehicle_id)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                route.append(node - 1)
            index = solution.Value(routing.NextVar(index))
        routes.append(route)

    meta["status"] = "optimal_or_feasible"
    meta["objective_m"] = int(solution.ObjectiveValue())
    return routes, meta
