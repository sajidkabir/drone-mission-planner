# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/).

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
