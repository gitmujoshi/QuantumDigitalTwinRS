"""Sales-friendly render helpers for Materials & Logistics demos."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Distinct colors per van (colorblind-friendly palette)
_VAN_ROUTE_COLORS = (
    "#e6194b",
    "#3cb44b",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#bfef45",
    "#469990",
    "#9a6324",
)


def render_materials_test_data(
    scenario: Any,
    *,
    expanded: bool = True,
    key_prefix: str = "mat",
) -> None:
    from domain_mocks.sales_demos import build_materials_test_data

    uid = f"{key_prefix}_{scenario.id}"
    data = build_materials_test_data(scenario)
    with st.expander("📋 Sample test data (inputs to this run)", expanded=expanded, key=f"exp_td_mat_{uid}"):
        st.caption(data.get("notes", ""))
        st.markdown("**Atomic structure (stub geometry)**")
        geom = data.get("atomic_structure") or []
        if geom:
            st.dataframe(pd.DataFrame(geom), use_container_width=True, hide_index=True)
        st.markdown("**Simulation parameters**")
        st.dataframe(
            pd.DataFrame([data.get("simulation_parameters", {})]).T.rename(columns={0: "value"}),
            use_container_width=True,
        )
        st.markdown("**Baseline (before optimization)**")
        st.json(data.get("baseline_before_optimization", {}))
        if st.checkbox(
            "Show reference mock outputs",
            value=False,
            key=f"show_mock_mat_{uid}",
        ):
            st.json(data.get("reference_mock_outputs", {}))
        st.download_button(
            label="Download test data JSON",
            data=json.dumps(data, indent=2),
            file_name=f"test_data_{scenario.id}.json",
            mime="application/json",
            key=f"dl_mat_{uid}",
        )


def render_logistics_test_data(
    scenario: Any,
    *,
    expanded: bool = True,
    key_prefix: str = "log",
) -> None:
    from domain_mocks.sales_demos import build_logistics_test_data

    uid = f"{key_prefix}_{scenario.id}"
    data = build_logistics_test_data(scenario)
    with st.expander("📋 Sample test data (inputs to this run)", expanded=expanded, key=f"exp_td_log_{uid}"):
        st.caption(data.get("notes", ""))
        depot = data.get("depot") or {}
        st.markdown(f"**Depot:** {depot.get('name')} · lat `{depot.get('lat')}`, lon `{depot.get('lon')}`")
        st.markdown("**Fleet**")
        st.json(data.get("fleet", {}))
        st.markdown("**Delivery stops (full manifest)**")
        st.dataframe(pd.DataFrame(data.get("delivery_stops", [])), use_container_width=True, hide_index=True)
        st.markdown("**Planner baseline (legacy)**")
        st.json(data.get("planner_baseline", {}))
        if st.checkbox(
            "Show reference mock outputs",
            value=False,
            key=f"show_mock_log_{uid}",
        ):
            st.json(data.get("reference_mock_outputs", {}))
        st.download_button(
            label="Download test data JSON",
            data=json.dumps(data, indent=2),
            file_name=f"test_data_{scenario.id}.json",
            mime="application/json",
            key=f"dl_log_{uid}",
        )


def render_flagship_test_data_panel() -> None:
    """Show test data for Examples 1 & 2 side by side."""
    from domain_mocks.sales_demos import (
        build_logistics_test_data,
        build_materials_test_data,
        get_logistics_scenario,
        get_materials_scenario,
        flagship_examples_test_data,
    )

    with st.expander("📋 Sample test data — flagship Examples 1 & 2", expanded=True):
        tab1, tab2, tab_all = st.tabs(["Example 1 (Materials)", "Example 2 (Logistics)", "Download all"])
        with tab1:
            render_materials_test_data(
                get_materials_scenario("li2s_ev_fast_charge"),
                expanded=False,
                key_prefix="flagship_tab1",
            )
        with tab2:
            render_logistics_test_data(
                get_logistics_scenario("northeast_pharma_cold_chain"),
                expanded=False,
                key_prefix="flagship_tab2",
            )
        with tab_all:
            bundle = flagship_examples_test_data()
            st.json(bundle)
            st.download_button(
                label="Download both examples (JSON)",
                data=json.dumps(bundle, indent=2),
                file_name="flagship_examples_test_data.json",
                mime="application/json",
                key="dl_flagship_bundle",
            )


def render_materials_story(scenario: Any) -> None:
    st.markdown(f"**Customer:** {scenario.customer}")
    st.markdown(f"**Persona:** {scenario.persona}")
    st.markdown(f"**Product:** {scenario.product}")
    st.info(scenario.story)
    render_materials_test_data(scenario, expanded=False, key_prefix="story_mat")
    with st.expander("Talk track (no quantum jargon)", expanded=False, key=f"talk_mat_{scenario.id}"):
        for line in scenario.talking_points:
            st.markdown(f"- {line}")


def render_materials_result(out: dict[str, Any]) -> None:
    sales = out.get("sales_demo") or {}
    base = sales.get("baseline") or {}
    rec = sales.get("recommendation") or {}
    summ = out.get("summary") or {}

    st.markdown("#### Lab recommendation")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Max safe fast-charge (V)",
        f"{rec.get('max_safe_voltage_v', summ.get('max_safe_voltage_v', '—'))}",
        delta=f"{float(rec.get('max_safe_voltage_v', 0)) - float(base.get('charger_setting_v', 0)):.2f} vs old setting"
        if rec.get("max_safe_voltage_v") and base.get("charger_setting_v")
        else None,
        delta_color="inverse",
    )
    c2.metric("Bond length (Å)", f"{rec.get('optimal_bond_length_angstrom', '—')}")
    c3.metric("Runtime", summ.get("runtime_label") or f"{summ.get('wall_time_s', '—')} s")
    c4.metric("Sign-off", rec.get("lab_signoff", "—"))

    st.markdown("#### Before vs after (executive view)")
    st.table(
        pd.DataFrame(
            [
                {
                    "": "Before (classical)",
                    "Time to answer": base.get("classical_runtime"),
                    "Charger setting (V)": base.get("charger_setting_v"),
                    "Risk": base.get("field_failure_risk"),
                },
                {
                    "": "After (this run)",
                    "Time to answer": summ.get("vs_classical") or summ.get("runtime_label"),
                    "Charger setting (V)": rec.get("max_safe_voltage_v"),
                    "Risk": "Within safe bond envelope",
                },
            ]
        )
    )


def _resolve_depot(out: dict[str, Any], scenario: Any) -> tuple[float, float, str]:
    bt = (out.get("simulation_payload") or {}).get("business_telemetry") or {}
    depot_info = bt.get("depot") or {}
    if depot_info.get("lat") is not None and depot_info.get("lon") is not None:
        return (
            float(depot_info["lat"]),
            float(depot_info["lon"]),
            str(depot_info.get("name") or scenario.depot_name),
        )
    d = scenario.depot
    return float(d[0]), float(d[1]), str(scenario.depot_name)


def _route_path_latlon(
    route: dict[str, Any],
    scenario: Any,
    depot: tuple[float, float],
) -> tuple[list[float], list[float], list[str]]:
    """Build depot → stops in visit order → depot for one van."""
    stop_ids: list[int] = list(route.get("stops") or [])
    if not stop_ids:
        return [], [], []

    lats: list[float] = [depot[0]]
    lons: list[float] = [depot[1]]
    labels: list[str] = ["Depot (start)"]

    coord_list = route.get("stop_coordinates") or []
    for i, sid in enumerate(stop_ids):
        if i < len(coord_list) and coord_list[i]:
            lat, lon = float(coord_list[i][0]), float(coord_list[i][1])
            name = None
        elif 0 <= sid < len(scenario.stops):
            stop = scenario.stops[sid]
            lat, lon = float(stop["lat"]), float(stop["lon"])
            name = stop.get("name")
        else:
            continue
        if not name and route.get("stop_names") and i < len(route["stop_names"]):
            name = route["stop_names"][i]
        elif not name:
            name = f"Stop {sid + 1}"
        lats.append(lat)
        lons.append(lon)
        labels.append(f"{i + 1}. {name}")

    lats.append(depot[0])
    lons.append(depot[1])
    labels.append("Depot (return)")
    return lats, lons, labels


def build_logistics_route_map_figure(out: dict[str, Any], scenario: Any) -> go.Figure | None:
    """Plotly map: one colored polyline per van from computed routes."""
    bt = (out.get("simulation_payload") or {}).get("business_telemetry") or {}
    routes: list[dict[str, Any]] = list(bt.get("routes") or [])
    if not routes:
        return None

    depot_lat, depot_lon, depot_name = _resolve_depot(out, scenario)
    depot = (depot_lat, depot_lon)

    fig = go.Figure()
    fig.add_trace(
        go.Scattermap(
            lat=[depot_lat],
            lon=[depot_lon],
            mode="markers",
            name="Depot",
            marker=dict(size=16, color="#1a1a1a"),
            text=[depot_name],
            hovertemplate="<b>%{text}</b><extra></extra>",
            showlegend=True,
        )
    )

    all_lats: list[float] = [depot_lat]
    all_lons: list[float] = [depot_lon]
    has_path = False

    for route in routes:
        vid = int(route.get("vehicle_id", 0))
        lats, lons, labels = _route_path_latlon(route, scenario, depot)
        if len(lats) < 2:
            continue
        has_path = True
        color = _VAN_ROUTE_COLORS[vid % len(_VAN_ROUTE_COLORS)]
        van_name = f"Van {vid + 1}"
        all_lats.extend(lats)
        all_lons.extend(lons)

        fig.add_trace(
            go.Scattermap(
                lat=lats,
                lon=lons,
                mode="lines+markers",
                name=van_name,
                line=dict(width=4, color=color),
                marker=dict(size=9, color=color),
                text=labels,
                hovertemplate="<b>%{text}</b><extra></extra>",
            )
        )

    if not has_path:
        return None

    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    lat_span = max(all_lats) - min(all_lats)
    lon_span = max(all_lons) - min(all_lons)
    span = max(lat_span, lon_span, 0.02)
    zoom = 10 if span < 0.15 else 9 if span < 0.35 else 8 if span < 0.7 else 7

    fig.update_layout(
        title="Optimized routes by van",
        map=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        showlegend=True,
    )
    return fig


def render_logistics_route_map(out: dict[str, Any], scenario: Any) -> None:
    """Route map with per-van colored paths; falls back to stop pins if no routes."""
    fig = build_logistics_route_map_figure(out, scenario)
    if fig is not None:
        st.caption(
            "Colored lines = visit order per van (depot → deliveries → depot). "
            "Black marker = distribution center."
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    depot = scenario.depot
    map_rows = [
        {"lat": depot[0], "lon": depot[1], "label": f"DEPOT: {scenario.depot_name}"},
    ]
    for s in scenario.stops:
        map_rows.append({"lat": s["lat"], "lon": s["lon"], "label": s["name"]})
    st.caption("Run optimization to draw van routes (showing stops only).")
    st.map(pd.DataFrame(map_rows), latitude="lat", longitude="lon", size=80)


def render_logistics_story(scenario: Any) -> None:
    st.markdown(f"**Customer:** {scenario.customer}")
    st.markdown(f"**Persona:** {scenario.persona}")
    st.info(scenario.story)
    render_logistics_test_data(scenario, expanded=False, key_prefix="story_log")
    with st.expander("Talk track (no quantum jargon)", expanded=False, key=f"talk_log_{scenario.id}"):
        for line in scenario.talking_points:
            st.markdown(f"- {line}")


def render_logistics_result(out: dict[str, Any], scenario: Any) -> None:
    label = out.get("solver_label")
    if label:
        if out.get("mock"):
            st.info(f"**{label}** — storytelling demo; not a production routing engine.")
        else:
            st.success(f"**{label}** — measured on this customer manifest.")

    sales = out.get("sales_demo") or {}
    exec_sum = sales.get("executive_summary") or {}
    base = sales.get("baseline") or {}

    st.markdown("#### Executive metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Distance (km)",
        f"{exec_sum.get('after_distance_km', '—')}",
        delta=f"-{exec_sum.get('miles_saved_pct', 0)}%",
        delta_color="normal",
    )
    c2.metric("Monthly fuel saved", f"${exec_sum.get('monthly_fuel_saved_usd', 0):,}")
    c3.metric("Planner time", exec_sum.get("planner_after", "—"))
    c4.metric("On-time risk", base.get("on_time_risk"), delta=exec_sum.get("on_time_risk_after", "Improved"))

    b1, b2 = st.columns(2)
    with b1:
        st.metric("Before — total km", exec_sum.get("before_distance_km"))
        st.caption(f"Legacy planner: {base.get('planner_runtime')}")
    with b2:
        st.metric("After — total km", exec_sum.get("after_distance_km"))
        st.caption(f"This run: {exec_sum.get('planner_after')}")

    route_sheet = sales.get("route_sheet") or []
    if route_sheet:
        st.markdown("#### Van route sheet")
        st.dataframe(pd.DataFrame(route_sheet), use_container_width=True, hide_index=True)

    st.markdown("#### Route map")
    render_logistics_route_map(out, scenario)
