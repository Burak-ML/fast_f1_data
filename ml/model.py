"""Finishing-position model.

Inputs: starting grid slot, air/track temperature, rain, driver, team, circuit.
Output: expected finishing position, plus a typical error band measured on
races the model never saw during training.
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "model.joblib")
METRICS_PATH = os.path.join(ARTIFACT_DIR, "metrics.json")

CATEGORICAL = ["driver_id", "constructor_id", "circuit_id"]
NUMERIC = ["grid", "air_temperature", "track_temperature", "rainfall"]
TARGET = "finish_position"
REQUIRED = ["season", "round"] + CATEGORICAL + NUMERIC + [TARGET]

MAX_POSITION = 20
TEST_RACE_FRACTION = 0.2


def load_dataset(path: str) -> pd.DataFrame:
    """Read the training CSV (one row per driver per race).

    Rows without a classified finish (DNF, DSQ) or without a grid slot are
    dropped, so the model predicts the position of a driver who finishes.
    """
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("dataset is missing columns: %s" % ", ".join(missing))
    df = df[REQUIRED].copy()
    df["rainfall"] = df["rainfall"].astype(float)
    df = df.dropna(subset=[TARGET, "grid"])
    return df.sort_values(["season", "round"]).reset_index(drop=True)


def build_pipeline() -> Pipeline:
    encode = ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value",
                                unknown_value=np.nan), CATEGORICAL)],
        remainder="passthrough",
    )
    regressor = HistGradientBoostingRegressor(
        categorical_features=[0, 1, 2],
        learning_rate=0.05, max_iter=200, max_depth=3,
        min_samples_leaf=20, random_state=0,
    )
    return Pipeline([("encode", encode), ("model", regressor)])


def _features(df: pd.DataFrame) -> pd.DataFrame:
    return df[CATEGORICAL + NUMERIC]


def train(df: pd.DataFrame):
    """Fit on the early races, score on the latest ones, then refit on all.

    The split is by race and by time: a random split would put laps from the
    same race on both sides and flatter the score.
    """
    races = df[["season", "round"]].drop_duplicates().reset_index(drop=True)
    if len(races) < 5:
        raise ValueError("need at least 5 races to train, got %d" % len(races))
    n_test = max(1, int(round(len(races) * TEST_RACE_FRACTION)))
    test_races = set(map(tuple, races.tail(n_test).to_numpy()))
    is_test = df.apply(lambda r: (r["season"], r["round"]) in test_races, axis=1)
    train_df, test_df = df[~is_test], df[is_test]

    pipe = build_pipeline().fit(_features(train_df), train_df[TARGET])
    pred = np.clip(pipe.predict(_features(test_df)), 1, MAX_POSITION)
    err = np.abs(pred - test_df[TARGET].to_numpy())
    baseline = np.abs(np.clip(test_df["grid"].to_numpy(), 1, MAX_POSITION)
                      - test_df[TARGET].to_numpy())

    final = build_pipeline().fit(_features(df), df[TARGET])
    metrics = {
        "rows": int(len(df)),
        "races": int(len(races)),
        "test_races": int(n_test),
        "mae_model": round(float(err.mean()), 3),
        "mae_grid_baseline": round(float(baseline.mean()), 3),
        "beats_baseline": bool(err.mean() < baseline.mean()),
        "within_3_positions": round(float((err <= 3).mean()), 3),
        "typical_error": round(float(np.percentile(err, 80)), 2),
        "options": {
            "drivers": sorted(df["driver_id"].unique().tolist()),
            "constructors": sorted(df["constructor_id"].unique().tolist()),
            "circuits": sorted(df["circuit_id"].unique().tolist()),
            "grid_max": int(min(df["grid"].max(), 22)),
        },
    }
    return final, metrics


def save(pipe, metrics, model_path=MODEL_PATH, metrics_path=METRICS_PATH):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(pipe, model_path)
    with open(metrics_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def load(model_path=MODEL_PATH, metrics_path=METRICS_PATH):
    if not (os.path.exists(model_path) and os.path.exists(metrics_path)):
        raise FileNotFoundError("model not trained yet: run `python -m ml.train`")
    with open(metrics_path, encoding="utf-8") as f:
        return joblib.load(model_path), json.load(f)


def predict(pipe, metrics, *, driver_id, constructor_id, circuit_id, grid,
            air_temperature, track_temperature, rainfall):
    row = pd.DataFrame([{
        "driver_id": driver_id, "constructor_id": constructor_id,
        "circuit_id": circuit_id, "grid": grid,
        "air_temperature": air_temperature,
        "track_temperature": track_temperature,
        "rainfall": float(rainfall),
    }])
    raw = float(np.clip(pipe.predict(row)[0], 1, MAX_POSITION))
    band = metrics["typical_error"]
    return {
        "predicted_position": int(round(raw)),
        "raw_position": round(raw, 2),
        "likely_range": [max(1, int(round(raw - band))),
                         min(MAX_POSITION, int(round(raw + band)))],
        "typical_error": band,
    }
