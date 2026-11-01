"""Seed the database with a clearly-labelled synthetic demonstration cohort.

Everything created here is synthetic. A modest association between teaching
methodology and outcomes is deliberately built into the generator so that the
analytics screens are meaningful; it is NOT evidence about real teaching.

Usage (from the ``backend`` directory):
    python -m app.seed_data --reset
    python -m app.seed_data --reset --skip-train
"""
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta

import numpy as np

from . import create_app
from .extensions import db
from .models import (
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
    Teacher,
    TeachingMethod,
    User,
)
from .nlp.feedback_analyzer import analyze_feedback

SEED = 2026
DEMO_PASSWORD_STAFF = "Teacher@12345"
DEMO_PASSWORD_STUDENT = "Student@12345"
DEMO_PASSWORD_ADMIN = "Admin@12345"

METHODOLOGIES = [
    "Lecture",
    "Demonstration",
    "Collaborative Learning",
    "Flipped Classroom",
    "Project Based Learning",
    "Discussion",
]
# Modest synthetic association used only to make demo charts non-empty.
METHOD_EFFECT = {
    "Lecture": 0.0,
    "Demonstration": 1.8,
    "Collaborative Learning": 2.6,
    "Flipped Classroom": 2.1,
    "Project Based Learning": 3.0,
    "Discussion": 2.2,
}

COMMENTS = {
    "positive": [
        "The teacher explains concepts clearly and uses practical examples from real life.",
        "Very interactive sessions, and doubts are answered patiently. The group activities help me understand.",
        "The practical demonstrations made the topic easy to understand. The notes are also useful.",
        "I enjoyed the collaborative activity and the teacher gave helpful feedback on our project.",
        "Clear explanations, good pace and useful slides. The class discussion kept me engaged.",
        "The teacher is supportive and encourages questions. I improved a lot this term.",
    ],
    "neutral": [
        "The class is okay. Some topics are explained well, others move quickly.",
        "The teaching is fine overall, but I would like more examples during revision.",
        "Lectures are organised. I sometimes find the pace difficult in the last period.",
        "The material is covered on time. More practice problems would help.",
        "It is a normal class. The notes are useful but the activities are limited.",
    ],
    "negative": [
        "The explanations are confusing and the pace is too fast for me to follow.",
        "Classes are mostly lectures and it is difficult to stay engaged for the full period.",
        "I did not understand the topic and there were not enough practical examples.",
        "The teacher moves quickly and does not check whether students understand.",
        "There are too few materials and the revision session was rushed and disorganised.",
        "Group work is not well organised and feedback on assignments arrives late.",
    ],
}


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return float(max(low, min(high, value)))


def reset_database() -> None:
    db.drop_all()
    db.create_all()


