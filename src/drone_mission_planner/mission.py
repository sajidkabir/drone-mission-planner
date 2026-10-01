"""Mission data model: waypoints, legs, and JSON round-tripping.

A Mission is an ordered list of Waypoints flown at one cruise speed. The
first waypoint is normally the launch point and the last one the recovery
point, but the model does not force that: legs are simply computed between
consecutive waypoints.

A mission file is JSON with this shape (the "aircraft" and "geofence"
sections are read by the CLI and the report builder, not by this module):

    {
      "name": "Dhaka north survey",
      "cruise_speed_mps": 10.0,
      "aircraft": {"mass_kg": 3.0, "battery_wh": 400.0},
      "geofence": [[23.80, 90.40], [23.80, 90.475], ...],
      "waypoints": [
        {"lat": 23.8103, "lon": 90.4125, "altitude_m": 50, "action": "none"},
        {"lat": 23.83, "lon": 90.43, "altitude_m": 60, "action": "photo"}
      ]
    }

Waypoint actions are "none" (pass through), "photo" (trigger a camera at
the point, no dwell time), and "loiter" (hold position for loiter_s
seconds, which costs hover energy).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .geo import haversine_m, initial_bearing_deg

ACTIONS = ("none", "photo", "loiter")


@dataclass
class Waypoint:
    """One point in a mission."""

    lat: float
    lon: float
    altitude_m: float = 50.0
    action: str = "none"
    loiter_s: float = 0.0

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise ValueError(
                f"unknown waypoint action {self.action!r}, expected one of {ACTIONS}"
            )
        if self.loiter_s < 0:
            raise ValueError("loiter_s cannot be negative")

    @property
    def dwell_s(self) -> float:
        """Seconds spent holding at this waypoint (loiter actions only)."""
        return self.loiter_s if self.action == "loiter" else 0.0

    def to_dict(self) -> dict:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "altitude_m": self.altitude_m,
            "action": self.action,
            "loiter_s": self.loiter_s,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Waypoint":
        return cls(
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            altitude_m=float(data.get("altitude_m", 50.0)),
            action=str(data.get("action", "none")),
            loiter_s=float(data.get("loiter_s", 0.0)),
        )


@dataclass
class Leg:
    """One flown segment between two consecutive waypoints."""

    index: int  # 1-based leg number
    from_index: int  # 0-based waypoint index the leg departs from
    to_index: int  # 0-based waypoint index the leg arrives at
    distance_m: float
    bearing_deg: float
    cumulative_m: float  # distance from mission start to the end of this leg


@dataclass
class Mission:
    """An ordered waypoint list flown at a single cruise speed."""

    name: str = "Untitled mission"
    waypoints: list[Waypoint] = field(default_factory=list)
    cruise_speed_mps: float = 12.0

    def legs(self) -> list[Leg]:
        """Compute the leg between each pair of consecutive waypoints."""
        legs: list[Leg] = []
        cumulative = 0.0
        for i in range(len(self.waypoints) - 1):
            a = self.waypoints[i]
            b = self.waypoints[i + 1]
            distance = haversine_m(a.lat, a.lon, b.lat, b.lon)
            cumulative += distance
            legs.append(
                Leg(
                    index=i + 1,
                    from_index=i,
                    to_index=i + 1,
                    distance_m=distance,
                    bearing_deg=initial_bearing_deg(a.lat, a.lon, b.lat, b.lon),
                    cumulative_m=cumulative,
                )
            )
        return legs

    def total_distance_m(self) -> float:
        """Sum of all leg distances, in metres."""
        return sum(leg.distance_m for leg in self.legs())

    def total_dwell_s(self) -> float:
        """Total loiter time across all waypoints, in seconds."""
        return sum(wp.dwell_s for wp in self.waypoints)

    def estimated_duration_s(self, cruise_speed_mps: float | None = None) -> float:
        """Flight time estimate: cruise time over all legs plus dwell time.

        Climb, descent, acceleration, and turns are not modelled, so treat
        this as a lower bound. The energy module applies the same leg times
        so the report stays internally consistent.
        """
        speed = self.cruise_speed_mps if cruise_speed_mps is None else cruise_speed_mps
        if speed <= 0:
            raise ValueError("cruise speed must be positive")
        return self.total_distance_m() / speed + self.total_dwell_s()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cruise_speed_mps": self.cruise_speed_mps,
            "waypoints": [wp.to_dict() for wp in self.waypoints],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Mission":
        return cls(
            name=str(data.get("name", "Untitled mission")),
            cruise_speed_mps=float(data.get("cruise_speed_mps", 12.0)),
            waypoints=[Waypoint.from_dict(wp) for wp in data.get("waypoints", [])],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Mission":
        return cls.from_dict(json.loads(text))

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def load_json(cls, path: str | Path) -> "Mission":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))
