"""Polygon geofence: is every waypoint inside the allowed area?

The point-in-polygon test is the standard ray-casting (even-odd) algorithm,
with one simplification stated plainly: longitude and latitude are treated
as planar x/y coordinates. For a mission-scale fence (a few kilometres
across, away from the poles) the distortion this introduces is centimetres
to metres, far below GPS accuracy. Do not use it for continent-scale
polygons or fences crossing the antimeridian.

Points exactly on a vertex or an edge count as inside. That is a deliberate
choice: a waypoint placed on the boundary was almost certainly meant to be
allowed, and it keeps the test free of floating-point surprises at corners.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mission import Mission

_EPS = 1e-12


def _on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> bool:
    """True if point (px, py) lies on segment (ax, ay) to (bx, by)."""
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cross) > _EPS:
        return False
    return (
        min(ax, bx) - _EPS <= px <= max(ax, bx) + _EPS
        and min(ay, by) - _EPS <= py <= max(ay, by) + _EPS
    )


def point_in_polygon(lat: float, lon: float, vertices: list[tuple[float, float]]) -> bool:
    """True if (lat, lon) is inside the polygon, boundary included.

    vertices is a list of (lat, lon) pairs in order, either clockwise or
    counter-clockwise. The polygon is closed automatically; the first
    vertex does not need to be repeated at the end.
    """
    if len(vertices) < 3:
        raise ValueError("a geofence polygon needs at least 3 vertices")
    x, y = lon, lat
    points = [(v_lon, v_lat) for v_lat, v_lon in vertices]
    n = len(points)
    for i in range(n):
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        if _on_segment(x, y, ax, ay, bx, by):
            return True
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = points[i]
        xj, yj = points[j]
        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_cross:
                inside = not inside
        j = i
    return inside


@dataclass
class GeofenceViolation:
    """One waypoint found outside the fence."""

    waypoint_index: int  # 0-based index into the mission's waypoint list
    lat: float
    lon: float


@dataclass
class Geofence:
    """A named polygon the mission is required to stay inside."""

    vertices: list[tuple[float, float]] = field(default_factory=list)
    name: str = "geofence"

    def contains(self, lat: float, lon: float) -> bool:
        return point_in_polygon(lat, lon, self.vertices)

    def violations(self, mission: "Mission") -> list[GeofenceViolation]:
        """Every waypoint outside the fence, in mission order."""
        found: list[GeofenceViolation] = []
        for i, wp in enumerate(mission.waypoints):
            if not self.contains(wp.lat, wp.lon):
                found.append(GeofenceViolation(waypoint_index=i, lat=wp.lat, lon=wp.lon))
        return found

    @classmethod
    def from_dict(cls, data) -> "Geofence":
        """Accepts {"name": ..., "vertices": [[lat, lon], ...]} or a bare
        list of [lat, lon] pairs."""
        if isinstance(data, list):
            return cls(vertices=[(float(a), float(b)) for a, b in data])
        return cls(
            name=str(data.get("name", "geofence")),
            vertices=[(float(a), float(b)) for a, b in data.get("vertices", [])],
        )
