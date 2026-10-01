"""Energy feasibility: can this aircraft fly this mission on this battery?

Two power models, both stated honestly as planning estimates, not
flight-test data:

- **Hover power** comes from actuator-disk momentum theory, the same model
  used in the author's solar-uav-sim project: induced velocity
  v_i = sqrt(T / (2 * rho * A)), power P = T * v_i / figure_of_merit, with
  thrust T = m * g and A the total rotor disk area.

- **Cruise power** is the standard two-term forward-flight approximation:
  an induced term that falls with speed, P_ind = (m * g)^2 / (2 * rho * A * v)
  (the high-speed approximation, with speed clamped at 1 m/s so it stays
  finite), plus a parasite term that grows with the cube of speed,
  P_par = 0.5 * rho * CdA * v^3, where CdA is the equivalent flat-plate
  drag area. A constant avionics draw is added to both.

What is NOT modelled: wind, climb and descent, acceleration, turns,
battery discharge curves, temperature. A real aircraft will use more
energy than this estimate, which is exactly why the verdict applies a
reserve margin and a "marginal" band instead of a single hard line.

Verdicts:

- **feasible**: mission energy fits in the usable battery (capacity after
  the reserve) with at least 10 percent of the usable energy to spare.
- **marginal**: it fits, but inside that last 10 percent. The binding
  constraint is the reserve margin.
- **infeasible**: mission energy exceeds the usable battery. The binding
  constraint is battery energy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mission import Mission

G = 9.80665

FEASIBLE = "feasible"
MARGINAL = "marginal"
INFEASIBLE = "infeasible"


@dataclass
class AircraftSpec:
    """The aircraft and battery the mission is checked against."""

    mass_kg: float = 3.0
    battery_wh: float = 500.0
    rotor_diameter_m: float = 0.33
    num_rotors: int = 4
    figure_of_merit: float = 0.65
    air_density_kg_m3: float = 1.225
    drag_area_m2: float = 0.03  # equivalent flat-plate area, Cd * A
    avionics_w: float = 10.0

    @property
    def disk_area_m2(self) -> float:
        """Total rotor disk area across all rotors."""
        return self.num_rotors * math.pi * (self.rotor_diameter_m / 2.0) ** 2

    @classmethod
    def from_dict(cls, data: dict) -> "AircraftSpec":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def hover_power_w(aircraft: AircraftSpec) -> float:
    """Hover power in watts from momentum theory, avionics included."""
    thrust = aircraft.mass_kg * G
    v_induced = math.sqrt(
        thrust / (2.0 * aircraft.air_density_kg_m3 * aircraft.disk_area_m2)
    )
    return thrust * v_induced / aircraft.figure_of_merit + aircraft.avionics_w


def cruise_power_w(aircraft: AircraftSpec, speed_mps: float) -> float:
    """Cruise power in watts at a steady forward speed, avionics included."""
    v = max(speed_mps, 1.0)
    weight = aircraft.mass_kg * G
    induced = weight**2 / (2.0 * aircraft.air_density_kg_m3 * aircraft.disk_area_m2 * v)
    parasite = 0.5 * aircraft.air_density_kg_m3 * aircraft.drag_area_m2 * v**3
    return induced + parasite + aircraft.avionics_w


@dataclass
class LegEnergy:
    """Energy and time for one leg at cruise power."""

    leg_index: int  # 1-based, matches the mission's Leg.index
    distance_m: float
    time_s: float
    energy_wh: float


@dataclass
class EnergyAssessment:
    """The full energy picture for one mission and aircraft pairing."""

    cruise_power_w: float
    hover_power_w: float
    leg_energies: list[LegEnergy] = field(default_factory=list)
    cruise_energy_wh: float = 0.0
    loiter_energy_wh: float = 0.0
    total_energy_wh: float = 0.0
    usable_energy_wh: float = 0.0
    reserve_fraction: float = 0.20
    margin_wh: float = 0.0  # usable minus total; negative means over budget
    verdict: str = FEASIBLE
    binding_constraint: str = "none"


def assess_mission(
    mission: "Mission",
    aircraft: AircraftSpec,
    reserve_fraction: float = 0.20,
) -> EnergyAssessment:
    """Per-leg and total energy for a mission, with a feasibility verdict."""
    if not 0.0 <= reserve_fraction < 1.0:
        raise ValueError("reserve_fraction must be in [0, 1)")
    speed = mission.cruise_speed_mps
    p_cruise = cruise_power_w(aircraft, speed)
    p_hover = hover_power_w(aircraft)

    leg_energies: list[LegEnergy] = []
    cruise_energy = 0.0
    for leg in mission.legs():
        time_s = leg.distance_m / speed
        energy_wh = p_cruise * time_s / 3600.0
        cruise_energy += energy_wh
        leg_energies.append(
            LegEnergy(
                leg_index=leg.index,
                distance_m=leg.distance_m,
                time_s=time_s,
                energy_wh=energy_wh,
            )
        )

    loiter_energy = p_hover * mission.total_dwell_s() / 3600.0
    total = cruise_energy + loiter_energy
    usable = aircraft.battery_wh * (1.0 - reserve_fraction)
    margin = usable - total

    if total > usable:
        verdict = INFEASIBLE
        binding = "battery energy"
    elif total > 0.9 * usable:
        verdict = MARGINAL
        binding = "reserve margin"
    else:
        verdict = FEASIBLE
        binding = "none"

    return EnergyAssessment(
        cruise_power_w=p_cruise,
        hover_power_w=p_hover,
        leg_energies=leg_energies,
        cruise_energy_wh=cruise_energy,
        loiter_energy_wh=loiter_energy,
        total_energy_wh=total,
        usable_energy_wh=usable,
        reserve_fraction=reserve_fraction,
        margin_wh=margin,
        verdict=verdict,
        binding_constraint=binding,
    )
