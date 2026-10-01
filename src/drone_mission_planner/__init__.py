"""drone-mission-planner: multirotor mission planning and feasibility.

Computes mission legs on a spherical Earth, checks waypoints against a
polygon geofence, and estimates whether the aircraft's battery can fly the
mission with a reserve to spare. Planning estimates, stated honestly: see
the energy module for exactly what is and is not modelled.
"""

from .energy import (
    FEASIBLE,
    INFEASIBLE,
    MARGINAL,
    AircraftSpec,
    EnergyAssessment,
    LegEnergy,
    assess_mission,
    cruise_power_w,
    hover_power_w,
)
from .geo import destination_point, haversine_m, initial_bearing_deg
from .geofence import Geofence, GeofenceViolation, point_in_polygon
from .mission import Leg, Mission, Waypoint
from .report import build_report

__version__ = "1.0.0"

__all__ = [
    "AircraftSpec",
    "EnergyAssessment",
    "FEASIBLE",
    "Geofence",
    "GeofenceViolation",
    "INFEASIBLE",
    "Leg",
    "LegEnergy",
    "MARGINAL",
    "Mission",
    "Waypoint",
    "__version__",
    "assess_mission",
    "build_report",
    "cruise_power_w",
    "destination_point",
    "haversine_m",
    "hover_power_w",
    "initial_bearing_deg",
    "point_in_polygon",
]
