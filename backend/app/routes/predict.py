import os
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from analysis import estimator

router = APIRouter()

DATA_PATH = os.getenv(
    "RACE_DATASET",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "analysis", "data", "race_dataset.csv"),
)


@lru_cache(maxsize=1)
def _load():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("race dataset not found: analysis/data/race_dataset.csv")
    df = estimator.load_dataset(DATA_PATH)
    return estimator.Analyst(df), estimator.evaluate(df)


def _loaded_or_503():
    try:
        return _load()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc))


class PredictRequest(BaseModel):
    driver_id: str
    grid: int = Field(ge=1, le=22, description="Starting grid slot")
    track_temperature: float = Field(ge=-10, le=80)
    rainfall: bool = False


@router.get("/options")
def options():
    """Drivers the analysis knows, and how well it did on races it had not seen."""
    analyst, metrics = _loaded_or_503()
    return {"drivers": analyst.drivers, "grid_max": analyst.grid_max, "metrics": metrics}


@router.post("")
def predict(req: PredictRequest):
    analyst, metrics = _loaded_or_503()
    if req.driver_id not in analyst.drivers:
        raise HTTPException(status_code=422, detail="unknown driver_id: %s" % req.driver_id)
    out = analyst.estimate(req.driver_id, req.grid, req.track_temperature, req.rainfall)
    band = metrics["typical_error"]
    raw = out["raw_position"]
    out["typical_error"] = band
    out["likely_range"] = [max(1, int(round(raw - band))),
                           min(estimator.MAX_POSITION, int(round(raw + band)))]
    return out
