"""Mission model: legs, totals, duration, and JSON round-tripping."""

from drone_mission_planner.mission import Mission, Waypoint


def survey_mission() -> Mission:
    return Mission(
        name="Square survey",
        cruise_speed_mps=10.0,
        waypoints=[
            Waypoint(23.8103, 90.4125),
            Waypoint(23.8300, 90.4300, action="photo"),
            Waypoint(23.8300, 90.4600, action="loiter", loiter_s=30.0),
            Waypoint(23.8103, 90.4125),
        ],
    )


def test_total_distance_equals_sum_of_legs():
    mission = survey_mission()
    legs = mission.legs()
    assert len(legs) == len(mission.waypoints) - 1
    assert abs(mission.total_distance_m() - sum(leg.distance_m for leg in legs)) < 1e-9
    # Cumulative distance on the last leg is the mission total.
    assert abs(legs[-1].cumulative_m - mission.total_distance_m()) < 1e-9
    assert mission.total_distance_m() > 0.0


def test_json_round_trip_preserves_waypoints(tmp_path):
    mission = survey_mission()
    path = tmp_path / "mission.json"
    mission.save_json(path)
    loaded = Mission.load_json(path)
    assert loaded.name == mission.name
    assert loaded.cruise_speed_mps == mission.cruise_speed_mps
    assert len(loaded.waypoints) == len(mission.waypoints)
    for original, restored in zip(mission.waypoints, loaded.waypoints):
        assert restored.lat == original.lat
        assert restored.lon == original.lon
        assert restored.altitude_m == original.altitude_m
        assert restored.action == original.action
        assert restored.loiter_s == original.loiter_s
    assert loaded.total_distance_m() == mission.total_distance_m()


def test_duration_includes_loiter_time():
    mission = survey_mission()
    cruise_only = mission.total_distance_m() / mission.cruise_speed_mps
    assert mission.total_dwell_s() == 30.0
    assert abs(mission.estimated_duration_s() - (cruise_only + 30.0)) < 1e-9


def test_photo_action_has_no_dwell():
    wp = Waypoint(23.81, 90.41, action="photo", loiter_s=99.0)
    assert wp.dwell_s == 0.0


def test_invalid_action_rejected():
    try:
        Waypoint(23.81, 90.41, action="barrel-roll")
    except ValueError:
        return
    raise AssertionError("an unknown action should raise ValueError")
