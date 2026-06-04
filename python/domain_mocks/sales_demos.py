"""
Curated demo datasets for sales — no quantum jargon required.

Use ``list_materials_scenarios()`` / ``list_logistics_scenarios()`` in the UI;
each scenario includes customer story, baseline vs outcome framing, and reproducible inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain_mocks.logistics_qaoa import LogisticsRequest
from domain_mocks.vqe_materials import VqeMaterialsRequest


@dataclass(frozen=True)
class MaterialsScenario:
    id: str
    title: str
    customer: str
    persona: str
    product: str
    story: str
    talking_points: tuple[str, ...]
    baseline: dict[str, Any]
    request: VqeMaterialsRequest
    # Fixed mock outcomes (reproducible sales demo in Mock mode)
    mock_outcome: dict[str, Any]


@dataclass(frozen=True)
class LogisticsScenario:
    id: str
    title: str
    customer: str
    persona: str
    story: str
    talking_points: tuple[str, ...]
    baseline: dict[str, Any]
    request: LogisticsRequest
    depot_name: str
    depot: tuple[float, float]
    stops: tuple[dict[str, Any], ...]  # name, lat, lon, window, kg
    mock_outcome: dict[str, Any]


# --- Materials: Li₂S EV pouch (MatrixQ PRD Helena Vance storyline) ---

MATERIALS_SCENARIOS: dict[str, MaterialsScenario] = {
    "li2s_ev_fast_charge": MaterialsScenario(
        id="li2s_ev_fast_charge",
        title="Li₂S EV pouch — fast-charge safety limit",
        customer="Aurora Cell Works (pilot line)",
        persona="Dr. Helena Vance · Lead Materials Scientist",
        product="Gen-2 Li₂S solid-electrolyte pouch (48 Ah)",
        story=(
            "Aurora needs the highest **safe** DC fast-charge voltage before micro-cracking at the "
            "Li₂S interface. Classical supercell runs were queued for **3 weeks** on an HPC cluster. "
            "This demo shows the same decision in minutes: bond length + voltage cap for the lab."
        ),
        talking_points=(
            "Before: 3-week queue, no clear voltage cap for production chargers.",
            "After: Recommended **max fast-charge voltage** and **bond length** for the QC sheet.",
            "No qubit knowledge needed — read the green metrics and Lab Recommendation box.",
        ),
        baseline={
            "classical_runtime": "3 weeks (HPC queue)",
            "charger_setting_v": 4.55,
            "field_failure_risk": "High (micro-cracking observed at 4.5 V)",
            "bond_length_angstrom": None,
        },
        request=VqeMaterialsRequest(
            preset="li2s",
            mapping="jordan_wigner",
            ansatz="uccsd_stub",
            qubits=12,
            shots=8192,
            spsa_iterations=6,
        ),
        mock_outcome={
            "max_safe_voltage_v": 4.12,
            "bond_length_angstrom": 2.16,
            "ground_state_energy_hartree": -44.872,
            "runtime_label": "3.8 minutes",
            "vs_classical": "3 weeks → under 4 minutes",
        },
    ),
    "li2s_grid_storage": MaterialsScenario(
        id="li2s_grid_storage",
        title="Li₂S grid storage — degradation threshold",
        customer="GridScale Storage Co.",
        persona="Dr. Helena Vance · Lead Materials Scientist",
        product="Containerized Li₂S module (200 kWh)",
        story=(
            "GridScale is certifying **cycle-life** under daily 2C charge. They must prove the "
            "electrolyte bond geometry stays stable below a voltage ceiling before committing "
            "**$12M** in line upgrades."
        ),
        talking_points=(
            "Shows bond length drift and safe voltage for warranty filings.",
            "Compare baseline charger setting vs recommended cap.",
        ),
        baseline={
            "classical_runtime": "18 days (partner supercomputer)",
            "charger_setting_v": 4.35,
            "field_failure_risk": "Medium (capacity fade after 400 cycles)",
            "bond_length_angstrom": 2.22,
        },
        request=VqeMaterialsRequest(
            preset="li2s",
            mapping="bravyi_kitaev",
            ansatz="hardware_efficient",
            qubits=16,
            shots=8192,
            spsa_iterations=5,
        ),
        mock_outcome={
            "max_safe_voltage_v": 4.08,
            "bond_length_angstrom": 2.13,
            "ground_state_energy_hartree": -45.104,
            "runtime_label": "4.1 minutes",
            "vs_classical": "18 days → under 5 minutes",
        },
    ),
}


# --- Logistics: Northeast pharma + NYC grocery (Marcus Vance storyline) ---

_LOGISTICS_PHARMA_STOPS: tuple[dict[str, Any], ...] = (
    {"name": "Morristown Medical Center", "lat": 40.789, "lon": -74.477, "window": "06:00-08:00", "kg": 420},
    {"name": "Hackensack University MC", "lat": 40.881, "lon": -74.043, "window": "06:30-08:30", "kg": 380},
    {"name": "St. Barnabas Hospital", "lat": 40.767, "lon": -74.145, "window": "07:00-09:00", "kg": 290},
    {"name": "RWJ New Brunswick", "lat": 40.495, "lon": -74.451, "window": "07:00-09:30", "kg": 510},
    {"name": "Capital Health Trenton", "lat": 40.221, "lon": -74.756, "window": "08:00-10:00", "kg": 260},
    {"name": "CVS Regional Hub Edison", "lat": 40.518, "lon": -74.411, "window": "08:30-10:30", "kg": 180},
    {"name": "Walgreens DC Somerset", "lat": 40.498, "lon": -74.488, "window": "09:00-11:00", "kg": 220},
    {"name": "ShopRite Pharmacy Newark", "lat": 40.735, "lon": -74.172, "window": "09:00-11:30", "kg": 150},
    {"name": "Holy Name Medical Center", "lat": 40.947, "lon": -74.075, "window": "10:00-12:00", "kg": 340},
    {"name": "Englewood Health", "lat": 40.893, "lon": -73.972, "window": "10:00-12:00", "kg": 275},
    {"name": "Summit Medical Group", "lat": 40.715, "lon": -74.365, "window": "11:00-13:00", "kg": 190},
    {"name": "Overlook Medical Center", "lat": 40.708, "lon": -74.327, "window": "11:30-13:30", "kg": 410},
    {"name": "Clara Maass Medical", "lat": 40.782, "lon": -74.304, "window": "12:00-14:00", "kg": 230},
    {"name": "Trinitas Regional MC", "lat": 40.652, "lon": -74.228, "window": "12:30-14:30", "kg": 360},
)

_LOGISTICS_GROCERY_STOPS: tuple[dict[str, Any], ...] = (
    {"name": "Whole Foods Columbus Circle", "lat": 40.768, "lon": -73.982, "window": "05:00-07:00", "kg": 900},
    {"name": "Trader Joe's Union Square", "lat": 40.735, "lon": -73.991, "window": "05:30-07:30", "kg": 720},
    {"name": "Target Harlem", "lat": 40.804, "lon": -73.954, "window": "06:00-08:00", "kg": 1100},
    {"name": "Costco Brooklyn", "lat": 40.652, "lon": -73.982, "window": "06:00-08:30", "kg": 2400},
    {"name": "Fresh Direct Bronx Hub", "lat": 40.820, "lon": -73.926, "window": "06:30-08:30", "kg": 1800},
    {"name": "Amazon Fresh LIC", "lat": 40.743, "lon": -73.939, "window": "07:00-09:00", "kg": 1300},
    {"name": "Wegmans Brooklyn", "lat": 40.689, "lon": -73.985, "window": "07:00-09:00", "kg": 950},
    {"name": "Stop & Shop Flushing", "lat": 40.758, "lon": -73.830, "window": "07:30-09:30", "kg": 800},
    {"name": "Key Food Astoria", "lat": 40.764, "lon": -73.915, "window": "08:00-10:00", "kg": 540},
    {"name": "Food Bazaar Jersey City", "lat": 40.717, "lon": -74.044, "window": "08:00-10:00", "kg": 670},
    {"name": "ShopRite Hoboken", "lat": 40.744, "lon": -74.032, "window": "08:30-10:30", "kg": 620},
    {"name": "Morton Williams UWS", "lat": 40.787, "lon": -73.975, "window": "09:00-11:00", "kg": 480},
    {"name": "Gristedes Midtown", "lat": 40.755, "lon": -73.980, "window": "09:00-11:00", "kg": 390},
    {"name": "Fairway Kips Bay", "lat": 40.742, "lon": -73.978, "window": "09:30-11:30", "kg": 520},
    {"name": "Eataly Flatiron", "lat": 40.742, "lon": -73.990, "window": "10:00-12:00", "kg": 410},
    {"name": "Dean & Deluca SoHo", "lat": 40.723, "lon": -74.002, "window": "10:00-12:00", "kg": 280},
    {"name": "Zabar's UWS", "lat": 40.785, "lon": -73.976, "window": "10:30-12:30", "kg": 350},
    {"name": "H Mart Hells Kitchen", "lat": 40.761, "lon": -73.992, "window": "11:00-13:00", "kg": 590},
)

LOGISTICS_SCENARIOS: dict[str, LogisticsScenario] = {
    "northeast_pharma_cold_chain": LogisticsScenario(
        id="northeast_pharma_cold_chain",
        title="Northeast pharma — cold-chain morning wave",
        customer="MedRoute 3PL",
        persona="Marcus Vance · VP Global Supply Chain",
        story=(
            "MedRoute must hit **14 hospital and pharmacy** deliveries before noon from one "
            "Secaucus cold-chain DC. Their legacy planner takes **6+ hours** on a grid cluster; "
            "missed windows cost **$18k per violation**."
        ),
        talking_points=(
            "Each row is a real stop name and delivery window — not abstract qubits.",
            "Compare **Before (round-robin)** vs **After (optimized)** total km and fuel $.",
            "Map shows which van serves which stop.",
        ),
        baseline={
            "planner_runtime": "6.2 hours (on-prem grid)",
            "total_distance_km": 487,
            "monthly_fuel_usd": 4_200_000,
            "on_time_risk": "3 predicted window violations",
        },
        request=LogisticsRequest(
            region_id="northeast_pharma_cold_chain",
            num_vehicles=4,
            num_stops=14,
            enforce_no_collision=True,
            shots=8192,
            qaoa_layers=3,
        ),
        depot_name="MedRoute Secaucus Cold-Chain DC",
        depot=(40.789, -74.056),
        stops=_LOGISTICS_PHARMA_STOPS,
        mock_outcome={
            "total_distance_km_optimized": 412,
            "total_distance_km_naive": 487,
            "distance_reduction_pct": 15.4,
            "fuel_savings_usd_per_month": 4_050_000,
            "runtime_label": "47 seconds",
            "on_time_risk_after": "0 predicted violations",
        },
    ),
    "nyc_last_mile_grocery": LogisticsScenario(
        id="nyc_last_mile_grocery",
        title="NYC last-mile grocery — peak breakfast stock",
        customer="UrbanBasket Same-Day",
        persona="Marcus Vance · VP Global Supply Chain",
        story=(
            "**18 store drops · 6 refrigerated vans.** "
            "UrbanBasket replenishes **18 Manhattan/Brooklyn/Queens stores** between 5–13:00 from "
            "a Brooklyn cross-dock. Combinatorial routing explodes classical overnight runs; this "
            "demo returns assignable van routes in under a minute."
        ),
        talking_points=(
            "High-weight Costco/Costco-style stops mixed with small bodegas — realistic load mix.",
            "Executive metric: **$ saved per month** and **% fewer miles**.",
        ),
        baseline={
            "planner_runtime": "9.5 hours (legacy VRP grid)",
            "total_distance_km": 312,
            "monthly_fuel_usd": 2_800_000,
            "on_time_risk": "5 late windows",
        },
        request=LogisticsRequest(
            region_id="nyc_last_mile_grocery",
            num_vehicles=6,
            num_stops=18,
            enforce_no_collision=True,
            shots=8192,
            qaoa_layers=2,
        ),
        depot_name="UrbanBasket Brooklyn Cross-Dock",
        depot=(40.650, -73.979),
        stops=_LOGISTICS_GROCERY_STOPS,
        mock_outcome={
            "total_distance_km_optimized": 268,
            "total_distance_km_naive": 312,
            "distance_reduction_pct": 14.1,
            "fuel_savings_usd_per_month": 2_650_000,
            "runtime_label": "52 seconds",
            "on_time_risk_after": "0 late windows",
        },
    ),
}


def list_materials_scenarios() -> list[MaterialsScenario]:
    return list(MATERIALS_SCENARIOS.values())


def list_logistics_scenarios() -> list[LogisticsScenario]:
    return list(LOGISTICS_SCENARIOS.values())


def get_materials_scenario(scenario_id: str) -> MaterialsScenario:
    if scenario_id not in MATERIALS_SCENARIOS:
        raise KeyError(f"Unknown materials scenario: {scenario_id}")
    return MATERIALS_SCENARIOS[scenario_id]


def get_logistics_scenario(scenario_id: str) -> LogisticsScenario:
    if scenario_id not in LOGISTICS_SCENARIOS:
        raise KeyError(f"Unknown logistics scenario: {scenario_id}")
    return LOGISTICS_SCENARIOS[scenario_id]


def attach_sales_narrative_materials(out: dict[str, Any], scenario: MaterialsScenario) -> dict[str, Any]:
    out = dict(out)
    out["sales_demo"] = {
        "scenario_id": scenario.id,
        "title": scenario.title,
        "customer": scenario.customer,
        "persona": scenario.persona,
        "product": scenario.product,
        "story": scenario.story,
        "talking_points": list(scenario.talking_points),
        "baseline": scenario.baseline,
        "recommendation": _materials_recommendation(out, scenario),
    }
    return out


def _materials_recommendation(out: dict[str, Any], scenario: MaterialsScenario) -> dict[str, Any]:
    summ = out.get("summary") or {}
    bt = (out.get("simulation_payload") or {}).get("business_telemetry") or {}
    v = summ.get("max_safe_voltage_v") or bt.get("max_safe_voltage_v")
    bond = summ.get("bond_length_angstrom") or bt.get("optimal_bond_length_angstrom")
    return {
        "action": "Set production fast-charge ceiling",
        "max_safe_voltage_v": v,
        "optimal_bond_length_angstrom": bond,
        "do_not_exceed_previous_charger_v": scenario.baseline.get("charger_setting_v"),
        "lab_signoff": "Approved for pilot line QC sheet" if v and v < scenario.baseline.get("charger_setting_v", 99) else "Review",
    }


def attach_sales_narrative_logistics(out: dict[str, Any], scenario: LogisticsScenario) -> dict[str, Any]:
    out = dict(out)
    stops_table = []
    bt = (out.get("simulation_payload") or {}).get("business_telemetry") or {}
    routes = bt.get("routes") or []
    for r in routes:
        vid = r.get("vehicle_id", 0)
        for seq, sid in enumerate(r.get("stops", []), start=1):
            if sid < len(scenario.stops):
                meta = scenario.stops[sid]
                stops_table.append(
                    {
                        "van": f"Van {vid + 1}",
                        "stop_order": seq,
                        "location": meta["name"],
                        "delivery_window": meta["window"],
                        "load_kg": meta["kg"],
                    }
                )
    out["sales_demo"] = {
        "scenario_id": scenario.id,
        "title": scenario.title,
        "customer": scenario.customer,
        "persona": scenario.persona,
        "story": scenario.story,
        "talking_points": list(scenario.talking_points),
        "baseline": scenario.baseline,
        "depot_name": scenario.depot_name,
        "stop_manifest": [dict(s) for s in scenario.stops],
        "route_sheet": stops_table,
        "executive_summary": _logistics_executive_summary(out, scenario),
    }
    return out


def _logistics_executive_summary(out: dict[str, Any], scenario: LogisticsScenario) -> dict[str, Any]:
    summ = out.get("summary") or {}
    bt = (out.get("simulation_payload") or {}).get("business_telemetry") or {}
    return {
        "before_distance_km": bt.get("total_distance_km_naive") or scenario.baseline.get("total_distance_km"),
        "after_distance_km": bt.get("total_distance_km_optimized") or summ.get("total_distance_km"),
        "miles_saved_pct": summ.get("distance_reduction_pct") or bt.get("distance_reduction_pct"),
        "monthly_fuel_saved_usd": summ.get("fuel_savings_usd_per_month") or bt.get("fuel_savings_usd_per_month"),
        "planner_before": scenario.baseline.get("planner_runtime"),
        "planner_after": summ.get("runtime_label") or out.get("summary", {}).get("wall_time_s"),
    }


def logistics_coords_from_scenario(scenario: LogisticsScenario) -> tuple[tuple[float, float], list[tuple[float, float]]]:
    coords = [(float(s["lat"]), float(s["lon"])) for s in scenario.stops]
    return scenario.depot, coords


# Explicit geometry / structure stubs shown in UI (toy coordinates for demo, not DFT-exported)
MATERIALS_GEOMETRY_STUBS: dict[str, list[dict[str, Any]]] = {
    "li2s_ev_fast_charge": [
        {"site": "Li (1)", "element": "Li", "x_angstrom": 0.0, "y_angstrom": 0.0, "z_angstrom": 0.0},
        {"site": "Li (2)", "element": "Li", "x_angstrom": 2.18, "y_angstrom": 0.0, "z_angstrom": 0.0},
        {"site": "S", "element": "S", "x_angstrom": 1.09, "y_angstrom": 1.88, "z_angstrom": 0.0},
    ],
    "li2s_grid_storage": [
        {"site": "Li (1)", "element": "Li", "x_angstrom": 0.0, "y_angstrom": 0.0, "z_angstrom": 0.0},
        {"site": "Li (2)", "element": "Li", "x_angstrom": 2.22, "y_angstrom": 0.0, "z_angstrom": 0.0},
        {"site": "S", "element": "S", "x_angstrom": 1.11, "y_angstrom": 1.92, "z_angstrom": 0.0},
    ],
}


def build_materials_test_data(scenario: MaterialsScenario) -> dict[str, Any]:
    """Structured input dataset for UI / JSON export (Example 1 & 2 materials)."""
    r = scenario.request
    return {
        "scenario_id": scenario.id,
        "title": scenario.title,
        "customer": scenario.customer,
        "product": scenario.product,
        "atomic_structure": MATERIALS_GEOMETRY_STUBS.get(scenario.id, []),
        "simulation_parameters": {
            "preset": r.preset,
            "fermion_mapping": r.mapping,
            "ansatz_template": r.ansatz,
            "active_qubits": r.qubits,
            "shots_per_iteration": r.shots,
            "spsa_iterations": r.spsa_iterations,
            "optimizer": "SPSA",
        },
        "baseline_before_optimization": dict(scenario.baseline),
        "reference_mock_outputs": dict(scenario.mock_outcome),
        "notes": (
            "Geometry is a simplified Li₂S unit-cell stub for the demo. "
            "Production would load XYZ/CIF from the customer LMS."
        ),
    }


def build_logistics_test_data(scenario: LogisticsScenario) -> dict[str, Any]:
    """Structured input dataset for UI / JSON export (Example 2 logistics)."""
    r = scenario.request
    total_kg = sum(int(s["kg"]) for s in scenario.stops)
    return {
        "scenario_id": scenario.id,
        "title": scenario.title,
        "customer": scenario.customer,
        "depot": {
            "name": scenario.depot_name,
            "lat": scenario.depot[0],
            "lon": scenario.depot[1],
        },
        "fleet": {
            "num_vehicles": r.num_vehicles,
            "enforce_no_collision": r.enforce_no_collision,
            "total_payload_kg": total_kg,
        },
        "delivery_stops": [dict(s) for s in scenario.stops],
        "planner_baseline": dict(scenario.baseline),
        "reference_mock_outputs": dict(scenario.mock_outcome),
        "notes": (
            "Stops are real facility names with lat/lon in the NY/NJ metro. "
            "Windows and kg loads are representative cold-chain test inputs."
        ),
    }


def flagship_examples_test_data() -> dict[str, Any]:
    """Both flagship examples in one JSON bundle."""
    return {
        "example_1_materials": build_materials_test_data(get_materials_scenario("li2s_ev_fast_charge")),
        "example_2_logistics": build_logistics_test_data(get_logistics_scenario("northeast_pharma_cold_chain")),
    }
