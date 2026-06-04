"""Sales scenario datasets."""

from domain_mocks.logistics_qaoa import run_logistics_qaoa
from domain_mocks.sales_demos import (
    get_logistics_scenario,
    get_materials_scenario,
    logistics_coords_from_scenario,
)
from domain_mocks.vqe_materials import run_vqe_materials


def test_materials_scenario_li2s() -> None:
    s = get_materials_scenario("li2s_ev_fast_charge")
    assert "Aurora Cell Works" in s.customer
    out = run_vqe_materials(s.request, real=False, scenario_id=s.id)
    assert out["sales_demo"]["scenario_id"] == s.id
    assert out["summary"]["max_safe_voltage_v"] == 4.12


def test_materials_test_data_export() -> None:
    from domain_mocks.sales_demos import build_materials_test_data, get_materials_scenario

    data = build_materials_test_data(get_materials_scenario("li2s_ev_fast_charge"))
    assert len(data["atomic_structure"]) == 3
    assert data["simulation_parameters"]["preset"] == "li2s"


def test_logistics_test_data_manifest() -> None:
    from domain_mocks.sales_demos import build_logistics_test_data, get_logistics_scenario

    data = build_logistics_test_data(get_logistics_scenario("northeast_pharma_cold_chain"))
    assert len(data["delivery_stops"]) == 14
    assert data["depot"]["name"].startswith("MedRoute")


def test_logistics_scenario_pharma_coords() -> None:
    s = get_logistics_scenario("northeast_pharma_cold_chain")
    depot, coords = logistics_coords_from_scenario(s)
    assert len(coords) == 14
    assert depot[0] == s.depot[0]
    out = run_logistics_qaoa(s.request, real=True, scenario_id=s.id)
    assert out["sales_demo"]["route_sheet"]
    assert len(out["sales_demo"]["stop_manifest"]) == 14
