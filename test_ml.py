"""Tests for the statistics-based estimator.

The data is synthetic with effects planted on purpose, so the tests can check
that the estimator finds them. They say nothing about real F1 accuracy.
"""
import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from analysis import estimator


def synthetic(races=40, drivers=20, seed=0):
    """d0 gains 3 places per race, d19 loses 3, and rain shuffles the order."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(races):
        rain = i % 5 == 0
        temp = 30 + rng.normal(0, 6)
        order = rng.permutation(drivers)
        for grid, d in enumerate(order, start=1):
            finish = grid + {0: -3, 19: 3}.get(int(d), 0) + rng.normal(0, 1.5)
            if rain:
                finish = 0.4 * finish + 0.6 * rng.uniform(1, drivers)
            rows.append({
                "season": 2024 + i // 20, "round": i % 20 + 1,
                "driver_id": "d%d" % d, "constructor_id": "t%d" % (d // 2),
                "grid": grid, "track_temperature": temp, "rainfall": int(rain),
                "finish_position": int(np.clip(round(finish), 1, drivers)),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def csv(tmp_path):
    p = tmp_path / "race_dataset.csv"
    synthetic().to_csv(p, index=False)
    return str(p)


def test_finds_the_planted_driver_effects(csv):
    a = estimator.Analyst(estimator.load_dataset(csv))
    gain = lambda d: a.team[a.team_of[d]] + a.driver[d]   # team + driver
    assert gain("d0") < -1.5        # gains places
    assert gain("d19") > 1.5        # loses places
    assert a.pull["rain"] > 0.2     # rain pulls the order toward the middle


def test_rain_moves_a_pole_sitter_back(csv):
    a = estimator.Analyst(estimator.load_dataset(csv))
    dry = a.estimate("d5", 1, 30, False)["raw_position"]
    wet = a.estimate("d5", 1, 30, True)["raw_position"]
    assert wet > dry


def test_breakdown_adds_up(csv):
    a = estimator.Analyst(estimator.load_dataset(csv))
    out = a.estimate("d0", 8, 35, False)
    b = out["breakdown"]
    assert out["raw_position"] == pytest.approx(
        np.clip(sum(b.values()), 1, 20), abs=0.05)


def test_unknown_driver_falls_back_to_grid_history(csv):
    a = estimator.Analyst(estimator.load_dataset(csv))
    out = a.estimate("rookie", 10, 30, False)
    assert out["known_driver"] is False
    assert out["breakdown"]["driver"] == 0 and out["breakdown"]["team"] == 0


def test_evaluate_compares_against_the_grid_baseline(csv):
    m = estimator.evaluate(estimator.load_dataset(csv))
    assert m["test_races"] == 8
    assert m["mae_full"] < m["mae_grid_baseline"]   # planted effects are found
    assert m["beats_baseline"] is True


def test_missing_columns_are_rejected(tmp_path):
    p = tmp_path / "bad.csv"
    synthetic().drop(columns=["grid"]).to_csv(p, index=False)
    with pytest.raises(ValueError, match="grid"):
        estimator.load_dataset(str(p))


def test_api(csv, monkeypatch):
    from backend.app.routes import predict as route
    route._load.cache_clear()
    app = FastAPI()
    app.include_router(route.router, prefix="/predict")
    client = TestClient(app)

    monkeypatch.setattr(route, "DATA_PATH", "/nonexistent.csv")
    assert client.get("/predict/options").status_code == 503

    route._load.cache_clear()
    monkeypatch.setattr(route, "DATA_PATH", csv)
    assert "d0" in client.get("/predict/options").json()["drivers"]
    body = dict(driver_id="d0", grid=4, track_temperature=38, rainfall=False)
    r = client.post("/predict", json=body)
    assert r.status_code == 200
    assert 1 <= r.json()["predicted_position"] <= 20 and "breakdown" in r.json()
    assert client.post("/predict", json={**body, "driver_id": "nobody"}).status_code == 422
    assert client.post("/predict", json={**body, "grid": 99}).status_code == 422
    route._load.cache_clear()
