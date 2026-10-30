from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml import model

router = APIRouter()


@lru_cache(maxsize=1)
def _load():
    return model.load()


class PredictRequest(BaseModel):
    driver_id: str
    constructor_id: str
    circuit_id: str
    grid: int = Field(ge=1, le=22, description="Starting grid slot")
    air_temperature: float = Field(ge=-10, le=60)
    track_temperature: float = Field(ge=-10, le=80)
    rainfall: bool = False


def _loaded_or_503():
    try:
        return _load()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/options")
def options():
    """Drivers, teams and circuits the model was trained on, and its accuracy."""
    _, metrics = _loaded_or_503()
    keep = ("rows", "races", "test_races", "mae_model", "mae_grid_baseline",
            "beats_baseline", "within_3_positions", "typical_error")
    return {**metrics["options"], "metrics": {k: metrics[k] for k in keep}}


@router.post("")
def predict(req: PredictRequest):
    pipe, metrics = _loaded_or_503()
    known = metrics["options"]
    for field, key in (("driver_id", "drivers"), ("constructor_id", "constructors"),
                       ("circuit_id", "circuits")):
        if getattr(req, field) not in known[key]:
            raise HTTPException(status_code=422,
                                detail="unknown %s: %s" % (field, getattr(req, field)))
    return model.predict(pipe, metrics, **req.model_dump())
