"""Great-circle geometry on a spherical Earth.

Small, dependency-free helpers shared by the mission, geofence, and energy
modules: haversine distance, initial bearing, and the destination point
reached by travelling a given distance along a given bearing.

The Earth is treated as a sphere of mean radius 6,371 km. That is the
standard planning approximation: errors stay well under half a percent at
mission scales, which is far below the uncertainty in any power or wind
estimate built on top of these numbers.
"""

from __future__ import annotations

import math

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon points.

    Uses the haversine formula, which stays numerically accurate for the
    short distances typical of multirotor missions (unlike the spherical
    law of cosines, which loses precision when the points are close).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def initial_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial great-circle bearing from point 1 to point 2, in degrees.

    The result is normalised to 0 to 360, where 0 is north, 90 is east,
    180 is south, and 270 is west. This is the bearing at departure; on a
    long leg the bearing changes slightly along the way, which a
    mission-scale planner can safely ignore.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)
    y = math.sin(d_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def destination_point(
    lat: float, lon: float, bearing_deg: float, distance_m: float
) -> tuple[float, float]:
    """Lat/lon reached by travelling distance_m from a start point.

    Follows the great circle whose initial bearing is bearing_deg. The
    longitude is normalised to -180 to 180.
    """
    delta = distance_m / EARTH_RADIUS_M
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta)
        + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    )
    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    lon2 = (math.degrees(lambda2) + 540.0) % 360.0 - 180.0
    return math.degrees(phi2), lon2
