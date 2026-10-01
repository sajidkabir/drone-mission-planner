"""Geofence: point-in-polygon cases and mission validation."""

from drone_mission_planner.geofence import Geofence, point_in_polygon
from drone_mission_planner.mission import Mission, Waypoint

# A square fence in (lat, lon): lat 0 to 10, lon 0 to 10.
SQUARE = [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0)]


def test_point_inside_polygon():
    assert point_in_polygon(5.0, 5.0, SQUARE) is True
    assert point_in_polygon(0.5, 9.5, SQUARE) is True


def test_point_outside_polygon():
    assert point_in_polygon(15.0, 5.0, SQUARE) is False
    assert point_in_polygon(5.0, -1.0, SQUARE) is False
    assert point_in_polygon(-3.0, -3.0, SQUARE) is False


def test_point_on_vertex_counts_as_inside():
    for lat, lon in SQUARE:
        assert point_in_polygon(lat, lon, SQUARE) is True


def test_point_on_edge_counts_as_inside():
    assert point_in_polygon(0.0, 5.0, SQUARE) is True
    assert point_in_polygon(5.0, 10.0, SQUARE) is True


def test_geofence_flags_outside_waypoint():
    fence = Geofence(vertices=SQUARE, name="test field")
    mission = Mission(
        waypoints=[
            Waypoint(5.0, 5.0),
            Waypoint(20.0, 5.0),  # outside, to the north
            Waypoint(6.0, 6.0),
        ]
    )
    violations = fence.violations(mission)
    assert len(violations) == 1
    assert violations[0].waypoint_index == 1
    assert violations[0].lat == 20.0
