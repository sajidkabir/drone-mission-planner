"""Tests for the MAVLink (QGC WPL 110) mission exporter."""

import pytest

from drone_mission_planner import Mission, Waypoint
from drone_mission_planner.export import (
    CMD_NAV_LAND,
    CMD_NAV_LOITER_TIME,
    CMD_NAV_TAKEOFF,
    CMD_NAV_WAYPOINT,
    FRAME_GLOBAL_RELATIVE_ALT,
    WPL_HEADER,
    to_qgc_wpl,
    write_qgc_wpl,
)


def sample_mission() -> Mission:
    return Mission(
        name="export sample",
        cruise_speed_mps=10.0,
        waypoints=[
            Waypoint(23.8103, 90.4125, altitude_m=50.0),
            Waypoint(23.8300, 90.4300, altitude_m=60.0, action="photo"),
            Waypoint(23.8400, 90.4400, altitude_m=70.0, action="loiter", loiter_s=45.0),
            Waypoint(23.8103, 90.4125, altitude_m=50.0),
        ],
    )


def data_rows(text: str) -> list[list[str]]:
    lines = text.splitlines()
    assert lines[0] == WPL_HEADER
    rows = [line.split("\t") for line in lines[1:]]
    for row in rows:
        assert len(row) == 12, f"row has {len(row)} columns: {row}"
    return rows


def test_header_and_trailing_newline():
    text = to_qgc_wpl(sample_mission())
    assert text.startswith(WPL_HEADER + "\n")
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_row_count_home_takeoff_waypoints_land():
    mission = sample_mission()
    rows = data_rows(to_qgc_wpl(mission))
    # home + takeoff + one row per waypoint + land
    assert len(rows) == len(mission.waypoints) + 3
    assert [int(r[0]) for r in rows] == list(range(len(rows)))


def test_home_row():
    rows = data_rows(to_qgc_wpl(sample_mission()))
    seq, current, frame, command = (int(rows[0][i]) for i in range(4))
    assert seq == 0
    assert current == 1
    assert frame == FRAME_GLOBAL_RELATIVE_ALT
    assert command == CMD_NAV_WAYPOINT
    assert rows[0][8] == "23.810300"
    assert rows[0][9] == "90.412500"
    assert rows[0][10] == "0.000000"


def test_takeoff_climbs_to_first_waypoint_altitude():
    rows = data_rows(to_qgc_wpl(sample_mission()))
    assert int(rows[1][3]) == CMD_NAV_TAKEOFF
    assert rows[1][8] == "23.810300"
    assert rows[1][9] == "90.412500"
    assert rows[1][10] == "50.000000"


def test_waypoint_rows_carry_positions_and_altitudes():
    rows = data_rows(to_qgc_wpl(sample_mission()))
    assert int(rows[2][3]) == CMD_NAV_WAYPOINT
    assert rows[2][8] == "23.810300"
    assert rows[2][10] == "50.000000"
    assert int(rows[3][3]) == CMD_NAV_WAYPOINT
    assert rows[3][8] == "23.830000"
    assert rows[3][10] == "60.000000"


def test_photo_waypoint_is_plain_waypoint_without_camera_command():
    # The exporter states this honestly: no camera trigger is invented.
    rows = data_rows(to_qgc_wpl(sample_mission()))
    assert int(rows[3][3]) == CMD_NAV_WAYPOINT


def test_loiter_waypoint_becomes_loiter_time_with_seconds():
    rows = data_rows(to_qgc_wpl(sample_mission()))
    assert int(rows[4][3]) == CMD_NAV_LOITER_TIME
    assert rows[4][4] == "45"
    assert rows[4][8] == "23.840000"
    assert rows[4][10] == "70.000000"


def test_land_row_at_last_waypoint():
    rows = data_rows(to_qgc_wpl(sample_mission()))
    land = rows[-1]
    assert int(land[3]) == CMD_NAV_LAND
    assert land[8] == "23.810300"
    assert land[9] == "90.412500"
    assert land[10] == "0.000000"


def test_all_rows_autocontinue_and_numeric():
    rows = data_rows(to_qgc_wpl(sample_mission()))
    for row in rows:
        assert row[11] == "1"
        for column in row[4:11]:
            float(column)  # every param and coordinate parses


def test_single_waypoint_mission_exports():
    mission = Mission(waypoints=[Waypoint(23.81, 90.41, altitude_m=40.0)])
    rows = data_rows(to_qgc_wpl(mission))
    assert len(rows) == 4  # home, takeoff, the waypoint, land
    assert int(rows[2][3]) == CMD_NAV_WAYPOINT
    assert int(rows[3][3]) == CMD_NAV_LAND


def test_empty_mission_raises():
    with pytest.raises(ValueError, match="no waypoints"):
        to_qgc_wpl(Mission())


def test_write_file_round_trip(tmp_path):
    target = tmp_path / "mission.waypoints"
    returned = write_qgc_wpl(sample_mission(), target)
    assert returned == target
    assert target.read_text(encoding="utf-8") == to_qgc_wpl(sample_mission())


def test_cli_export_writes_file(tmp_path, capsys):
    from drone_mission_planner.cli import main

    mission_path = tmp_path / "m.json"
    out_path = tmp_path / "m.waypoints"
    sample_mission().save_json(mission_path)
    assert main(["export", str(mission_path), "-o", str(out_path)]) == 0
    text = out_path.read_text(encoding="utf-8")
    assert text.startswith(WPL_HEADER + "\n")
    out, _ = capsys.readouterr()
    assert "m.waypoints" in out


def test_cli_export_default_output_name(tmp_path):
    from drone_mission_planner.cli import main

    mission_path = tmp_path / "survey.json"
    sample_mission().save_json(mission_path)
    assert main(["export", str(mission_path)]) == 0
    assert (tmp_path / "survey.waypoints").exists()


def test_cli_export_missing_file_errors():
    from drone_mission_planner.cli import main

    assert main(["export", "does-not-exist.json"]) == 2


def test_cli_export_unknown_format_exits_2(tmp_path):
    from drone_mission_planner.cli import main

    mission_path = tmp_path / "m.json"
    sample_mission().save_json(mission_path)
    with pytest.raises(SystemExit) as exc:
        main(["export", str(mission_path), "--format", "kml"])
    assert exc.value.code == 2
