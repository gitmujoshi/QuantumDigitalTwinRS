"""OR-Tools VRP on sales-demo manifests."""

from __future__ import annotations

import pytest

from domain_mocks.logistics_qaoa import run_logistics_qaoa
from domain_mocks.sales_demos import get_logistics_scenario


def test_pharma_real_mode_solver_label():
    s = get_logistics_scenario("northeast_pharma_cold_chain")
    out = run_logistics_qaoa(s.request, real=True, scenario_id=s.id)
    assert out["mock"] is False
    assert "solver_label" in out
    assert out["solver_id"] in ("ortools_vrp", "greedy_nearest_neighbor")
    if out["solver_id"] == "ortools_vrp":
        assert "OR-Tools" in out["solver_label"]
    routes = out["simulation_payload"]["business_telemetry"]["routes"]
    assert len(routes) >= 1
    covered = {stop for r in routes for stop in r["stops"]}
    assert len(covered) == len(s.stops)


@pytest.mark.skipif(
    "not __import__('routing.ortools_vrp', fromlist=['ORTOOLS_AVAILABLE']).ORTOOLS_AVAILABLE",
    reason="ortools not installed",
)
def test_ortools_direct_pharma():
    from routing.ortools_vrp import solve_vrp_ortools
    from domain_mocks.sales_demos import logistics_coords_from_scenario

    s = get_logistics_scenario("northeast_pharma_cold_chain")
    depot, coords = logistics_coords_from_scenario(s)
    demands = [int(st["kg"]) for st in s.stops]
    routes, meta = solve_vrp_ortools(depot, coords, s.request.num_vehicles, demands_kg=demands)
    assert meta["solver"] == "ortools_vrp"
    assert sum(len(r) for r in routes) == len(coords)


def test_route_map_figure_has_van_traces():
    import sys
    from pathlib import Path

    app_dir = Path(__file__).resolve().parent.parent / "app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    from sales_demo_views import build_logistics_route_map_figure

    s = get_logistics_scenario("northeast_pharma_cold_chain")
    out = run_logistics_qaoa(s.request, real=True, scenario_id=s.id)
    fig = build_logistics_route_map_figure(out, s)
    assert fig is not None
    names = {t.name for t in fig.data}
    assert "Depot" in names
    assert any(n.startswith("Van ") for n in names)
    assert len(fig.data) >= 2


def test_mock_mode_quantum_label():
    s = get_logistics_scenario("northeast_pharma_cold_chain")
    out = run_logistics_qaoa(s.request, real=False, scenario_id=s.id)
    assert out["mock"] is True
    assert out["solver_label"] == "Demo: Quantum narrative (mock)"
