# drone-mission-planner

[![CI](https://github.com/sajidkabir/drone-mission-planner/actions/workflows/ci.yml/badge.svg)](https://github.com/sajidkabir/drone-mission-planner/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23077815.svg)](https://doi.org/10.5281/zenodo.23077815)

A multirotor mission planner and feasibility checker. Give it a mission as
a list of waypoints and it answers the three questions that matter before
anyone charges a battery: where exactly does the aircraft go (leg distances
and bearings on a spherical Earth), is it allowed to go there (a polygon
geofence check on every waypoint), and can it get back (an energy estimate
against the battery, with a reserve margin and a clear verdict).

**Feasible, marginal, or infeasible, with the binding constraint named.**
No silent optimism, no third-party dependencies: the whole package is the
Python standard library.

## Features

- **Mission model**: waypoints with altitude and actions (pass through,
  photo, loiter with a hold time), legs computed between consecutive
  points, total distance, and estimated duration at a cruise speed.
- **JSON mission files**: load and save round-trip exactly, with optional
  aircraft and geofence sections so one file fully describes a check.
- **Great-circle geometry**: haversine distance, initial bearing, and
  destination point, validated against known city pairs.
- **Polygon geofence**: ray-casting point-in-polygon test (boundary counts
  as inside, vertices included) and per-waypoint violation reporting.
- **Energy feasibility**: momentum-theory hover power and a two-term
  induced-plus-parasite cruise power model, per-leg energy, loiter energy
  at hover power, and a verdict against the usable battery after reserve.
- **Plain-text report**: the leg table, the geofence result, and the
  energy verdict in one page a human can read in the field.
- **CLI**: `mission-planner check mission.json` prints the report;
  `mission-planner demo` runs the bundled Dhaka survey mission.

## Installation

Requires Python 3.10 or newer. No third-party runtime dependencies.

```bash
git clone https://github.com/sajidkabir/drone-mission-planner.git
cd drone-mission-planner
pip install -e .
```

For development (adds the test runner):

```bash
pip install -e . pytest
pytest -q
```

## Quickstart

### Command line

Run the bundled demo mission, a photo survey grid north-east of central
Dhaka with one loiter point:

```bash
mission-planner demo
```

```text
Mission feasibility report
  Mission:         Dhaka north survey
  Waypoints:       6
  Cruise speed:    10.0 m/s
  Aircraft:        3.0 kg, battery 400 Wh, reserve 20%

Legs:
  Leg 1: WP1 -> WP2     2822.7 m  bearing  39.1 deg  cumulative    2822.7 m
  Leg 2: WP2 -> WP3     3051.5 m  bearing  90.0 deg  cumulative    5874.1 m
  Leg 3: WP3 -> WP4     2223.9 m  bearing   0.0 deg  cumulative    8098.0 m
  Leg 4: WP4 -> WP5     3051.0 m  bearing 270.0 deg  cumulative   11149.0 m
  Leg 5: WP5 -> WP6     4759.8 m  bearing 202.0 deg  cumulative   15908.8 m
  Total distance:  15908.8 m
  Est. duration:   27 min 16 s (includes 45 s of loiter)

Geofence:
  OK: all waypoints inside 'geofence'.

Energy:
  Cruise power:    131.6 W   Hover power: 278.1 W
  Cruise energy:   58.2 Wh
  Loiter energy:   3.5 Wh
  Total energy:    61.6 Wh
  Usable battery:  320.0 Wh   Margin: +258.4 Wh

Verdict: FEASIBLE (binding constraint: none)
```

Check your own mission file (the same mission ships as
`examples/dhaka_survey.json`):

```bash
mission-planner check examples/dhaka_survey.json
mission-planner check my_mission.json --reserve 0.30
```

### Python API

```python
from drone_mission_planner import AircraftSpec, Mission, Waypoint, build_report

mission = Mission(
    name="Harbour loop",
    cruise_speed_mps=10.0,
    waypoints=[
        Waypoint(23.8103, 90.4125),
        Waypoint(23.8300, 90.4300, action="photo"),
        Waypoint(23.8103, 90.4125),
    ],
)

print(mission.total_distance_m())      # 5645.3 m there and back
print(mission.estimated_duration_s())  # 564.5 s at cruise speed
print(build_report(mission, aircraft=AircraftSpec(battery_wh=400.0)))
```

Missions save and load as JSON: `mission.save_json("m.json")` and
`Mission.load_json("m.json")` restore every waypoint exactly.

## How it works

| Module | Responsibility |
| --- | --- |
| `geo.py` | Great-circle distance, bearing, and destination point |
| `mission.py` | Waypoint and mission model, legs, totals, JSON files |
| `geofence.py` | Polygon containment and violation reporting |
| `energy.py` | Power models, per-leg energy, feasibility verdict |
| `report.py` | The plain-text report combining all three checks |
| `cli.py` | Command-line interface (`check`, `demo`) |

Key relations:

- Haversine: a = sin^2(dphi/2) + cos(phi1) * cos(phi2) * sin^2(dlambda/2),
  distance = 2 * R * asin(sqrt(a)), with R = 6,371 km
- Hover induced velocity: v_i = sqrt(T / (2 * rho * A)), hover power
  P = T * v_i / figure_of_merit, with T = m * g
- Cruise power: P(v) = (m * g)^2 / (2 * rho * A * v) + 0.5 * rho * CdA * v^3
  + avionics, an induced term that falls with speed plus a parasite term
  that grows with its cube
- Usable energy = battery capacity * (1 - reserve fraction). Verdict:
  feasible with at least 10 percent of usable energy to spare, marginal
  inside that last 10 percent, infeasible beyond the usable energy

## Validation and sanity checks

The test suite (22 tests) checks the numbers against references, not just
the plumbing:

- Dhaka to Chattogram by haversine is 214.0 km, matching the known
  straight-line distance, and the initial bearing is about 139 degrees,
  squarely south-east.
- A destination-point round trip closes to under a metre.
- Hover power matches a hand-computed momentum-theory value within
  2 percent.
- Point-in-polygon: inside, outside, on a vertex, and on an edge all
  behave as documented; a mission with one waypoint outside the fence
  flags exactly that waypoint.
- A small survey is feasible, a Dhaka to Chattogram return on a 100 Wh
  battery is infeasible with the battery named as the binding constraint,
  and a battery sized into the last 10 percent of usable energy lands in
  the marginal band.
- JSON round-tripping preserves every waypoint field, and total distance
  equals the sum of the legs.

## Honest limitations

- Spherical Earth throughout. Fine at mission scale; not a survey-grade
  geodesy package.
- The geofence test treats longitude and latitude as planar coordinates.
  Distortion is negligible for fences a few kilometres across and grows
  for large or polar polygons. Fences crossing the antimeridian are not
  supported.
- No wind model yet: a headwind leg and a tailwind leg cost the same here.
- No climb, descent, acceleration, or turn energy. Totals are lower bounds.
- The cruise induced term is the high-speed approximation, clamped at
  1 m/s; power at very low speeds is approximate.
- One cruise speed for the whole mission; no per-leg speeds.
- The geofence is two-dimensional: altitude is recorded on waypoints but
  not checked.
- The battery is an ideal energy bucket: no discharge curve, C-rate, or
  temperature effects.

These are deliberate. Each one is a clean extension point, listed below.

## Roadmap and room for exploration

Ideas are welcome. Roughly in order of expected value:

- **Wind model**: a wind vector per mission, with ground speed and energy
  adjusted per leg by heading.
- **Climb and descent energy**: use waypoint altitude changes, with a
  climb efficiency and partial descent recovery.
- **Per-leg speed and altitude profiles** instead of one cruise speed.
- **Return-to-home check from every waypoint**: energy to get home from
  the worst point, not just the planned total.
- **Coverage path generation**: turn a survey polygon into a lawnmower
  grid at a given camera footprint and overlap.
- **Waypoint ordering optimization**: shortest tour through a point set
  for inspection missions.
- **3D geofence**: altitude floors and ceilings, plus circular keep-in
  and keep-out zones alongside polygons.
- **Battery realism**: discharge curves, Peukert effect, temperature
  derating.
- **Exporters**: MAVLink mission files, QGroundControl .plan format, and
  KML for map tools.

If you build one of these, open an issue or a pull request. Design notes
in the PR description are appreciated: what assumption changed, and what
it did to the verdict for the reference mission.

## Project structure

```text
src/drone_mission_planner/   the package (geo, mission, geofence,
                             energy, report, cli)
tests/                       pytest suite, reference checks included
examples/                    the Dhaka survey mission as JSON, plus a
                             runnable script that reports on it
.github/workflows/           CI: install and run the test suite on
                             every push
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: fork, branch,
test, pull request. Every change should keep `pytest -q` green and should
not move the validated numbers without explaining why in the PR.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Citation

If you use this project in research, please cite the archived release:

Sajid Kabir Saji (2026). drone-mission-planner (v1.0.1) [Software]. Zenodo. https://doi.org/10.5281/zenodo.23077816

The concept DOI https://doi.org/10.5281/zenodo.23077815 always resolves to the latest version.

## License

MIT. See [LICENSE](LICENSE).

## Author

Sajid Kabir Saji, aeronautical engineer. Research interests: onboard
autonomous decision-making for UAVs and solar-electric flight endurance.
More at [sajidkabir.com](https://sajidkabir.com).
