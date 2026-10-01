"""Plain-text mission feasibility report.

Combines the three checks a planner actually needs before flying: the leg
table (where the aircraft goes), the geofence check (whether it is allowed
to go there), and the energy verdict (whether it can get back). The overall
verdict is INFEASIBLE if any waypoint sits outside the geofence, because a
mission that leaves its approved area is not flyable no matter how much
battery it has; otherwise the verdict is the energy verdict.
"""

from __future__ import annotations

from .energy import INFEASIBLE, AircraftSpec, EnergyAssessment, assess_mission
from .geofence import Geofence
from .mission import Mission


def _format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes} min {secs:02d} s"


def build_report(
    mission: Mission,
    geofence: Geofence | None = None,
    aircraft: AircraftSpec | None = None,
    reserve_fraction: float = 0.20,
) -> str:
    """Render the full feasibility report for a mission as plain text."""
    if aircraft is None:
        aircraft = AircraftSpec()
    assessment: EnergyAssessment = assess_mission(mission, aircraft, reserve_fraction)
    legs = mission.legs()

    lines: list[str] = []
    lines.append("Mission feasibility report")
    lines.append(f"  Mission:         {mission.name}")
    lines.append(f"  Waypoints:       {len(mission.waypoints)}")
    lines.append(f"  Cruise speed:    {mission.cruise_speed_mps:.1f} m/s")
    lines.append(
        f"  Aircraft:        {aircraft.mass_kg:.1f} kg, "
        f"battery {aircraft.battery_wh:.0f} Wh, reserve {reserve_fraction:.0%}"
    )
    lines.append("")
    lines.append("Legs:")
    if legs:
        for leg in legs:
            lines.append(
                f"  Leg {leg.index}: WP{leg.from_index + 1} -> WP{leg.to_index + 1}"
                f"  {leg.distance_m:9.1f} m  bearing {leg.bearing_deg:5.1f} deg"
                f"  cumulative {leg.cumulative_m:9.1f} m"
            )
    else:
        lines.append("  (no legs: a mission needs at least two waypoints)")
    lines.append(f"  Total distance:  {mission.total_distance_m():.1f} m")
    lines.append(
        f"  Est. duration:   {_format_duration(mission.estimated_duration_s())}"
        f" (includes {mission.total_dwell_s():.0f} s of loiter)"
    )
    lines.append("")
    lines.append("Geofence:")
    violations = []
    if geofence is None:
        lines.append("  No geofence supplied, containment not checked.")
    else:
        violations = geofence.violations(mission)
        if violations:
            lines.append(
                f"  FAIL: {len(violations)} waypoint(s) outside '{geofence.name}':"
            )
            for v in violations:
                lines.append(
                    f"    WP{v.waypoint_index + 1} at lat {v.lat:.5f}, lon {v.lon:.5f}"
                )
        else:
            lines.append(f"  OK: all waypoints inside '{geofence.name}'.")
    lines.append("")
    lines.append("Energy:")
    lines.append(
        f"  Cruise power:    {assessment.cruise_power_w:.1f} W"
        f"   Hover power: {assessment.hover_power_w:.1f} W"
    )
    lines.append(f"  Cruise energy:   {assessment.cruise_energy_wh:.1f} Wh")
    lines.append(f"  Loiter energy:   {assessment.loiter_energy_wh:.1f} Wh")
    lines.append(f"  Total energy:    {assessment.total_energy_wh:.1f} Wh")
    lines.append(
        f"  Usable battery:  {assessment.usable_energy_wh:.1f} Wh"
        f"   Margin: {assessment.margin_wh:+.1f} Wh"
    )
    lines.append("")
    if violations:
        verdict = INFEASIBLE
        binding = "geofence"
        lines.append(f"Verdict: {verdict.upper()} (binding constraint: {binding})")
    else:
        lines.append(
            f"Verdict: {assessment.verdict.upper()}"
            f" (binding constraint: {assessment.binding_constraint})"
        )
    return "\n".join(lines)
