"""Offline tests for analysis/collect.py: a fake client stands in for OpenF1,
so these check the joining logic, not the live API."""
import csv

import pytest

from analysis import collect, estimator


class FakeClient:
    """Three drivers; every race has the same shape, race 2 is wet."""

    def __init__(self, races=6):
        self.races = races

    def get(self, endpoint, **p):
        if endpoint == "sessions":
            return [{"session_key": 100 + i, "date_start": "2024-%02d-01" % (i + 1),
                     "location": "L%d" % i} for i in reversed(range(self.races))]
        key = p["session_key"]
        wet = key == 101
        if endpoint == "session_result":
            return [
                {"driver_number": 1, "position": 1, "dnf": False, "dns": False, "dsq": False},
                {"driver_number": 44, "position": 3, "dnf": False, "dns": False, "dsq": False},
                {"driver_number": 16, "position": None, "dnf": True, "dns": False, "dsq": False},
            ]
        if endpoint == "starting_grid":
            return [{"driver_number": 1, "position": 2}, {"driver_number": 44, "position": 1}]
        if endpoint == "drivers":
            return [{"driver_number": 1, "name_acronym": "VER", "team_name": "Red Bull"},
                    {"driver_number": 44, "name_acronym": "HAM", "team_name": "Mercedes"},
                    {"driver_number": 16, "name_acronym": "LEC", "team_name": "Ferrari"}]
        if endpoint == "weather":
            return [{"track_temperature": 30.0, "rainfall": 1 if wet else 0},
                    {"track_temperature": 40.0, "rainfall": 0}]
        raise AssertionError(endpoint)


def test_rows_are_joined_per_driver_and_ordered_by_date():
    rows = collect.race_rows(FakeClient(), 2024)
    assert len(rows) == 6 * 3
    first = rows[0]
    assert (first["round"], first["driver_id"], first["constructor_id"]) == (1, "VER", "Red Bull")
    assert first["grid"] == 2 and first["finish_position"] == 1
    assert first["track_temperature"] == 35.0 and first["rainfall"] == 0


def test_retirements_and_missing_grid_are_left_empty():
    lec = [r for r in collect.race_rows(FakeClient(), 2024) if r["driver_id"] == "LEC"][0]
    assert lec["finish_position"] == "" and lec["grid"] == ""


def test_rain_is_flagged_for_the_wet_race_only():
    rows = collect.race_rows(FakeClient(), 2024)
    wet = {r["round"] for r in rows if r["rainfall"] == 1}
    assert wet == {2}


def test_unfinished_races_are_skipped():
    class Empty(FakeClient):
        def get(self, endpoint, **p):
            return [] if endpoint in ("session_result", "starting_grid") else super().get(endpoint, **p)
    assert collect.race_rows(Empty(), 2024) == []


def test_output_loads_in_the_estimator(tmp_path):
    out = tmp_path / "race_dataset.csv"
    collect.write_csv(collect.race_rows(FakeClient(), 2024), str(out))
    with open(out, encoding="utf-8") as f:
        assert next(csv.reader(f)) == collect.COLUMNS
    df = estimator.load_dataset(str(out))
    assert len(df) == 6 * 2                      # the DNF / no-grid rows are dropped
    assert set(df["driver_id"]) == {"VER", "HAM"}
