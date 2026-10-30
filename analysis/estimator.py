"""Finishing-position estimate built from historical race statistics.

No model is trained. Everything below is a table of averages computed from
past races, with every effect shrunk toward zero when it rests on few races,
so one lucky weekend cannot make a driver look like a legend.

    estimate = what a grid slot usually finishes
             + what the team usually adds or loses
             + what the driver usually adds or loses on top of the team
             + how much rain / a hot track pulls the order toward the middle
"""
import numpy as np
import pandas as pd

REQUIRED = ["season", "round", "driver_id", "constructor_id", "grid",
            "track_temperature", "rainfall", "finish_position"]

MAX_POSITION = 20
MIDFIELD = (MAX_POSITION + 1) / 2
TEST_RACE_FRACTION = 0.2

# "Pretend we have K extra races saying the effect is zero."
SHRINK_GRID = 5
SHRINK_TEAM = 15
SHRINK_DRIVER = 8
SHRINK_PULL = 300


def load_dataset(path: str) -> pd.DataFrame:
    """One row per driver per race. Rows without a classified finish (DNF,
    DSQ) or a grid slot are dropped: this estimates how a finisher ends up."""
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("dataset is missing columns: %s" % ", ".join(missing))
    df = df[REQUIRED].copy()
    df["rainfall"] = df["rainfall"].astype(float) > 0
    df = df.dropna(subset=["finish_position", "grid", "track_temperature"])
    return df.sort_values(["season", "round"]).reset_index(drop=True)


def _shrunk_mean(values: pd.Series, groups: pd.Series, k: float) -> pd.Series:
    g = values.groupby(groups)
    return g.sum() / (g.count() + k)


class Analyst:
    def __init__(self, df: pd.DataFrame):
        # The baseline, team and driver tables come from dry races only; rain
        # is layered on separately. Mixing them would drag every front-row
        # slot toward midfield and spoil the dry-race estimate.
        dry = df[~df["rainfall"]]
        if len(dry) < 50:
            dry = df
        dry_grid = dry["grid"].clip(1, MAX_POSITION)
        stats = dry.groupby(dry_grid)["finish_position"].agg(["mean", "count"])
        slots = pd.Series(stats.index, index=stats.index, dtype=float)
        self.grid_finish = ((stats["count"] * stats["mean"] + SHRINK_GRID * slots)
                            / (stats["count"] + SHRINK_GRID))

        r = dry["finish_position"] - dry_grid.map(self._grid_base)
        self.team = _shrunk_mean(r, dry["constructor_id"], SHRINK_TEAM)
        r = r - dry["constructor_id"].map(self.team)
        self.driver = _shrunk_mean(r, dry["driver_id"], SHRINK_DRIVER)

        grid = df["grid"].clip(1, MAX_POSITION)
        r = (df["finish_position"] - grid.map(self._grid_base)
             - df["constructor_id"].map(self.team).fillna(0)
             - df["driver_id"].map(self.driver).fillna(0))

        last = df.drop_duplicates("driver_id", keep="last")
        self.team_of = dict(zip(last["driver_id"], last["constructor_id"]))

        # Weather pulls the order toward the middle: slope of what is left
        # over against the distance from midfield (0 = no effect, 1 = full
        # shuffle, negative = the order hardens).
        pull = MIDFIELD - grid.map(self._grid_base)
        self.hot_from = float(dry["track_temperature"].median())
        hot = df["track_temperature"] >= self.hot_from
        self.pull = {
            "rain": self._slope(r, pull, df["rainfall"]),
            "hot": self._slope(r, pull, ~df["rainfall"] & hot),
            "cool": self._slope(r, pull, ~df["rainfall"] & ~hot),
        }
        self.n = {"rain": int(df["rainfall"].sum()),
                  "hot": int((~df["rainfall"] & hot).sum()),
                  "cool": int((~df["rainfall"] & ~hot).sum())}
        self.drivers = sorted(df["driver_id"].unique().tolist())
        self.grid_max = int(min(grid.max(), 22))

    def _grid_base(self, g):
        g = int(min(max(g, 1), MAX_POSITION))
        return float(self.grid_finish.get(g, g))

    @staticmethod
    def _slope(resid, pull, mask) -> float:
        x, y = pull[mask], resid[mask]
        return float((x * y).sum() / ((x * x).sum() + SHRINK_PULL))

    def estimate(self, driver_id, grid, track_temperature, rainfall) -> dict:
        base = self._grid_base(grid)
        known = driver_id in self.driver.index
        team = self.team_of.get(driver_id)
        team_fx = float(self.team.get(team, 0.0)) if known else 0.0
        driver_fx = float(self.driver.get(driver_id, 0.0))
        if rainfall:
            condition = "rain"
        else:
            condition = "hot" if track_temperature >= self.hot_from else "cool"
        weather_fx = self.pull[condition] * (MIDFIELD - base)
        raw = float(np.clip(base + team_fx + driver_fx + weather_fx, 1, MAX_POSITION))
        return {
            "raw_position": round(raw, 2),
            "predicted_position": int(round(raw)),
            "known_driver": known,
            "condition": condition,
            "breakdown": {
                "grid_slot": round(base, 2),
                "team": round(team_fx, 2),
                "driver": round(driver_fx, 2),
                "weather": round(weather_fx, 2),
            },
        }

    def estimate_row(self, row) -> float:
        return self.estimate(row.driver_id, row.grid, row.track_temperature,
                             bool(row.rainfall))["raw_position"]


def evaluate(df: pd.DataFrame) -> dict:
    """Fit on the early races, score on the latest ones (never the reverse:
    a random split would put the same race on both sides)."""
    races = df[["season", "round"]].drop_duplicates().reset_index(drop=True)
    if len(races) < 5:
        raise ValueError("need at least 5 races, got %d" % len(races))
    n_test = max(1, int(round(len(races) * TEST_RACE_FRACTION)))
    test_keys = set(map(tuple, races.tail(n_test).to_numpy()))
    mask = np.fromiter(((s, r) in test_keys for s, r in zip(df["season"], df["round"])),
                       dtype=bool, count=len(df))
    train, test = df[~mask], df[mask]

    analyst = Analyst(train)
    actual = test["finish_position"].to_numpy()
    grid = test["grid"].clip(1, MAX_POSITION).to_numpy()
    curve = np.array([analyst._grid_base(g) for g in grid])
    full = np.array([analyst.estimate_row(r) for r in test.itertuples()])
    mae = lambda p: round(float(np.abs(p - actual).mean()), 3)
    err = np.abs(full - actual)
    return {
        "rows": int(len(df)), "races": int(len(races)), "test_races": int(n_test),
        "mae_grid_baseline": mae(grid),
        "mae_grid_curve": mae(curve),
        "mae_full": mae(full),
        "beats_baseline": bool(err.mean() < np.abs(grid - actual).mean()),
        "within_3_positions": round(float((err <= 3).mean()), 3),
        "typical_error": round(float(np.percentile(err, 80)), 2),
    }
