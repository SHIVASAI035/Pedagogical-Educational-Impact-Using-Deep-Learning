"""Analytics for students, teachers and the overall pedagogical impact.

Design notes
------------
* Teacher effectiveness is described through *multiple indicators* (feedback
  dimensions, observation dimensions, methodology mix, outcome context). No
  single "effectiveness score" is produced or ranked.
* The impact module reports associations (Pearson r, ANOVA) and explicitly
  separates correlation from causation.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

import numpy as np
from scipy import stats
from sqlalchemy import func

from ..extensions import db
from ..models import (
    AcademicRecord,
    Assignment,
    AssignmentSubmission,
    Attendance,
    ClassRoom,
    ClassroomObservation,
    LearningActivity,
    Student,
    StudentFeedback,
    Subject,
    TeachingMethod,
)
from .features import (
    attendance_series,
    marks_trend,
    public_features,
    student_features,
    subject_breakdown,
)


# ---------------------------------------------------------------------------
# small statistical helpers
# ---------------------------------------------------------------------------
def _r(value, digits: int = 2):
    if value is None:
        return None
    return round(float(value), digits)


def _summary(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "mean": _r(array.mean()),
        "std": _r(array.std(ddof=1)) if array.size > 1 else 0.0,
        "min": _r(array.min()),
        "max": _r(array.max()),
    }


def _anova(groups: list[list[float]]) -> dict:
    usable = [group for group in groups if len(group) >= 2]
    if len(usable) < 2:
        return {"f": None, "p": None, "note": "Not enough observations per group for ANOVA."}
    f_stat, p_value = stats.f_oneway(*usable)
    return {
        "f": _r(f_stat, 3),
        "p": _r(p_value, 4),
        "note": (
            "p < 0.05 suggests group means differ; it does not show which "
            "methodology caused the difference."
        ),
    }


def _correlation(x: list[float], y: list[float]) -> dict:
    if len(x) < 3 or len(y) < 3:
        return {"r": None, "p": None, "n": len(x), "strength": "insufficient data"}
    r_value, p_value = stats.pearsonr(x, y)
    magnitude = abs(r_value)
    strength = (
        "very weak" if magnitude < 0.2
        else "weak" if magnitude < 0.4
        else "moderate" if magnitude < 0.6
        else "strong"
    )
    return {
        "r": _r(r_value, 3),
        "p": _r(p_value, 4),
        "n": len(x),
        "strength": strength,
        "direction": "positive" if r_value >= 0 else "negative",
    }


def _attendance_pct(student_id: int) -> float:
    rows = Attendance.query.filter_by(student_id=student_id).all()
    if not rows:
        return 0.0
    present = sum(1 for row in rows if row.status in ("present", "late"))
    return round(present / len(rows) * 100, 1)


def _average_score(student_id: int) -> float | None:
    value = (
        db.session.query(func.avg(AcademicRecord.marks_obtained * 100.0 / AcademicRecord.max_marks))
        .filter(AcademicRecord.student_id == student_id)
        .scalar()
    )
    return _r(value) if value is not None else None


def _assignment_stats(student_id: int) -> dict:
    student = db.session.get(Student, student_id)
    if student is None or student.class_id is None:
        return {"total": 0, "submitted": 0, "pending": 0, "completion_pct": 0.0}
    assignments = Assignment.query.filter_by(class_id=student.class_id).all()
    submissions = {
        row.assignment_id: row
        for row in AssignmentSubmission.query.filter_by(student_id=student_id).all()
    }
    total = len(assignments)
    submitted = sum(
        1
        for assignment in assignments
        if assignment.id in submissions
        and submissions[assignment.id].status in ("submitted", "late")
    )
    return {
        "total": total,
        "submitted": submitted,
        "pending": max(0, total - submitted),
        "completion_pct": round(submitted / total * 100, 1) if total else 0.0,
    }


# ---------------------------------------------------------------------------
# Module 1: student performance
# ---------------------------------------------------------------------------
def student_dashboard(student_id: int) -> dict:
    student = db.session.get(Student, student_id)
    if student is None:
        return {}
    features = student_features(student_id)
    breakdown = subject_breakdown(student_id)
    attendance = Attendance.query.filter_by(student_id=student_id).all()
    last_30 = [row for row in attendance if row.date >= date.today() - timedelta(days=30)]
    activities = (
        LearningActivity.query.filter_by(student_id=student_id)
        .order_by(LearningActivity.date.asc())
        .limit(20)
        .all()
    )

    from ..models import Prediction

    latest_prediction = (
        Prediction.query.filter_by(student_id=student_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    return {
        "student": student.to_dict(),
        "features": public_features(features),
        "data_quality": {
            "completeness": features.get("_completeness"),
            "confidence": features.get("_confidence"),
            "evidence": features.get("_evidence"),
        },
        "attendance": {
            "overall_pct": _r(features.get("attendance_pct")),
            "last_30_days_pct": (
                round(
                    sum(1 for row in last_30 if row.status != "absent") / len(last_30) * 100, 1
                )
                if last_30
                else None
            ),
            "records": len(attendance),
            "present": sum(1 for row in attendance if row.status == "present"),
            "late": sum(1 for row in attendance if row.status == "late"),
            "absent": sum(1 for row in attendance if row.status == "absent"),
            "monthly": attendance_series(student_id),
        },
        "academics": {
            "average_pct": _r(features.get("subject_performance")),
            "latest_exam_average": _r(features.get("previous_marks")),
            "subjects": breakdown,
            "trend": marks_trend(student_id),
            "strongest_subject": breakdown[0] if breakdown else None,
            "weakest_subject": breakdown[-1] if breakdown else None,
        },
        "assignments": _assignment_stats(student_id),
        "learning": {
            "study_hours_per_day": features.get("study_hours"),
            "participation_pct": features.get("class_participation"),
            "engagement_pct": features.get("learning_engagement"),
            "recent_activity": [
                {
                    "date": row.date.isoformat(),
                    "study_hours": row.study_hours,
                    "engagement": round(row.engagement_score * 10, 1),
                    "participation": round(row.participation_score * 10, 1),
                }
                for row in activities
            ],
        },
        "prediction": latest_prediction.to_dict() if latest_prediction else None,
    }


# ---------------------------------------------------------------------------
# Module 2: teacher effectiveness
# ---------------------------------------------------------------------------
def _feedback_aggregate(feedback_rows: list[StudentFeedback]) -> dict:
    dimensions = [
        "clarity_rating",
        "interaction_rating",
        "methodology_rating",
        "practical_rating",
        "difficulty_rating",
        "overall_rating",
    ]
    averages = {
        dimension: _r(np.mean([getattr(row, dimension) for row in feedback_rows]))
        if feedback_rows
        else None
        for dimension in dimensions
    }
    sentiments = Counter(row.sentiment_label or "neutral" for row in feedback_rows)
    total = len(feedback_rows) or 1
    keywords = Counter()
    for row in feedback_rows:
        from ..nlp.feedback_analyzer import analyze_text

        for keyword in analyze_text(row.comments or "")["keywords"]:
            keywords[keyword] += 1

    return {
        "count": len(feedback_rows),
        "averages": averages,
        "sentiment": {
            "positive": sentiments.get("positive", 0),
            "neutral": sentiments.get("neutral", 0),
            "negative": sentiments.get("negative", 0),
            "positive_pct": round(sentiments.get("positive", 0) / total * 100, 1),
            "neutral_pct": round(sentiments.get("neutral", 0) / total * 100, 1),
            "negative_pct": round(sentiments.get("negative", 0) / total * 100, 1),
        },
        "top_keywords": [{"word": word, "count": count} for word, count in keywords.most_common(10)],
    }


def _observation_summary(observations: list[ClassroomObservation]) -> dict:
    dimensions = [
        "interaction_score",
        "clarity_score",
        "engagement_score",
        "practical_examples_score",
        "material_usage_score",
    ]
    return {
        "count": len(observations),
        "averages": {
            dimension: _r(np.mean([getattr(row, dimension) for row in observations]))
            if observations
            else None
            for dimension in dimensions
        },
        "by_methodology": {
            methodology: _summary([row.engagement_score for row in observations if row.methodology == methodology])
            for methodology in sorted({row.methodology for row in observations})
        },
    }


def teacher_dashboard(teacher_id: int) -> dict:
    from ..models import Teacher

    teacher = db.session.get(Teacher, teacher_id)
    if teacher is None:
        return {}

    subjects = Subject.query.filter_by(teacher_id=teacher_id).all()
    class_ids = sorted({subject.class_id for subject in subjects})
    students = Student.query.filter(Student.class_id.in_(class_ids)).all() if class_ids else []
    feedback = StudentFeedback.query.filter_by(teacher_id=teacher_id).all()
    observations = ClassroomObservation.query.filter_by(teacher_id=teacher_id).all()
    methods = TeachingMethod.query.filter_by(teacher_id=teacher_id).all()

    subject_performance = []
    for subject in subjects:
        average = (
            db.session.query(func.avg(AcademicRecord.marks_obtained * 100.0 / AcademicRecord.max_marks))
            .filter(AcademicRecord.subject_id == subject.id)
            .scalar()
        )
        subject_performance.append(
            {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "class_name": subject.classroom.name if subject.classroom else None,
                "students": len(subject.classroom.students) if subject.classroom else 0,
                "average_pct": _r(average),
            }
        )

    methodology_mix = Counter(method.methodology for method in methods)
    feedback_summary = _feedback_aggregate(feedback)
    observation_summary = _observation_summary(observations)

    indicators = _teacher_indicators(feedback_summary, observation_summary, len(students))
    sufficiency = {
        "students": len(students),
        "feedback_observations": len(feedback),
        "classroom_observations": len(observations),
        "teaching_sessions_logged": len(methods),
        "adequate": len(feedback) >= 5 and len(observations) >= 3,
        "note": (
            "Indicators are contextual. Fewer than 5 feedback responses or 3 "
            "observations are too few to interpret as a stable pattern."
        ),
    }

    # Anonymised recent comments: no student identifiers leave the backend.
    recent_comments = [
        {
            "comment": row.comments,
            "sentiment": row.sentiment_label,
            "date": row.created_at.date().isoformat() if row.created_at else None,
        }
        for row in sorted(feedback, key=lambda item: item.created_at or date.min, reverse=True)
        if row.comments
    ][:8]

    return {
        "teacher": teacher.to_dict(),
        "subjects": [subject.to_dict() for subject in subjects],
        "students": {
            "count": len(students),
            "classes": len(class_ids),
            "average_attendance": _r(
                np.mean([_attendance_pct(student.id) for student in students])
            )
            if students
            else None,
        },
        "subject_performance": subject_performance,
        "feedback": feedback_summary,
        "observations": observation_summary,
        "methodology_mix": [
            {"methodology": name, "sessions": count}
            for name, count in methodology_mix.most_common()
        ],
        "indicators": indicators,
        "data_sufficiency": sufficiency,
        "recent_comments": recent_comments,
        "caveats": [
            "Student ratings are perceptions, not direct measures of learning.",
            "Classroom observations describe sampled lessons, not every lesson.",
            "Differences between teachers may reflect class composition, subject difficulty or workload.",
            "No composite teacher score is calculated; interpret indicators together.",
        ],
    }


def _teacher_indicators(feedback: dict, observations: dict, student_count: int) -> list[dict]:
    averages = feedback.get("averages", {})
    observation_averages = observations.get("averages", {})

    def indicator(name, value, benchmark, interpretation, source, count):
        return {
            "indicator": name,
            "value": value,
            "benchmark": benchmark,
            "interpretation": interpretation,
            "source": source,
            "observations": count,
        }

    return [
        indicator(
            "Explanation clarity", averages.get("clarity_rating"), 3.5,
            "Below benchmark: consider worked examples, slower pacing and checking understanding.",
            "student feedback (1-5)", feedback.get("count", 0),
        ),
        indicator(
            "Classroom interaction", averages.get("interaction_rating"), 3.5,
            "Below benchmark: add questioning, think-pair-share or discussion segments.",
            "student feedback (1-5)", feedback.get("count", 0),
        ),
        indicator(
            "Practical examples", averages.get("practical_rating"), 3.5,
            "Below benchmark: connect concepts to real problems and demonstrations.",
            "student feedback (1-5)", feedback.get("count", 0),
        ),
        indicator(
            "Observed engagement", observation_averages.get("engagement_score"), 6.0,
            "Below benchmark: review activity design and student participation patterns.",
            "classroom observation (0-10)", observations.get("count", 0),
        ),
        indicator(
            "Observed clarity", observation_averages.get("clarity_score"), 6.0,
            "Below benchmark: structure explanations and summarise key points.",
            "classroom observation (0-10)", observations.get("count", 0),
        ),
        indicator(
            "Teaching material usage", observation_averages.get("material_usage_score"), 6.0,
            "Below benchmark: prepare slides, worksheets or reference material.",
            "classroom observation (0-10)", observations.get("count", 0),
        ),
        indicator(
            "Negative feedback share (%)", feedback.get("sentiment", {}).get("negative_pct"), 25.0,
            "Above benchmark means more negative comments than typical; read comments for context.",
            "NLP sentiment", feedback.get("count", 0),
        ),
    ]


# ---------------------------------------------------------------------------
# Module 3: pedagogical and educational impact
# ---------------------------------------------------------------------------
def _subject_methodology() -> dict[int, str]:
    """Dominant logged methodology per subject."""
    rows = TeachingMethod.query.all()
    counter: dict[int, Counter] = defaultdict(Counter)
    for row in rows:
        if row.subject_id is not None:
            counter[row.subject_id][row.methodology] += 1
    return {
        subject_id: counts.most_common(1)[0][0]
        for subject_id, counts in counter.items()
        if counts
    }


def methodology_comparison() -> dict:
    dominant = _subject_methodology()
    subject_scores: dict[int, list[float]] = defaultdict(list)
    for subject_id, percentage in (
        db.session.query(
            AcademicRecord.subject_id,
            AcademicRecord.marks_obtained * 100.0 / AcademicRecord.max_marks,
        ).all()
    ):
        subject_scores[subject_id].append(float(percentage))

    groups: dict[str, list[float]] = defaultdict(list)
    for subject_id, scores in subject_scores.items():
        methodology = dominant.get(subject_id)
        if methodology is None:
            continue
        groups[methodology].extend(scores)

    observations = ClassroomObservation.query.all()
    engagement: dict[str, list[float]] = defaultdict(list)
    for observation in observations:
        engagement[observation.methodology].append(observation.engagement_score)

    feedback_by_teacher_method: dict[str, list[float]] = defaultdict(list)
    teacher_methodology: dict[int, str] = {}
    for teacher_id, methodology in (
        db.session.query(TeachingMethod.teacher_id, TeachingMethod.methodology)
        .distinct()
        .all()
    ):
        teacher_methodology.setdefault(teacher_id, methodology)
    for feedback in StudentFeedback.query.all():
        methodology = teacher_methodology.get(feedback.teacher_id)
        if methodology:
            feedback_by_teacher_method[methodology].append(feedback.overall_rating)

    rows = []
    for methodology in sorted(set(groups) | set(engagement)):
        score_stats = _summary(groups.get(methodology, []))
        engagement_stats = _summary(engagement.get(methodology, []))
        rating_stats = _summary(feedback_by_teacher_method.get(methodology, []))
        rows.append(
            {
                "methodology": methodology,
                "students_assessed": score_stats["n"],
                "average_score": score_stats["mean"],
                "score_std": score_stats["std"],
                "average_engagement": engagement_stats["mean"],
                "engagement_observations": engagement_stats["n"],
                "average_feedback_rating": rating_stats["mean"],
                "feedback_responses": rating_stats["n"],
            }
        )

    anova = _anova([groups[name] for name in groups])
    return {
        "methodologies": rows,
        "anova": anova,
        "note": (
            "Scores are grouped by the dominant methodology logged for each "
            "subject. Class composition, teacher and subject difficulty are not "
            "controlled, so differences are associations, not causal effects."
        ),
    }


def engagement_analysis() -> dict:
    observations = ClassroomObservation.query.all()
    by_methodology: dict[str, list[float]] = defaultdict(list)
    for observation in observations:
        by_methodology[observation.methodology].append(observation.engagement_score)

    participation_rows = LearningActivity.query.all()
    participation_by_class: dict[int, list[float]] = defaultdict(list)
    for row in participation_rows:
        student = db.session.get(Student, row.student_id)
        if student and student.class_id:
            participation_by_class[student.class_id].append(row.participation_score * 10)

    class_names = {
        classroom.id: f"{classroom.name} - {classroom.section}"
        for classroom in ClassRoom.query.all()
    }

    return {
        "engagement_by_methodology": [
            {
                "methodology": methodology,
                "observations": _summary(values)["n"],
                "average_engagement": _summary(values)["mean"],
                "std": _summary(values)["std"],
            }
            for methodology, values in sorted(by_methodology.items())
        ],
        "participation_by_class": [
            {
                "class_id": class_id,
                "class_name": class_names.get(class_id, f"Class {class_id}"),
                "average_participation": _summary(values)["mean"],
                "records": _summary(values)["n"],
            }
            for class_id, values in sorted(participation_by_class.items())
        ],
        "anova": _anova(list(by_methodology.values())),
    }


def learning_patterns() -> dict:
    students = Student.query.all()
    rows = []
    for student in students:
        features = student_features(student.id)
        score = _average_score(student.id)
        if score is None or features.get("_completeness", 0) < 0.5:
            continue
        rows.append(
            {
                "student_id": student.id,
                "attendance": features["attendance_pct"],
                "study_hours": features["study_hours"],
                "engagement": features["learning_engagement"],
                "assignment_completion": features["assignment_completion"],
                "score": score,
            }
        )

    if len(rows) < 12:
        return {
            "available": False,
            "reason": "At least 12 students with marks and activity data are required.",
            "students_analysed": len(rows),
        }

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    matrix = np.array(
        [
            [
                row["attendance"],
                row["study_hours"] * 10,
                row["engagement"],
                row["assignment_completion"],
                row["score"],
            ]
            for row in rows
        ],
        dtype=float,
    )
    scaled = StandardScaler().fit_transform(matrix)
    k = 3
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(scaled)

    cluster_scores = {
        cluster: float(np.mean([rows[index]["score"] for index in range(len(rows)) if labels[index] == cluster]))
        for cluster in range(k)
    }
    ordered = sorted(cluster_scores, key=cluster_scores.get, reverse=True)
    names = {
        ordered[0]: "Consistent, highly engaged learners",
        ordered[1]: "Steady learners with room to grow",
        ordered[2]: "Learners needing structured support",
    }

    clusters = []
    for cluster in ordered:
        members = [rows[index] for index in range(len(rows)) if labels[index] == cluster]
        clusters.append(
            {
                "cluster": cluster,
                "label": names[cluster],
                "students": len(members),
                "average_score": _r(np.mean([member["score"] for member in members])),
                "average_attendance": _r(np.mean([member["attendance"] for member in members])),
                "average_study_hours": _r(np.mean([member["study_hours"] for member in members])),
                "average_engagement": _r(np.mean([member["engagement"] for member in members])),
                "average_assignment_completion": _r(
                    np.mean([member["assignment_completion"] for member in members])
                ),
            }
        )

    return {
        "available": True,
        "method": "KMeans (k=3) on standardised engagement, attendance, study, assignment and score features",
        "students_analysed": len(rows),
        "clusters": clusters,
        "note": "Clusters describe co-occurring patterns; they do not identify causes.",
    }


def impact_analysis() -> dict:
    students = Student.query.all()
    features_rows = []
    for student in students:
        features = student_features(student.id)
        score = _average_score(student.id)
        if score is None or features.get("_completeness", 0) < 0.5:
            continue
        features_rows.append((features, score))

    dimensions = [
        ("attendance_pct", "Attendance (%)"),
        ("study_hours", "Daily study hours"),
        ("class_participation", "Class participation (%)"),
        ("learning_engagement", "Learning engagement (%)"),
        ("assignment_completion", "Assignment completion (%)"),
        ("previous_marks", "Previous examination marks (%)"),
    ]
    correlations = []
    for key, label in dimensions:
        x = [row[0][key] for row in features_rows]
        y = [row[1] for row in features_rows]
        result = _correlation(x, y)
        correlations.append({"feature": key, "label": label, **result})

    comparison = methodology_comparison()
    engagement = engagement_analysis()

    insights = []
    for item in correlations:
        if item["r"] is not None and item["p"] is not None and item["p"] < 0.05:
            insights.append(
                f"{item['label']} shows a {item['strength']} {item['direction']} association "
                f"with average academic score (r = {item['r']}, p = {item['p']}, n = {item['n']})."
            )

    if comparison["methodologies"]:
        ranked = [row for row in comparison["methodologies"] if row["average_score"] is not None]
        if len(ranked) >= 2:
            best = max(ranked, key=lambda row: row["average_score"])
            lowest = min(ranked, key=lambda row: row["average_score"])
            insights.append(
                f"Students in subjects where '{best['methodology']}' is the dominant logged "
                f"methodology average {best['average_score']}%, compared with "
                f"{lowest['average_score']}% for '{lowest['methodology']}'. "
                "This is an association; teaching assignment and class composition are not controlled."
            )

    return {
        "students_analysed": len(features_rows),
        "correlations": correlations,
        "methodology_comparison": comparison,
        "engagement": engagement,
        "learning_patterns": learning_patterns(),
        "insights": insights,
        "causality_statement": (
            "All relationships shown here are observational associations. The data "
            "were not collected through a randomised or controlled design, so no "
            "teaching method can be said to cause a change in academic performance."
        ),
        "limitations": [
            "Synthetic cohort data are used for the demonstration dataset and seeded records.",
            "Self-reported study hours and engagement are subject to reporting bias.",
            "Class composition, prior attainment and subject difficulty are not controlled.",
            "Feedback sentiment is lexicon-based and misses sarcasm and code-mixing.",
        ],
    }


# ---------------------------------------------------------------------------
# Admin overview
# ---------------------------------------------------------------------------
def admin_overview() -> dict:
    from ..models import Prediction, Teacher, User

    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_classes = ClassRoom.query.count()
    total_subjects = Subject.query.count()

    score_rows = (
        db.session.query(AcademicRecord.student_id,
                         func.avg(AcademicRecord.marks_obtained * 100.0 / AcademicRecord.max_marks))
        .group_by(AcademicRecord.student_id)
        .all()
    )
    scores = [float(value) for _, value in score_rows if value is not None]
    attendance_rows = Attendance.query.all()
    attendance_pct = (
        round(
            sum(1 for row in attendance_rows if row.status != "absent")
            / len(attendance_rows)
            * 100,
            1,
        )
        if attendance_rows
        else None
    )

    activities = LearningActivity.query.all()
    engagement = (
        _r(np.mean([row.engagement_score * 10 for row in activities])) if activities else None
    )
    participation = (
        _r(np.mean([row.participation_score * 10 for row in activities])) if activities else None
    )

    risk_counts = Counter(
        prediction.risk_level
        for prediction in Prediction.query.order_by(Prediction.created_at.desc()).limit(500).all()
    )
    sentiment = Counter(
        feedback.sentiment_label for feedback in StudentFeedback.query.all()
    )
    methodology = Counter(method.methodology for method in TeachingMethod.query.all())

    return {
        "totals": {
            "students": total_students,
            "teachers": total_teachers,
            "classes": total_classes,
            "subjects": total_subjects,
            "users": User.query.count(),
        },
        "academics": {
            "average_score": _summary(scores)["mean"],
            "score_distribution": _score_distribution(scores),
        },
        "attendance": {"average_pct": attendance_pct, "records": len(attendance_rows)},
        "engagement": {"average_pct": engagement, "participation_pct": participation},
        "predictions": {
            "low": risk_counts.get("low", 0),
            "moderate": risk_counts.get("moderate", 0),
            "high": risk_counts.get("high", 0),
        },
        "feedback": {
            "total": sum(sentiment.values()),
            "positive": sentiment.get("positive", 0),
            "neutral": sentiment.get("neutral", 0),
            "negative": sentiment.get("negative", 0),
        },
        "methodologies": [
            {"methodology": name, "sessions": count}
            for name, count in methodology.most_common()
        ],
        "methodology_comparison": methodology_comparison()["methodologies"],
    }


def _score_distribution(scores: list[float]) -> list[dict]:
    bands = [(0, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 101)]
    labels = ["<40", "40-49", "50-59", "60-69", "70-79", "80-89", "90+"]
    result = []
    for (low, high), label in zip(bands, labels):
        result.append(
            {"band": label, "students": sum(1 for score in scores if low <= score < high)}
        )
    return result
