# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-06

### Added

- MAVLink mission exporter: `to_qgc_wpl` / `write_qgc_wpl` write the
  planner's mission as a QGroundControl waypoint file (`QGC WPL 110`),
  readable by QGroundControl and Mission Planner and flyable on ArduPilot
  and PX4. Home row, takeoff to the first waypoint's altitude, one
  waypoint row per planner waypoint (`loiter` becomes
  `MAV_CMD_NAV_LOITER_TIME` with the hold seconds), and a land row at the
  last waypoint. Altitudes export relative to the launch point
  (`MAV_FRAME_GLOBAL_RELATIVE_ALT`).
- `mission-planner export mission.json [-o out.waypoints]` CLI
  subcommand.
- `tests/test_export.py`: 16 checks covering the header, the row mapping,
  loiter seconds, the photo-waypoint limitation, empty-mission rejection,
  and the CLI.

### Notes

- `photo` waypoints export as plain waypoints: no camera trigger command
  is written, because trigger configuration is outside the planner model.

## [1.0.0] - 2026-10-01

First stable release.

### Added

- Mission data model (`Mission`, `Waypoint`, `Leg`) with per-leg distance,
  bearing, and cumulative distance, plus total distance and estimated
  duration at a cruise speed.
- JSON mission files with load/save round-tripping; optional "aircraft"
  and "geofence" sections read by the CLI and report builder.
- Great-circle geometry (`haversine_m`, `initial_bearing_deg`,
  `destination_point`) on a spherical Earth.
- Polygon geofence with ray-casting point-in-polygon checks (boundary
  counts as inside) and per-waypoint violation reporting.
- Energy feasibility assessment: momentum-theory hover power, a two-term
  induced-plus-parasite cruise power model, per-leg energy, loiter energy,
  and a feasible / marginal / infeasible verdict against the usable
  battery after a reserve margin, with the binding constraint named.
- Plain-text feasibility report combining the leg table, the geofence
  check, and the energy verdict.
- Command-line interface with `check` and `demo` subcommands.
- Test suite of 22 tests covering the geodesy against known city pairs,
  the geofence edge cases, and the verdict bands, plus GitHub Actions CI
  on Python 3.12.
- Example mission: a photo survey grid north-east of central Dhaka with a
  loiter point inside a rectangular geofence.
