"""Generate the documented SYNTHETIC student-performance dataset.

Why synthetic?
--------------
The project needs seven specific behavioural features (attendance, study hours,
previous marks, assignment completion, participation, engagement and
subject-wise performance) *together with* a final score. Public datasets such as
UCI "Student Performance" (Cortez & Silva, 2008) contain only a subset of these
and do not include assignment completion, participation or engagement
observations, so deriving them would amount to fabricating data. Instead this
module generates a fully documented synthetic cohort whose data-generating
process (DGP) is explicit, reproducible (seed = 42) and reported in
``docs/DATASET.md``.

The dataset is synthetic and must not be presented as real student data.

DGP (all scores 0-100 unless stated)
------------------------------------
attendance_pct        ~ Normal(84, 9)          clipped [45, 100]
study_hours           ~ Normal(3.2, 1.25)      clipped [0.5, 9]  (hours/day)
previous_marks        ~ Normal(67, 12)         clipped [25, 98]
assignment_completion ~ Normal(79, 13)         clipped [25, 100]
class_participation   ~ Normal(68, 14)         clipped [15, 100]
learning_engagement   ~ 0.55*participation + 0.35*attendance + noise
subject_performance   ~ 0.60*previous_marks + 0.25*engagement + noise

final_score =
      0.22*previous_marks + 0.16*subject_performance + 0.18*attendance_pct
    + 0.10*(study_hours/9*100) + 0.14*assignment_completion
    + 0.08*class_participation + 0.12*learning_engagement
    + 6.0*(engagement/100)*(attendance/100)        # small interaction term
    - 8.0*max(0, 65-attendance)/65                 # attendance penalty
    + N(0, 4.2)                                    # irreducible noise
clipped to [0, 100]

Usage
-----
    python -m app.dataset.generate_dataset            # writes CSV + metadata
    python -m app.dataset.generate_dataset --rows 6000
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "student_performance.csv")
META_PATH = os.path.join(BASE_DIR, "student_performance.meta.json")

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


def generate(rows: int = 4000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    attendance = np.clip(rng.normal(84, 9, rows), 45, 100)
    study_hours = np.clip(rng.normal(3.2, 1.25, rows), 0.5, 9.0)
    previous = np.clip(rng.normal(67, 12, rows), 25, 98)
    assignment = np.clip(rng.normal(79, 13, rows), 25, 100)
    participation = np.clip(rng.normal(68, 14, rows), 15, 100)

    engagement = np.clip(
        0.55 * participation + 0.35 * attendance - 18 + rng.normal(0, 6, rows),
        5,
        100,
    )
    subject_perf = np.clip(
        0.60 * previous + 0.25 * engagement + 10 + rng.normal(0, 6, rows),
        10,
        100,
    )

    latent = (
        0.22 * previous
        + 0.16 * subject_perf
        + 0.18 * attendance
        + 0.10 * (study_hours / 9.0 * 100)
        + 0.14 * assignment
        + 0.08 * participation
        + 0.12 * engagement
        + 6.0 * (engagement / 100.0) * (attendance / 100.0)
        - 8.0 * np.maximum(0, 65 - attendance) / 65.0
        + rng.normal(0, 4.2, rows)
    )
    final = np.clip(latent, 0, 100)

    frame = pd.DataFrame(
        {
            "attendance_pct": np.round(attendance, 1),
            "study_hours": np.round(study_hours, 1),
            "previous_marks": np.round(previous, 1),
            "assignment_completion": np.round(assignment, 1),
            "class_participation": np.round(participation, 1),
            "learning_engagement": np.round(engagement, 1),
            "subject_performance": np.round(subject_perf, 1),
            "final_score": np.round(final, 1),
        }
    )

    # Simulate realistic missingness (~1.5% per feature) so the preprocessing
    # step (median imputation) is exercised by real missing values.
    for column in FEATURES:
        mask = rng.random(rows) < 0.015
        frame.loc[mask, column] = np.nan
    return frame


def write_dataset(rows: int = 4000, seed: int = 42) -> dict:
    frame = generate(rows=rows, seed=seed)
    frame.to_csv(CSV_PATH, index=False)
    meta = {
        "name": "Synthetic Student Performance Dataset",
        "synthetic": True,
        "seed": seed,
        "rows": int(len(frame)),
        "features": FEATURES,
        "target": TARGET,
        "missing_value_rate": round(float(frame[FEATURES].isna().mean().mean()), 4),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generator": "app/dataset/generate_dataset.py",
        "documentation": "docs/DATASET.md",
        "note": (
            "Synthetic data generated from the documented process in this file. "
            "It is not collected from real students and must not be presented as such."
        ),
    }
    with open(META_PATH, "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2)
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic dataset.")
    parser.add_argument("--rows", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    meta = write_dataset(rows=args.rows, seed=args.seed)
    print(f"Wrote {meta['rows']} rows to {CSV_PATH}")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
