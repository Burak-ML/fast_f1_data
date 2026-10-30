"""Plumbing tests for the prediction model.

The dataset here is synthetic and only proves that training, saving, loading
and the API work end to end. It says nothing about real accuracy.
"""
import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ml import model


def synthetic(races=30, drivers=20, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(races):
        order = rng.permutation(drivers)
        for grid, d in enumerate(order, start=1):
            finish = int(np.clip(round(grid + rng.normal(0, 2)), 1, drivers))
            rows.append({
                "season": 2024 + i // 15, "round": i % 15 + 1,
                "driver_id": "d%d" % d, "constructor_id": "t%d" % (d // 2),
                "circuit_id": "c%d" % (i % 15), "grid": grid,
                "air_temperature": 20 + rng.normal(0, 4),
                "track_temperature": 30 + rng.normal(0, 6),
                "rainfall": int(rng.random() < 0.1), "finish_position": finish,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def trained(tmp_path):
    csv = tmp_path / "race_dataset.csv"
    synthetic().to_csv(csv, index=False)
    pipe, metrics = model.train(model.load_dataset(str(csv)))
    return pipe, metrics, tmp_path


def test_train_reports_honest_metrics(trained):
    _, m, _ = trained
    assert m["test_races"] == 6
    assert m["mae_model"] > 0 and m["mae_grid_baseline"] > 0
    assert isinstance(m["beats_baseline"], bool)
    assert "d0" in m["options"]["drivers"]


def test_predict_is_a_valid_position(trained):
    pipe, m, _ = trained
    out = model.predict(pipe, m, driver_id="d0", constructor_id="t0",
                        circuit_id="c0", grid=3, air_temperature=22,
                        track_temperature=35, rainfall=False)
    lo, hi = out["likely_range"]
    assert 1 <= out["predicted_position"] <= 20 and 1 <= lo <= hi <= 20


def test_unknown_driver_does_not_crash(trained):
    pipe, m, _ = trained
    out = model.predict(pipe, m, driver_id="rookie", constructor_id="t0",
                        circuit_id="c0", grid=10, air_temperature=22,
                        track_temperature=35, rainfall=True)
    assert 1 <= out["predicted_position"] <= 20


def test_missing_columns_are_rejected(tmp_path):
    csv = tmp_path / "bad.csv"
    synthetic().drop(columns=["grid"]).to_csv(csv, index=False)
    with pytest.raises(ValueError, match="grid"):
        model.load_dataset(str(csv))


def test_api(trained, monkeypatch):
    pipe, m, tmp = trained
    from backend.app.routes import predict as route
    route._load.cache_clear()

    app = FastAPI()
    app.include_router(route.router, prefix="/predict")
    client = TestClient(app)

    monkeypatch.setattr(model, "MODEL_PATH", str(tmp / "none.joblib"))
    monkeypatch.setattr(route, "_load", lambda: (_ for _ in ()).throw(FileNotFoundError("model not trained yet")))
    assert client.get("/predict/options").status_code == 503

    monkeypatch.setattr(route, "_load", lambda: (pipe, m))
    assert "drivers" in client.get("/predict/options").json()
    body = dict(driver_id="d0", constructor_id="t0", circuit_id="c0", grid=4,
                air_temperature=24, track_temperature=38, rainfall=False)
    r = client.post("/predict", json=body)
    assert r.status_code == 200 and 1 <= r.json()["predicted_position"] <= 20
    assert client.post("/predict", json={**body, "driver_id": "nobody"}).status_code == 422
    assert client.post("/predict", json={**body, "grid": 99}).status_code == 422
