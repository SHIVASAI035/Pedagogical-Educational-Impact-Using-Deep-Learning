"""Train the student academic-score Artificial Neural Network.

Architecture (as required by the project specification)
-------------------------------------------------------
Input (7) -> Dense 64 ReLU -> Dense 32 ReLU -> Dense 16 ReLU -> Dense 1 linear

Training: Adam, MSE loss, early stopping on validation loss, 70/15/15 split,
median imputation + standard scaling fitted on the training partition only.

Usage
-----
    python -m app.deep_learning.train_student_ann
    python -m app.deep_learning.train_student_ann --epochs 300 --seed 7

Artifacts written to ``app/deep_learning/artifacts``:
    student_ann.keras     trained Keras model
    scaler.pkl            fitted StandardScaler
    imputer.pkl           fitted SimpleImputer (median)
    metrics.json          real evaluation metrics + training history
    feature_order.json    exact feature order used by the model
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(os.path.dirname(BASE_DIR), "dataset")
DEFAULT_CSV = os.path.join(DATASET_DIR, "student_performance.csv")
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
TARGET = "final_score"
MODEL_VERSION = "student-ann-v1"


def _build_model(input_dim: int = 7):
    # Imported lazily so the rest of the API can start even if TensorFlow is
    # unavailable; only training/prediction require it.
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers

    tf.random.set_seed(42)
    model = keras.Sequential(
        [
            keras.Input(shape=(input_dim,), name="student_features"),
            layers.Dense(64, activation="relu", name="hidden_1"),
            layers.Dense(32, activation="relu", name="hidden_2"),
            layers.Dense(16, activation="relu", name="hidden_3"),
            layers.Dense(1, activation="linear", name="academic_score"),
        ],
        name="student_performance_ann",
    )
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001),
                  loss="mse", metrics=["mae"])
    return model


def load_dataset(csv_path: str = DEFAULT_CSV) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        from app.dataset.generate_dataset import write_dataset

        write_dataset()
    frame = pd.read_csv(csv_path)
    missing = [column for column in FEATURES + [TARGET] if column not in frame.columns]
    if missing:
        raise ValueError(f"Dataset is missing required column(s): {missing}")
    return frame


def train(csv_path: str = DEFAULT_CSV, epochs: int = 250, seed: int = 42,
          verbose: int = 2, artifact_dir: str | None = None) -> dict:
    artifact_dir = artifact_dir or ARTIFACT_DIR
    import tensorflow as tf
    from tensorflow import keras

    frame = load_dataset(csv_path)
    X = frame[FEATURES].astype(float).to_numpy()
    y = frame[TARGET].astype(float).to_numpy()

    # 70 / 15 / 15 split. The scaler/imputer only ever see the training rows.
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=seed
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=seed
    )

    imputer = SimpleImputer(strategy="median")
    X_train = imputer.fit_transform(X_train)
    X_val = imputer.transform(X_val)
    X_test = imputer.transform(X_test)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    tf.keras.utils.set_random_seed(seed)
    model = _build_model(X_train.shape[1])

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=20, restore_best_weights=True, min_delta=1e-4
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=8, min_lr=1e-5
        ),
    ]

    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=32,
        verbose=verbose,
        callbacks=callbacks,
    )

    test_predictions = model.predict(X_test, verbose=0).ravel()
    mae = float(mean_absolute_error(y_test, test_predictions))
    mse = float(mean_squared_error(y_test, test_predictions))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_test, test_predictions))

    val_predictions = model.predict(X_val, verbose=0).ravel()
    val_mae = float(mean_absolute_error(y_val, val_predictions))
    val_rmse = float(np.sqrt(mean_squared_error(y_val, val_predictions)))

    os.makedirs(artifact_dir, exist_ok=True)
    model_path = os.path.join(artifact_dir, "student_ann.keras")
    model.save(model_path)
    joblib.dump(scaler, os.path.join(artifact_dir, "scaler.pkl"))
    joblib.dump(imputer, os.path.join(artifact_dir, "imputer.pkl"))

    with open(os.path.join(artifact_dir, "feature_order.json"), "w", encoding="utf-8") as handle:
        json.dump({"features": FEATURES, "target": TARGET, "version": MODEL_VERSION}, handle, indent=2)

    metrics = {
        "model_version": MODEL_VERSION,
        "architecture": "7 -> Dense(64, relu) -> Dense(32, relu) -> Dense(16, relu) -> Dense(1, linear)",
        "optimizer": "Adam(0.001)",
        "loss": "mean_squared_error",
        "dataset": {
            "path": os.path.relpath(csv_path, os.path.dirname(os.path.dirname(BASE_DIR))).replace("\\", "/"),
            "synthetic": True,
            "rows_total": int(len(frame)),
            "rows_train": int(len(X_train)),
            "rows_validation": int(len(X_val)),
            "rows_test": int(len(X_test)),
            "features": FEATURES,
        },
        "training": {
            "epochs_requested": int(epochs),
            "epochs_run": int(len(history.history["loss"])),
            "batch_size": 32,
            "early_stopping_patience": 20,
            "seed": seed,
        },
        "test_metrics": {
            "mae": round(mae, 4),
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
        },
        "validation_metrics": {"mae": round(val_mae, 4), "rmse": round(val_rmse, 4)},
        "history": {
            key: [round(float(value), 5) for value in values]
            for key, values in history.history.items()
        },
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "artifacts": {
            "model": "student_ann.keras",
            "scaler": "scaler.pkl",
            "imputer": "imputer.pkl",
            "feature_order": "feature_order.json",
        },
    }
    with open(os.path.join(artifact_dir, "metrics.json"), "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    print("\nTest metrics (real run, no hard-coded values):")
    print(json.dumps(metrics["test_metrics"], indent=2))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the student performance ANN.")
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--epochs", type=int, default=250)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    train(csv_path=args.csv, epochs=args.epochs, seed=args.seed, verbose=0 if args.quiet else 2)


if __name__ == "__main__":
    main()
