"""Geodesy sanity checks against known city-to-city values."""

import math

from drone_mission_planner.geo import (
    destination_point,
    haversine_m,
    initial_bearing_deg,
)

DHAKA = (23.8103, 90.4125)
CHATTOGRAM = (22.3569, 91.7832)


def test_haversine_dhaka_to_chattogram():
    # Known road-free straight-line distance is about 214 km. The haversine
    # on a 6,371 km sphere gives 214.0 km; allow a few km of slack for the
    # spherical-Earth approximation.
    distance_km = haversine_m(*DHAKA, *CHATTOGRAM) / 1000.0
    assert abs(distance_km - 214.0) < 5.0


def test_haversine_same_point_is_zero():
    assert haversine_m(*DHAKA, *DHAKA) == 0.0


def test_bearing_dhaka_to_chattogram_is_southeast():
    # Chattogram lies south-east of Dhaka; the initial bearing works out to
    # about 139 degrees, squarely in the south-east quadrant.
    bearing = initial_bearing_deg(*DHAKA, *CHATTOGRAM)
    assert 90.0 < bearing < 180.0
    assert abs(bearing - 139.0) < 5.0


def test_bearing_due_north_and_east():
    assert initial_bearing_deg(0.0, 0.0, 1.0, 0.0) == 0.0
    assert abs(initial_bearing_deg(0.0, 0.0, 0.0, 1.0) - 90.0) < 0.01


def test_destination_point_round_trip():
    # Fly 10 km from Dhaka on a bearing of 45 degrees, then measure the way
    # back: distance and position must be consistent.
    lat2, lon2 = destination_point(*DHAKA, 45.0, 10_000.0)
    assert abs(haversine_m(*DHAKA, lat2, lon2) - 10_000.0) < 1.0
    # North-east of the start means both coordinates increase here.
    assert lat2 > DHAKA[0]
    assert lon2 > DHAKA[1]
    # One degree of latitude is about 111.19 km on this sphere.
    lat3, _ = destination_point(0.0, 0.0, 0.0, 111_195.0)
    assert abs(lat3 - 1.0) < 0.01
    assert math.isfinite(lat3)
