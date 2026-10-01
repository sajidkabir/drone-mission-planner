"""Run the bundled Dhaka survey mission and print its feasibility report.

Usage:
    python examples/dhaka_survey.py

Equivalent to: mission-planner check examples/dhaka_survey.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from drone_mission_planner.cli import load_plan
from drone_mission_planner.report import build_report


def main() -> None:
    mission, geofence, aircraft = load_plan(Path(__file__).with_name("dhaka_survey.json"))
    print(build_report(mission, geofence, aircraft))


if __name__ == "__main__":
    main()