def seed(reset: bool = True, train_model: bool = True) -> dict:
    rng = np.random.default_rng(SEED)
    random.seed(SEED)

    if reset:
        reset_database()

    if User.query.filter_by(email="admin@school.edu").first():
        raise SystemExit("Demo data already exists. Re-run with --reset to rebuild it.")

    # ---------------------------------------------------------------- admin
    admin = User(full_name="Dr. Meera Sharma", email="admin@school.edu", role="admin")
    admin.set_password(DEMO_PASSWORD_ADMIN)
    db.session.add(admin)

    # -------------------------------------------------------------- teachers
    teacher_specs = [
        ("Mr. Arjun Rao", "teacher1@school.edu", "T001", "Science", "Physics"),
        ("Ms. Priya Nair", "teacher2@school.edu", "T002", "Mathematics", "Algebra"),
        ("Mr. Rohan Verma", "teacher3@school.edu", "T003", "Languages", "English"),
        ("Ms. Kavya Iyer", "teacher4@school.edu", "T004", "Science", "Chemistry"),
        ("Mr. Sameer Khan", "teacher5@school.edu", "T005", "Social Science", "History"),
        ("Ms. Ananya Bose", "teacher6@school.edu", "T006", "Computer Science", "Programming"),
    ]
    teachers: list[Teacher] = []
    for index, (name, email, code, department, specialization) in enumerate(teacher_specs):
        user = User(full_name=name, email=email, role="teacher")
        user.set_password(DEMO_PASSWORD_STAFF)
        db.session.add(user)
        db.session.flush()
        teacher = Teacher(
            user_id=user.id,
            employee_code=code,
            department=department,
            specialization=specialization,
        )
        teacher.quality = float(rng.normal(0, 0.8))  # transient attribute for the generator
        db.session.add(teacher)
        teachers.append(teacher)
    db.session.flush()

    # --------------------------------------------------------------- classes
    class_specs = [
        ("Grade 9", "A", "2025-2026", teachers[0]),
        ("Grade 9", "B", "2025-2026", teachers[1]),
        ("Grade 10", "A", "2025-2026", teachers[2]),
    ]
    classes: list[ClassRoom] = []
    for name, section, year, class_teacher in class_specs:
        classroom = ClassRoom(
            name=name,
            section=section,
            academic_year=year,
            class_teacher_id=class_teacher.id,
        )
        db.session.add(classroom)
        classes.append(classroom)
    db.session.flush()

    # -------------------------------------------------------------- subjects
    subject_names = [
        ("Mathematics", "MATH"),
        ("Science", "SCI"),
        ("English", "ENG"),
        ("Social Science", "SOC"),
        ("Computer Science", "CS"),
    ]
    subjects: list[Subject] = []
    subject_method: dict[int, str] = {}
    for classroom in classes:
        for offset, (name, code) in enumerate(subject_names):
            teacher = teachers[(offset + classes.index(classroom)) % len(teachers)]
            subject = Subject(
                name=name,
                code=f"{code}-{classroom.name.replace(' ', '')}{classroom.section}",
                class_id=classroom.id,
                teacher_id=teacher.id,
            )
            db.session.add(subject)
            subjects.append(subject)
            subject_method[id(subject)] = METHODOLOGIES[
                (offset + classes.index(classroom)) % len(METHODOLOGIES)
            ]
    db.session.flush()
    for subject in subjects:
        subject.dominant_method = subject_method[id(subject)]  # transient

    # -------------------------------------------------------------- students
    students: list[Student] = []
    roll = 1001
    for classroom in classes:
        for _ in range(18):
            user = User(
                full_name=f"Student {roll}",
                email=f"student{roll}@school.edu",
                role="student",
            )
            user.set_password(DEMO_PASSWORD_STUDENT)
            db.session.add(user)
            db.session.flush()
            student = Student(
                user_id=user.id,
                roll_number=f"S{roll}",
                class_id=classroom.id,
                guardian_name=f"Guardian {roll}",
            )
            # Latent profile used by the generator (not stored).
            student.ability = float(np.clip(rng.normal(64, 13), 25, 95))
            student.attendance_propensity = float(np.clip(rng.normal(0.86, 0.09), 0.5, 1.0))
            student.engagement = float(np.clip(rng.normal(65, 14), 15, 100))
            student.study_hours = float(np.clip(rng.normal(3.1, 1.1), 0.4, 8))
            student.participation = float(np.clip(rng.normal(64, 15), 10, 100))
            student.completion_propensity = float(np.clip(rng.normal(0.80, 0.13), 0.3, 1.0))
            db.session.add(student)
            students.append(student)
            roll += 1
    db.session.flush()

    today = date.today()

    # ------------------------------------------------------------- teaching
    for subject in subjects:
        teacher = subject.teacher
        dominant = subject.dominant_method
        for session_index in range(6):
            methodology = (
                dominant
                if session_index < 4
                else random.choice([m for m in METHODOLOGIES if m != dominant])
            )
            db.session.add(
                TeachingMethod(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    methodology=methodology,
                    description=f"{methodology} session on {subject.name}",
                    date_used=today - timedelta(days=random.randint(10, 120)),
                    duration_minutes=random.choice([40, 45, 50]),
                )
            )

    for teacher in teachers:
        teacher_subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
        for observation_index in range(6):
            subject = random.choice(teacher_subjects)
            methodology = subject.dominant_method
            base = 6.2 + 0.7 * teacher.quality + 0.35 * METHOD_EFFECT[methodology]
            db.session.add(
                ClassroomObservation(
                    teacher_id=teacher.id,
                    class_id=subject.class_id,
                    subject_id=subject.id,
                    methodology=methodology,
                    observation_date=today - timedelta(days=random.randint(5, 100)),
                    interaction_score=round(_clamp(base + rng.normal(0, 1.1), 0, 10), 1),
                    clarity_score=round(_clamp(base + rng.normal(0, 0.9), 0, 10), 1),
                    engagement_score=round(_clamp(base + rng.normal(0, 1.0), 0, 10), 1),
                    practical_examples_score=round(_clamp(base + rng.normal(0, 1.2), 0, 10), 1),
                    material_usage_score=round(_clamp(base + rng.normal(0, 1.3), 0, 10), 1),
                    observer_notes="Structured observation by the academic coordinator.",
                    observer_id=admin.id,
                )
            )

    # ----------------------------------------------------------- attendance
    attendance_rows = 0
    for student in students:
        class_subjects = Subject.query.filter_by(class_id=student.class_id).all()
        for day_offset in range(60):
            current = today - timedelta(days=day_offset)
            if current.weekday() >= 5:
                continue
            roll_value = rng.random()
            if roll_value < student.attendance_propensity:
                status = "present"
            elif roll_value < student.attendance_propensity + 0.05:
                status = "late"
            else:
                status = "absent"
            db.session.add(
                Attendance(
                    student_id=student.id,
                    subject_id=random.choice(class_subjects).id,
                    date=current,
                    status=status,
                )
            )
            attendance_rows += 1

    # ------------------------------------------------------------ activities
    for student in students:
        for week in range(12):
            activity_date = today - timedelta(days=week * 7)
            study = float(np.clip(rng.normal(student.study_hours, 0.7), 0, 9))
            db.session.add(
                LearningActivity(
                    student_id=student.id,
                    date=activity_date,
                    study_hours=round(study, 1),
                    participation_score=round(
                        _clamp(student.participation / 10 + rng.normal(0, 0.6), 0, 10), 1
                    ),
                    engagement_score=round(
                        _clamp(student.engagement / 10 + rng.normal(0, 0.6), 0, 10), 1
                    ),
                    assignment_completion=round(
                        _clamp(student.completion_propensity * 100 + rng.normal(0, 6)), 1
                    ),
                    notes="Weekly learning log",
                )
            )

    # ----------------------------------------------------------- assignments
    assignments: list[Assignment] = []
    for subject in subjects:
        for index in range(2):
            assignment = Assignment(
                subject_id=subject.id,
                class_id=subject.class_id,
                title=f"{subject.name} Assignment {index + 1}",
                description="Complete the exercises and submit before the due date.",
                due_date=today - timedelta(days=random.randint(2, 40)),
                max_marks=20,
                created_by=subject.teacher.user_id,
            )
            db.session.add(assignment)
            assignments.append(assignment)
    db.session.flush()

    for student in students:
        class_assignments = [a for a in assignments if a.class_id == student.class_id]
        for assignment in class_assignments:
            if rng.random() < student.completion_propensity:
                status = "late" if rng.random() < 0.12 else "submitted"
                marks = round(
                    _clamp(student.ability * 0.2 + rng.normal(0, 2), 0, assignment.max_marks), 1
                )
                db.session.add(
                    AssignmentSubmission(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        status=status,
                        marks=marks,
                        submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    )
                )
            else:
                db.session.add(
                    AssignmentSubmission(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        status="pending",
                    )
                )

    # ---------------------------------------------------------------- marks
    exams = [
        ("Unit Test 1", 150),
        ("Midterm", 110),
        ("Unit Test 2", 60),
        ("Final Exam", 20),
    ]
    for student in students:
        for subject in Subject.query.filter_by(class_id=student.class_id).all():
            methodology = subject.dominant_method
            teacher_quality = subject.teacher.quality
            for exam_name, days_ago in exams:
                score = (
                    0.52 * student.ability
                    + 0.14 * student.engagement
                    + 0.10 * (student.attendance_propensity * 100)
                    + 0.08 * (student.completion_propensity * 100)
                    + 0.05 * student.participation
                    + METHOD_EFFECT[methodology]
                    + 1.6 * teacher_quality
                    + rng.normal(0, 5.5)
                )
                db.session.add(
                    AcademicRecord(
                        student_id=student.id,
                        subject_id=subject.id,
                        exam_name=exam_name,
                        marks_obtained=round(_clamp(score), 1),
                        max_marks=100,
                        exam_date=today - timedelta(days=days_ago),
                        recorded_by=subject.teacher.user_id,
                    )
                )

    # -------------------------------------------------------------- feedback
    for student in students:
        class_teachers = list(
            {subject.teacher for subject in Subject.query.filter_by(class_id=student.class_id).all()}
        )
        for teacher in random.sample(class_teachers, k=min(3, len(class_teachers))):
            teacher_subject = Subject.query.filter_by(
                teacher_id=teacher.id, class_id=student.class_id
            ).first()
            methodology = teacher_subject.dominant_method if teacher_subject else "Lecture"
            base = 3.4 + 0.55 * teacher.quality + 0.12 * METHOD_EFFECT[methodology]
            ratings = [
                int(np.clip(round(base + rng.normal(0, 0.7)), 1, 5)) for _ in range(5)
            ]
            overall = int(np.clip(round(np.mean(ratings)), 1, 5))
            if overall >= 4:
                sentiment_bucket = "positive"
            elif overall <= 2:
                sentiment_bucket = "negative"
            else:
                sentiment_bucket = "neutral"
            comment = random.choice(COMMENTS[sentiment_bucket])
            analysis = analyze_feedback(comment, ratings + [overall])
            db.session.add(
                StudentFeedback(
                    student_id=student.id,
                    teacher_id=teacher.id,
                    subject_id=teacher_subject.id if teacher_subject else None,
                    clarity_rating=ratings[0],
                    interaction_rating=ratings[1],
                    methodology_rating=ratings[2],
                    practical_rating=ratings[3],
                    difficulty_rating=ratings[4],
                    overall_rating=overall,
                    comments=comment,
                    sentiment_label=analysis["label"],
                    sentiment_score=analysis["score"],
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 45)),
                )
            )

    db.session.commit()
    print(f"Seeded {len(students)} students, {len(teachers)} teachers, {len(subjects)} subjects.")

    result = {
        "students": len(students),
        "teachers": len(teachers),
        "classes": len(classes),
        "subjects": len(subjects),
        "attendance_records": attendance_rows,
        "trained": False,
        "predictions": 0,
    }

    if train_model:
        from .deep_learning import predictor
        from .deep_learning.train_student_ann import train

        print("Training the student performance ANN (this takes a moment)...")
        metrics = train(verbose=0)
        print("Test metrics:", metrics["test_metrics"])

        from .models import Prediction
        from .services.features import public_features, student_features

        count = 0
        for student in students:
            features = student_features(student.id)
            if features.get("_completeness", 0) == 0:
                continue
            prediction = predictor.predict(public_features(features))
            db.session.add(
                Prediction(
                    student_id=student.id,
                    model_version=prediction["model_version"],
                    predicted_score=prediction["predicted_score"],
                    risk_level=prediction["risk_level"],
                    features=public_features(features),
                )
            )
            count += 1
        db.session.commit()
        result["trained"] = True
        result["predictions"] = count
        print(f"Stored {count} predictions.")

        from .services.recommendations import generate_for_student, generate_for_teacher

        for student in students:
            generate_for_student(student.id)
        for teacher in teachers:
            generate_for_teacher(teacher.id)
        print("Generated student and teacher recommendations.")

    print("\nDemo accounts (synthetic data):")
    print("  admin   : admin@school.edu / Admin@12345")
    print("  teacher : teacher1@school.edu / Teacher@12345")
    print("  student : student1001@school.edu / Student@12345")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic demonstration data.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables.")
    parser.add_argument("--skip-train", action="store_true", help="Do not train the ANN.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        seed(reset=args.reset, train_model=not args.skip_train)


if __name__ == "__main__":
    main()
