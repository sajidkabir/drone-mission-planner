"""Energy feasibility: verdicts for small, marginal, and oversized missions."""

from drone_mission_planner.energy import (
    FEASIBLE,
    INFEASIBLE,
    MARGINAL,
    AircraftSpec,
    assess_mission,
    cruise_power_w,
    hover_power_w,
)
from drone_mission_planner.mission import Mission, Waypoint

DHAKA = (23.8103, 90.4125)
CHATTOGRAM = (22.3569, 91.7832)


def small_mission() -> Mission:
    return Mission(
        name="Small",
        cruise_speed_mps=10.0,
        waypoints=[Waypoint(*DHAKA), Waypoint(23.83, 90.43), Waypoint(*DHAKA)],
    )


def test_hover_power_matches_momentum_theory():
    # Hand check for the default aircraft: thrust 29.42 N on 0.342 m2 of
    # disk gives v_i = 5.93 m/s, so P = 29.42 * 5.93 / 0.65 + 10 W of
    # avionics = about 278 W. Allow 2 percent.
    power = hover_power_w(AircraftSpec())
    assert abs(power - 278.0) / 278.0 < 0.02


def test_cruise_power_below_hover_at_moderate_speed():
    # A multirotor at a moderate cruise speed needs less power than in a
    # hover, because the induced term falls faster than drag grows.
    aircraft = AircraftSpec()
    assert cruise_power_w(aircraft, 10.0) < hover_power_w(aircraft)


def test_small_mission_is_feasible():
    result = assess_mission(small_mission(), AircraftSpec(battery_wh=400.0))
    assert result.verdict == FEASIBLE
    assert result.binding_constraint == "none"
    assert result.margin_wh > 0.0
    assert result.total_energy_wh < result.usable_energy_wh


def test_oversized_mission_is_infeasible():
    # Dhaka to Chattogram and back is about 428 km: no 100 Wh battery on a
    # 3 kg quad covers that. The verdict must say so and name the battery.
    mission = Mission(
        name="Intercity",
        cruise_speed_mps=12.0,
        waypoints=[Waypoint(*DHAKA), Waypoint(*CHATTOGRAM), Waypoint(*DHAKA)],
    )
    result = assess_mission(mission, AircraftSpec(battery_wh=100.0))
    assert result.verdict == INFEASIBLE
    assert result.binding_constraint == "battery energy"
    assert result.margin_wh < 0.0


def test_loiter_adds_energy():
    base = Mission(
        name="No loiter",
        cruise_speed_mps=10.0,
        waypoints=[Waypoint(*DHAKA), Waypoint(23.83, 90.43), Waypoint(*DHAKA)],
    )
    with_loiter = Mission(
        name="Loiter",
        cruise_speed_mps=10.0,
        waypoints=[
            Waypoint(*DHAKA),
            Waypoint(23.83, 90.43, action="loiter", loiter_s=600.0),
            Waypoint(*DHAKA),
        ],
    )
    aircraft = AircraftSpec(battery_wh=400.0)
    plain = assess_mission(base, aircraft)
    loitering = assess_mission(with_loiter, aircraft)
    assert loitering.cruise_energy_wh == plain.cruise_energy_wh
    assert loitering.loiter_energy_wh > 0.0
    assert loitering.total_energy_wh > plain.total_energy_wh
    # 600 s at hover power of about 278 W is about 46 Wh.
    assert abs(loitering.loiter_energy_wh - 46.0) < 3.0


def test_marginal_band_between_feasible_and_infeasible():
    # Size the battery so the mission lands in the last 10 percent of the
    # usable energy: verdict marginal, binding constraint the reserve.
    probe = assess_mission(small_mission(), AircraftSpec(battery_wh=10_000.0))
    total = probe.total_energy_wh
    battery_wh = total / (0.80 * 0.95)  # usable = 0.80 * battery = total / 0.95
    result = assess_mission(small_mission(), AircraftSpec(battery_wh=battery_wh))
    assert result.verdict == MARGINAL
    assert result.binding_constraint == "reserve margin"


def test_report_contains_verdict():
    from drone_mission_planner.report import build_report

    report = build_report(small_mission(), aircraft=AircraftSpec(battery_wh=400.0))
    assert "Verdict: FEASIBLE" in report
    assert "Total distance:" in report
    assert "No geofence supplied" in report
