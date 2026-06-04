"""Domain mocks and QPU vendor mock."""

from __future__ import annotations

import pytest

from domain_mocks.drug_discovery import DrugPipelineRequest, run_drug_pipeline_mock
from domain_mocks.logistics_qaoa import LogisticsRequest, run_logistics_qaoa, run_logistics_qaoa_mock
from domain_mocks.vqe_materials import VqeMaterialsRequest, run_vqe_materials, run_vqe_materials_mock
from domain_mocks.weather import WeatherRunRequest, run_regional_forecast_mock

pytest.importorskip("twin_sentry._native")

from twin_sentry import PulseCommand
from twin_sentry.qpu_vendor_mock import get_calibration_mock, submit_pulse_vendor_mock


def test_weather_mock_ok() -> None:
    out = run_regional_forecast_mock(
        WeatherRunRequest(region="eu-west", horizon_hours=12, backend="hybrid_qsvt")
    )
    assert out["ok"] is True
    assert out["mock"] is True
    assert out["subroutine"] == "qsvt_linear_solve_stub"


def test_vqe_materials_mock_payload() -> None:
    out = run_vqe_materials_mock(VqeMaterialsRequest(preset="li2s"))
    assert out["ok"] is True
    sp = out["simulation_payload"]
    assert sp["success"] is True
    assert sp["business_telemetry"]["max_safe_voltage_v"] > 0
    assert sum(sp["counts"].values()) == 8192


def test_logistics_qaoa_mock_routes() -> None:
    out = run_logistics_qaoa_mock(LogisticsRequest(region_id="test-metro"))
    assert out["ok"] is True
    routes = out["simulation_payload"]["business_telemetry"]["routes"]
    assert len(routes) >= 1


def test_vqe_materials_real() -> None:
    out = run_vqe_materials(VqeMaterialsRequest(preset="li2s"), real=True)
    assert out["ok"] is True
    assert out["mock"] is False
    assert out["summary"]["max_safe_voltage_v"] > 0


def test_logistics_qaoa_real() -> None:
    out = run_logistics_qaoa(LogisticsRequest(region_id="nyc-demo", num_stops=10), real=True)
    assert out["ok"] is True
    assert out["mock"] is False
    assert out["summary"]["distance_reduction_pct"] >= 0


def test_drug_mock_stages() -> None:
    out = run_drug_pipeline_mock(
        DrugPipelineRequest(molecule_id="aspirin-demo", backend="hybrid_vqe")
    )
    assert out["ok"] is True
    assert len(out["stages"]) >= 2


def test_qpu_vendor_mock_submit() -> None:
    cmd = PulseCommand(
        amplitude=0.5,
        frequency_hz=5e9,
        duration_s=80e-9,
        qubit0_split_hz=5e9,
        qubit1_split_hz=4.5e9,
        rabi_ref_hz=10e6,
    )
    out = submit_pulse_vendor_mock(cmd, "HADAMARD", vendor="mock_ibm", shots=512)
    assert out["ok"] is True
    assert out["job_id"].startswith("mock_ibm-")
    assert sum(out["counts"].values()) == 512


def test_qpu_policy_reject() -> None:
    cmd = PulseCommand()
    out = submit_pulse_vendor_mock(cmd, None, vendor="mock_ionq", shots=100, policy_approved=False)
    assert out["ok"] is False
    assert out["stage"] == "policy_gate"


def test_calibration_mock() -> None:
    cal = get_calibration_mock("mock_rigetti")
    assert cal.operational
    assert cal.t2_us > 0
