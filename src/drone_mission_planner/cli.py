"""Command-line interface.

    mission-planner check mission.json   print the feasibility report
    mission-planner demo                 run the bundled Dhaka survey demo

A mission file is JSON: a "waypoints" list plus optional "aircraft" and
"geofence" sections (see the mission module docstring for the full format).
Without those sections, sensible defaults are used: a 3 kg quadcopter with
a 500 Wh battery, and no geofence check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .energy import AircraftSpec
from .geofence import Geofence
from .mission import Mission
from .report import build_report

# The demo mission mirrors examples/dhaka_survey.json: a photo survey grid
# north-east of central Dhaka with one loiter point, inside a rectangular
# geofence. Keep the two in sync.
DEMO_MISSION: dict = {
    "name": "Dhaka north survey",
    "cruise_speed_mps": 10.0,
    "aircraft": {"mass_kg": 3.0, "battery_wh": 400.0},
    "geofence": [
        [23.8000, 90.4000],
        [23.8000, 90.4750],
        [23.8600, 90.4750],
        [23.8600, 90.4000],
    ],
    "waypoints": [
        {"lat": 23.8103, "lon": 90.4125, "altitude_m": 50, "action": "none"},
        {"lat": 23.8300, "lon": 90.4300, "altitude_m": 60, "action": "photo"},
        {"lat": 23.8300, "lon": 90.4600, "altitude_m": 60, "action": "photo"},
        {"lat": 23.8500, "lon": 90.4600, "altitude_m": 70, "action": "loiter", "loiter_s": 45},
        {"lat": 23.8500, "lon": 90.4300, "altitude_m": 60, "action": "photo"},
        {"lat": 23.8103, "lon": 90.4125, "altitude_m": 50, "action": "none"},
    ],
}


def load_plan(path: str | Path) -> tuple[Mission, Geofence | None, AircraftSpec]:
    """Load a mission file into (mission, geofence or None, aircraft)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    mission = Mission.from_dict(data)
    geofence = Geofence.from_dict(data["geofence"]) if "geofence" in data else None
    aircraft = AircraftSpec.from_dict(data.get("aircraft", {}))
    return mission, geofence, aircraft


def plan_from_dict(data: dict) -> tuple[Mission, Geofence | None, AircraftSpec]:
    """Same as load_plan, for an already-parsed mission dictionary."""
    mission = Mission.from_dict(data)
    geofence = Geofence.from_dict(data["geofence"]) if "geofence" in data else None
    aircraft = AircraftSpec.from_dict(data.get("aircraft", {}))
    return mission, geofence, aircraft


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mission-planner",
        description="Multirotor mission planner: legs, geofence, and energy feasibility.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="check a mission JSON file")
    check.add_argument("path", help="path to the mission JSON file")
    check.add_argument(
        "--reserve",
        type=float,
        default=0.20,
        help="battery reserve fraction kept unused (default 0.20)",
    )

    demo = sub.add_parser("demo", help="run the bundled Dhaka survey demo mission")
    demo.add_argument(
        "--reserve",
        type=float,
        default=0.20,
        help="battery reserve fraction kept unused (default 0.20)",
    )

    args = parser.parse_args(argv)

    if args.command == "check":
        try:
            mission, geofence, aircraft = load_plan(args.path)
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"error: could not load mission file: {exc}", file=sys.stderr)
            return 2
        print(build_report(mission, geofence, aircraft, reserve_fraction=args.reserve))
        return 0

    if args.command == "demo":
        mission, geofence, aircraft = plan_from_dict(DEMO_MISSION)
        print(build_report(mission, geofence, aircraft, reserve_fraction=args.reserve))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
