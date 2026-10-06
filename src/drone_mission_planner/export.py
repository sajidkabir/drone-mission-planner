"""Mission exporters: write planner missions in formats real flight stacks read.

Currently supports the QGroundControl waypoint file format (``QGC WPL 110``),
which QGroundControl and Mission Planner both open, and which ArduPilot and
PX4 autopilots accept over MAVLink. The mapping from the planner model is
deliberate and documented below; anything the planner does not model is
stated, not faked.

Mapping
-------
* Row 0: home position (first waypoint latitude/longitude, altitude 0),
  ``MAV_CMD_NAV_WAYPOINT``.
* Row 1: ``MAV_CMD_NAV_TAKEOFF`` at the home position, climbing to the first
  waypoint's altitude. Altitudes are exported as height above the launch
  point (``MAV_FRAME_GLOBAL_RELATIVE_ALT``); the planner never records a
  launch elevation, so absolute (AMSL) altitudes are not available.
* One row per planner waypoint: ``MAV_CMD_NAV_WAYPOINT`` at its position and
  altitude, except a ``loiter`` waypoint, which becomes
  ``MAV_CMD_NAV_LOITER_TIME`` with param1 set to ``loiter_s``.
* Final row: ``MAV_CMD_NAV_LAND`` at the last waypoint's position, altitude
  0. The planner's last waypoint is normally the recovery point.

Not encoded (stated honestly)
-----------------------------
* ``photo`` waypoints are exported as plain waypoints. No camera trigger
  command is written: trigger distances and camera setup are outside the
  planner model, so emitting one would invent configuration the user never
  gave.
* The export performs no takeoff or landing safety checks (obstacle
  clearance, RTL altitude, geofence margins). Fly the exported file in SITL
  before putting it on hardware.
"""

from __future__ import annotations

from pathlib import Path

from .mission import Mission

# MAVLink enums referenced below (common.xml / MAV_CMD, MAV_FRAME).
FRAME_GLOBAL_RELATIVE_ALT = 3
CMD_NAV_WAYPOINT = 16
CMD_NAV_LOITER_TIME = 19
CMD_NAV_LAND = 21
CMD_NAV_TAKEOFF = 22

WPL_HEADER = "QGC WPL 110"


def _coord(value: float) -> str:
    """Format a coordinate or altitude the way ground stations write them."""
    return f"{value:.6f}"


def _param(value: float) -> str:
    """Format a MAVLink parameter without inventing false precision."""
    if value == int(value):
        return str(int(value))
    return repr(value)


def _row(
    seq: int,
    command: int,
    lat: float,
    lon: float,
    alt: float,
    *,
    param1: float = 0.0,
    current: int = 0,
) -> str:
    """One QGC WPL 110 data row (12 tab-separated columns)."""
    fields = [
        str(seq),
        str(current),
        str(FRAME_GLOBAL_RELATIVE_ALT),
        str(command),
        _param(param1),
        _param(0.0),
        _param(0.0),
        _param(0.0),
        _coord(lat),
        _coord(lon),
        _coord(alt),
        "1",  # autocontinue
    ]
    return "\t".join(fields)


def to_qgc_wpl(mission: Mission) -> str:
    """Render a mission as QGC WPL 110 text (trailing newline included).

    Raises ValueError if the mission has no waypoints.
    """
    if not mission.waypoints:
        raise ValueError("mission has no waypoints: nothing to export")
    first = mission.waypoints[0]
    last = mission.waypoints[-1]

    lines = [WPL_HEADER]
    seq = 0
    lines.append(
        _row(seq, CMD_NAV_WAYPOINT, first.lat, first.lon, 0.0, current=1)
    )
    seq += 1
    lines.append(
        _row(seq, CMD_NAV_TAKEOFF, first.lat, first.lon, first.altitude_m)
    )
    seq += 1
    for waypoint in mission.waypoints:
        if waypoint.action == "loiter":
            lines.append(
                _row(
                    seq,
                    CMD_NAV_LOITER_TIME,
                    waypoint.lat,
                    waypoint.lon,
                    waypoint.altitude_m,
                    param1=waypoint.loiter_s,
                )
            )
        else:
            lines.append(
                _row(
                    seq,
                    CMD_NAV_WAYPOINT,
                    waypoint.lat,
                    waypoint.lon,
                    waypoint.altitude_m,
                )
            )
        seq += 1
    lines.append(_row(seq, CMD_NAV_LAND, last.lat, last.lon, 0.0))
    return "\n".join(lines) + "\n"


def write_qgc_wpl(mission: Mission, path: str | Path) -> Path:
    """Write a mission as a QGC WPL 110 ``.waypoints`` file; return the path."""
    target = Path(path)
    target.write_text(to_qgc_wpl(mission), encoding="utf-8")
    return target
