"""Thread-safe inference wrapper around the trained Keras model."""
from __future__ import annotations

import json
import os
import threading

import joblib
import numpy as np

from ..utils.errors import ModelNotTrainedError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = os.path.join(BASE_DIR, "artifacts")

FEATURES = [
    "attendance_pct",
    "study_hours",
    "previous_marks",
    "assignment_completion",
    "class_participation",
    "learning_engagement",
    "subject_performance",
]

_lock = threading.Lock()
_cache: dict = {}


def _load():
    with _lock:
        if _cache:
            return _cache
        model_path = os.path.join(ARTIFACT_DIR, "student_ann.keras")
        scaler_path = os.path.join(ARTIFACT_DIR, "scaler.pkl")
        imputer_path = os.path.join(ARTIFACT_DIR, "imputer.pkl")
        if not all(os.path.exists(path) for path in (model_path, scaler_path, imputer_path)):
            raise ModelNotTrainedError(
                "The student performance model has not been trained yet. "
                "Run `python -m app.deep_learning.train_student_ann` first."
            )
        from tensorflow import keras

        _cache["model"] = keras.models.load_model(model_path, compile=False)
        _cache["scaler"] = joblib.load(scaler_path)
        _cache["imputer"] = joblib.load(imputer_path)
        metrics_path = os.path.join(ARTIFACT_DIR, "metrics.json")
        _cache["metrics"] = (
            json.load(open(metrics_path, encoding="utf-8"))
            if os.path.exists(metrics_path)
            else {}
        )
        return _cache


def reset_cache() -> None:
    """Drop cached model objects (used by tests and after retraining)."""
    with _lock:
        _cache.clear()


def is_ready() -> bool:
    return all(
        os.path.exists(os.path.join(ARTIFACT_DIR, name))
        for name in ("student_ann.keras", "scaler.pkl", "imputer.pkl")
    )


def risk_level(score: float) -> str:
    if score < 50:
        return "high"
    if score < 65:
        return "moderate"
    return "low"


def predict(features: dict) -> dict:
    """Predict an academic score from a mapping of the seven features.

    Missing / null values are imputed with the training median, matching the
    training pipeline exactly.
    """
    bundle = _load()
    row = []
    used = {}
    for name in FEATURES:
        value = features.get(name)
        try:
            numeric = float(value)
            if np.isnan(numeric):
                raise ValueError
        except (TypeError, ValueError):
            numeric = np.nan
        row.append(numeric)
        used[name] = None if np.isnan(numeric) else round(numeric, 2)

    matrix = np.array([row], dtype=float)
    matrix = bundle["imputer"].transform(matrix)
    matrix = bundle["scaler"].transform(matrix)
    prediction = float(bundle["model"].predict(matrix, verbose=0).ravel()[0])
    prediction = max(0.0, min(100.0, prediction))

    return {
        "predicted_score": round(prediction, 2),
        "risk_level": risk_level(prediction),
        "model_version": bundle["metrics"].get("model_version", "student-ann-v1"),
        "features_used": used,
        "note": (
            "Prediction from a model trained on synthetic data. Use it as a "
            "support signal, never as a final academic judgement."
        ),
    }


def metrics() -> dict:
    return _load()["metrics"]
