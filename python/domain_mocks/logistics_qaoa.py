"""
MatrixQ §4.2 logistics / VRP — mock QAOA narrative and real-world classical routing.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from twin_sentry.simulation_contract import build_simulation_payload

@dataclass
class LogisticsRequest:
    region_id: str = "metro-east"
    num_vehicles: int = 4
    num_stops: int = 12
    enforce_no_collision: bool = True
    shots: int = 8192
    qaoa_layers: int = 2
    coordinates: list[tuple[float, float]] = field(default_factory=list)


def _seed(region: str) -> float:
    return int.from_bytes(hashlib.sha256(region.encode()).digest()[:4], "big") / 0xFFFFFFFF


def run_logistics_qaoa_mock(req: LogisticsRequest) -> dict[str, Any]:
    """QAOA-style VRP mock with bitstring → route schedule telemetry."""
    t0 = time.perf_counter()
    rng = _seed(req.region_id)
    n_bits = min(16, max(4, req.num_stops))

    stages: list[dict[str, Any]] = []
    gamma, beta = 0.7 + rng * 0.2, 0.4 + rng * 0.1
    for layer in range(req.qaoa_layers):
        stages.append(
            {
                "layer": layer + 1,
                "gamma": round(gamma, 4),
                "beta": round(beta, 4),
                "optimizer": "COBYLA_stub",
                "duration_s": round(0.5 + rng * 0.2, 3),
            }
        )
        gamma *= 0.92
        beta *= 1.05

    route_bits = "".join("1" if (i + int(rng * 10)) % 3 else "0" for i in range(n_bits))
    alt = route_bits[: n_bits // 2] + "0" + route_bits[n_bits // 2 + 1 :]
    counts = {
        route_bits: int(req.shots * (0.85 + rng * 0.05)),
        alt: int(req.shots * 0.08),
    }
    rem = req.shots - sum(counts.values())
    if rem > 0:
        counts["0" * n_bits] = rem

    routes: list[dict[str, Any]] = []
    for v in range(req.num_vehicles):
        stops = [i for i in range(req.num_stops) if (i + v) % req.num_vehicles == 0]
        routes.append(
            {
                "vehicle_id": v,
                "stops": stops[: max(1, len(stops))],
                "distance_km": round(12.0 + v * 3.5 + rng * 5, 1),
            }
        )

    fuel_savings_usd_month = round(4_000_000 * (0.9 + rng * 0.1))

    business = {
        "domain": "logistics_qaoa",
        "region_id": req.region_id,
        "dominant_bitstring": route_bits,
        "routes": routes,
        "fuel_savings_usd_per_month": fuel_savings_usd_month,
        "no_collision_rules": req.enforce_no_collision,
        "kpi_narrative": "Mock: hours grid → sub-minute serverless (portfolio target)",
    }

    duration_ms = (time.perf_counter() - t0) * 1000.0 + 114.7
    simulation_payload = build_simulation_payload(
        success=True,
        cloud={"ok": True, "backend": "mock_qaoa_cloud", "counts": counts},
        shots=req.shots,
        gate_type="CNOT",
        business_telemetry=business,
        duration_ms=duration_ms,
    )
    simulation_payload["quantum_metadata"]["allocated_qubits"] = n_bits
    simulation_payload["quantum_metadata"]["optimized_gate_depth"] = 24 + req.qaoa_layers * 8

    return {
        "ok": True,
        "mock": True,
        "solver_id": "mock_qaoa",
        "solver_label": "Demo: Quantum narrative (mock)",
        "workflow": "[INPUT ROUTE & TRUCK MATRIX] → [HYBRID QAOA MESH] → [ACTIONABLE LOGISTICS MAP]",
        "request": {
            "region_id": req.region_id,
            "num_vehicles": req.num_vehicles,
            "num_stops": req.num_stops,
        },
        "stages": stages,
        "simulation_payload": simulation_payload,
        "summary": {
            "fuel_savings_usd_per_month": fuel_savings_usd_month,
            "vehicles_scheduled": req.num_vehicles,
            "wall_time_s": round(time.perf_counter() - t0, 3),
        },
    }


def _depot_and_stops(
    region_id: str, num_stops: int
) -> tuple[tuple[float, float], list[tuple[float, float]]]:
    seed = int.from_bytes(hashlib.sha256(region_id.encode()).digest()[:4], "big")
    rng = np.random.default_rng(seed)
    depot = (40.75, -73.98)
    stops = [
        (float(depot[0] + rng.uniform(-0.15, 0.15)), float(depot[1] + rng.uniform(-0.12, 0.12)))
        for _ in range(num_stops)
    ]
    return depot, stops


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _route_distance(depot: tuple[float, float], stops: list[int], coords: list[tuple[float, float]]) -> float:
    if not stops:
        return 0.0
    total = _dist(depot, coords[stops[0]])
    for i in range(len(stops) - 1):
        total += _dist(coords[stops[i]], coords[stops[i + 1]])
    total += _dist(coords[stops[-1]], depot)
    return total


def _greedy_vrp(
    depot: tuple[float, float],
    coords: list[tuple[float, float]],
    num_vehicles: int,
) -> list[list[int]]:
    n = len(coords)
    if n == 0:
        return [[] for _ in range(num_vehicles)]

    buckets: list[list[int]] = [[] for _ in range(num_vehicles)]
    for i, c in enumerate(coords):
        ang = math.atan2(c[1] - depot[1], c[0] - depot[0])
        bucket = int((ang + math.pi) / (2 * math.pi) * num_vehicles) % num_vehicles
        buckets[bucket].append(i)

    routes: list[list[int]] = []
    for bucket in buckets:
        remaining = set(bucket)
        route: list[int] = []
        cur: tuple[float, float] = depot
        while remaining:
            nxt = min(
                remaining,
                key=lambda s: _dist(cur, coords[s]) if route else _dist(depot, coords[s]),
            )
            route.append(nxt)
            remaining.remove(nxt)
            cur = coords[nxt]
        routes.append(route)
    while len(routes) < num_vehicles:
        routes.append([])
    return routes[:num_vehicles]


def _demands_kg_from_scenario(scenario: Any | None) -> list[int] | None:
    if scenario is None:
        return None
    stops = getattr(scenario, "stops", None)
    if not stops:
        return None
    return [int(s.get("kg", 0)) for s in stops]


def _solve_routes_real(
    depot: tuple[float, float],
    coords: list[tuple[float, float]],
    num_vehicles: int,
    *,
    scenario: Any | None = None,
) -> tuple[list[list[int]], str, dict[str, Any]]:
    """OR-Tools capacitated VRP when available; else greedy nearest-neighbor."""
    demands = _demands_kg_from_scenario(scenario)
    try:
        from routing.ortools_vrp import solve_vrp_ortools

        routes, meta = solve_vrp_ortools(
            depot,
            coords,
            num_vehicles,
            demands_kg=demands,
        )
        return routes, "ortools_vrp", meta
    except ImportError:
        pass
    except RuntimeError:
        pass

    optimized = _greedy_vrp(depot, coords, num_vehicles)
    return optimized, "greedy_nearest_neighbor", {"solver": "greedy_nearest_neighbor", "fallback": True}


def _naive_vrp(n: int, num_vehicles: int) -> list[list[int]]:
    routes: list[list[int]] = [[] for _ in range(num_vehicles)]
    for i in range(n):
        routes[i % num_vehicles].append(i)
    return routes


def run_logistics_qaoa_real(
    req: LogisticsRequest,
    *,
    scenario: Any | None = None,
) -> dict[str, Any]:
    """Real-world path: classical greedy VRP on lat/lon stops (no synthetic bitstrings)."""
    t0 = time.perf_counter()
    if req.coordinates:
        coords = list(req.coordinates)
        depot = scenario.depot if scenario is not None else (40.75, -73.98)
    else:
        depot, coords = _depot_and_stops(req.region_id, req.num_stops)

    naive = _naive_vrp(len(coords), req.num_vehicles)
    optimized, solver_id, solver_meta = _solve_routes_real(
        depot, coords, req.num_vehicles, scenario=scenario
    )

    naive_km = sum(_route_distance(depot, r, coords) for r in naive) * 111.0
    opt_km = sum(_route_distance(depot, r, coords) for r in optimized) * 111.0
    savings_pct = max(0.0, (naive_km - opt_km) / naive_km * 100.0) if naive_km > 0 else 0.0
    fuel_savings = round(4_000_000 * (savings_pct / 100.0) * 0.85)

    stop_labels = [s["name"] for s in scenario.stops] if scenario else None

    routes_out: list[dict[str, Any]] = []
    for v, stop_ids in enumerate(optimized):
        entry: dict[str, Any] = {
            "vehicle_id": v,
            "stops": stop_ids,
            "stop_coordinates": [coords[s] for s in stop_ids],
            "distance_km": round(_route_distance(depot, stop_ids, coords) * 111.0, 1),
        }
        if stop_labels:
            entry["stop_names"] = [stop_labels[s] for s in stop_ids if s < len(stop_labels)]
        routes_out.append(entry)

    # Encode route selection as bitstring for contract compatibility (1 = stop assigned to active leg)
    bits = ["0"] * len(coords)
    for r in optimized:
        for s in r:
            bits[s] = "1"
    route_bits = "".join(bits)

    counts = {route_bits: int(req.shots * 0.88), "0" * len(bits): req.shots - int(req.shots * 0.88)}

    business = {
        "domain": "logistics_qaoa",
        "execution": "real_world",
        "region_id": req.region_id,
        "depot": {
            "lat": depot[0],
            "lon": depot[1],
            "name": scenario.depot_name if scenario else "Distribution center",
        },
        "dominant_bitstring": route_bits,
        "routes": routes_out,
        "total_distance_km_optimized": round(opt_km, 1),
        "total_distance_km_naive": round(naive_km, 1),
        "distance_reduction_pct": round(savings_pct, 1),
        "fuel_savings_usd_per_month": fuel_savings,
        "no_collision_rules": req.enforce_no_collision,
        "use_case": "Metro fleet VRP — classical routing on customer manifest",
        "solver_id": solver_id,
        "solver_meta": solver_meta,
    }

    solver_label = (
        "Solver: Classical (OR-Tools)"
        if solver_id == "ortools_vrp"
        else "Solver: Classical (greedy VRP)"
    )

    duration_ms = (time.perf_counter() - t0) * 1000.0
    simulation_payload = build_simulation_payload(
        success=True,
        cloud={"ok": True, "backend": solver_id, "counts": counts},
        shots=req.shots,
        gate_type="CNOT",
        business_telemetry=business,
        duration_ms=duration_ms,
    )

    return {
        "ok": True,
        "mock": False,
        "execution": "real_world",
        "solver_id": solver_id,
        "solver_label": solver_label,
        "workflow": "[INPUT ROUTE & TRUCK MATRIX] → [CLASSICAL VRP SOLVE] → [ACTIONABLE LOGISTICS MAP]",
        "request": {
            "region_id": req.region_id,
            "num_vehicles": req.num_vehicles,
            "num_stops": len(coords),
            "solver": solver_id,
        },
        "stages": [
            {
                "stage": "baseline_round_robin",
                "distance_km": round(naive_km, 1),
            },
            {
                "stage": f"optimized_{solver_id}",
                "distance_km": round(opt_km, 1),
            },
        ],
        "simulation_payload": simulation_payload,
        "summary": {
            "fuel_savings_usd_per_month": fuel_savings,
            "distance_reduction_pct": round(savings_pct, 1),
            "vehicles_scheduled": req.num_vehicles,
            "wall_time_s": round(time.perf_counter() - t0, 3),
        },
    }


def _apply_logistics_mock_sales(out: dict[str, Any], mock: dict[str, Any]) -> dict[str, Any]:
    out = dict(out)
    summ = dict(out.get("summary") or {})
    summ.update(
        {
            "distance_reduction_pct": mock["distance_reduction_pct"],
            "fuel_savings_usd_per_month": mock["fuel_savings_usd_per_month"],
            "runtime_label": mock.get("runtime_label"),
            "total_distance_km_optimized": mock.get("total_distance_km_optimized"),
            "total_distance_km_naive": mock.get("total_distance_km_naive"),
        }
    )
    out["summary"] = summ
    sp = dict(out.get("simulation_payload") or {})
    bt = dict(sp.get("business_telemetry") or {})
    bt.update(
        {
            "total_distance_km_optimized": mock["total_distance_km_optimized"],
            "total_distance_km_naive": mock["total_distance_km_naive"],
            "distance_reduction_pct": mock["distance_reduction_pct"],
            "fuel_savings_usd_per_month": mock["fuel_savings_usd_per_month"],
        }
    )
    sp["business_telemetry"] = bt
    out["simulation_payload"] = sp
    return out


def run_logistics_qaoa(
    req: LogisticsRequest,
    *,
    real: bool = False,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    scenario = None
    if scenario_id:
        from domain_mocks.sales_demos import (
            attach_sales_narrative_logistics,
            get_logistics_scenario,
            logistics_coords_from_scenario,
        )

        scenario = get_logistics_scenario(scenario_id)
        depot, coords = logistics_coords_from_scenario(scenario)
        req = LogisticsRequest(
            region_id=scenario.request.region_id,
            num_vehicles=scenario.request.num_vehicles,
            num_stops=len(coords),
            enforce_no_collision=scenario.request.enforce_no_collision,
            shots=scenario.request.shots,
            qaoa_layers=scenario.request.qaoa_layers,
            coordinates=coords,
        )

    if real:
        out = run_logistics_qaoa_real(req, scenario=scenario)
    else:
        out = run_logistics_qaoa_mock(req)
        if scenario is not None:
            out = _apply_logistics_mock_sales(out, scenario.mock_outcome)

    if scenario is not None:
        from domain_mocks.sales_demos import attach_sales_narrative_logistics

        out = attach_sales_narrative_logistics(out, scenario)
    return out
