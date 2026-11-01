"""Classes, subjects, marks, attendance, assignments and learning activity."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import (
    AcademicRecord,
    Assignment,
    AssignmentSubmission,
    Attendance,
    ClassRoom,
    LearningActivity,
    Student,
    Subject,
    Teacher,
)
from ..utils.decorators import auth_required, current_user, role_required
from ..utils.errors import ForbiddenError, ValidationError
from ..utils.validation import (
    as_date,
    as_float,
    as_int,
    as_status,
    as_str,
    as_text,
    payload,
    require_fields,
)
from ._helpers import (
    get_or_404,
    paginated,
    require_student_access,
    teacher_can_edit_subject,
    teacher_of,
)

bp = Blueprint("academics", __name__, url_prefix="/api/academics")
classes_bp = Blueprint("classes", __name__, url_prefix="/api/classes")
subjects_bp = Blueprint("subjects", __name__, url_prefix="/api/subjects")


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------
@classes_bp.get("")
@auth_required
def list_classes():
    return jsonify([classroom.to_dict() for classroom in ClassRoom.query.order_by(ClassRoom.name).all()])


@classes_bp.post("")
@role_required("admin")
def create_class():
    data = payload()
    require_fields(data, ["name", "academic_year"])
    classroom = ClassRoom(
        name=as_str(data["name"], "name", max_len=80),
        section=as_str(data.get("section", "A"), "section", max_len=20),
        academic_year=as_str(data["academic_year"], "academic_year", max_len=20),
        class_teacher_id=data.get("class_teacher_id"),
    )
    db.session.add(classroom)
    db.session.commit()
    return jsonify(classroom.to_dict()), 201


@classes_bp.put("/<int:class_id>")
@role_required("admin")
def update_class(class_id: int):
    classroom = get_or_404(ClassRoom, class_id, "Class")
    data = payload()
    if "name" in data:
        classroom.name = as_str(data["name"], "name", max_len=80)
    if "section" in data:
        classroom.section = as_str(data["section"], "section", max_len=20)
    if "academic_year" in data:
        classroom.academic_year = as_str(data["academic_year"], "academic_year", max_len=20)
    if "class_teacher_id" in data:
        classroom.class_teacher_id = data["class_teacher_id"]
    db.session.commit()
    return jsonify(classroom.to_dict())


@classes_bp.delete("/<int:class_id>")
@role_required("admin")
def delete_class(class_id: int):
    classroom = get_or_404(ClassRoom, class_id, "Class")
    if classroom.students:
        raise ValidationError("Move students to another class before deleting this class.")
    db.session.delete(classroom)
    db.session.commit()
    return jsonify({"message": "Class deleted."})


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
@subjects_bp.get("")
@auth_required
def list_subjects():
    query = Subject.query
    class_id = request.args.get("class_id", type=int)
    if class_id:
        query = query.filter(Subject.class_id == class_id)
    user = current_user()
    if user.role == "teacher" and request.args.get("mine") == "1":
        query = query.filter(Subject.teacher_id == teacher_of(user).id)
    if user.role == "student" and user.student_profile and user.student_profile.class_id:
        query = query.filter(Subject.class_id == user.student_profile.class_id)
    return jsonify([subject.to_dict() for subject in query.order_by(Subject.name).all()])


@subjects_bp.post("")
@role_required("admin")
def create_subject():
    data = payload()
    require_fields(data, ["name", "code", "class_id"])
    get_or_404(ClassRoom, data["class_id"], "Class")
    if data.get("teacher_id") is not None:
        get_or_404(Teacher, data["teacher_id"], "Teacher")
    subject = Subject(
        name=as_str(data["name"], "name", max_len=120),
        code=as_str(data["code"], "code", max_len=30),
        class_id=data["class_id"],
        teacher_id=data.get("teacher_id"),
    )
    db.session.add(subject)
    db.session.commit()
    return jsonify(subject.to_dict()), 201


@subjects_bp.put("/<int:subject_id>")
@role_required("admin")
def update_subject(subject_id: int):
    subject = get_or_404(Subject, subject_id, "Subject")
    data = payload()
    if "name" in data:
        subject.name = as_str(data["name"], "name", max_len=120)
    if "code" in data:
        subject.code = as_str(data["code"], "code", max_len=30)
    if "class_id" in data:
        get_or_404(ClassRoom, data["class_id"], "Class")
        subject.class_id = data["class_id"]
    if "teacher_id" in data:
        subject.teacher_id = data["teacher_id"]
    db.session.commit()
    return jsonify(subject.to_dict())


@subjects_bp.delete("/<int:subject_id>")
@role_required("admin")
def delete_subject(subject_id: int):
    subject = get_or_404(Subject, subject_id, "Subject")
    db.session.delete(subject)
    db.session.commit()
    return jsonify({"message": "Subject deleted."})


# ---------------------------------------------------------------------------
# Academic records (marks)
# ---------------------------------------------------------------------------
@bp.get("/records")
@auth_required
def list_records():
    user = current_user()
    query = AcademicRecord.query
    student_id = request.args.get("student_id", type=int)
    subject_id = request.args.get("subject_id", type=int)

    if user.role == "student":
        student = user.student_profile
        if student is None:
            raise ForbiddenError("This account has no student profile.")
        query = query.filter(AcademicRecord.student_id == student.id)
    elif user.role == "teacher":
        if student_id:
            require_student_access(get_or_404(Student, student_id, "Student"))
            query = query.filter(AcademicRecord.student_id == student_id)
        else:
            subject_ids = [subject.id for subject in teacher_of(user).subjects]
            query = query.filter(AcademicRecord.subject_id.in_(subject_ids))
    elif student_id:
        query = query.filter(AcademicRecord.student_id == student_id)

    if subject_id:
        query = query.filter(AcademicRecord.subject_id == subject_id)
    query = query.order_by(AcademicRecord.exam_date.desc(), AcademicRecord.id.desc())
    return jsonify(paginated(query))


@bp.post("/records")
@auth_required
def create_record():
    user = current_user()
    if user.role not in ("admin", "teacher"):
        raise ForbiddenError("Only teachers and administrators can enter marks.")
    data = payload()
    require_fields(data, ["student_id", "subject_id", "exam_name", "marks_obtained"])
    student = get_or_404(Student, data["student_id"], "Student")
    subject = get_or_404(Subject, data["subject_id"], "Subject")
    if student.class_id != subject.class_id:
        raise ValidationError("The student is not enrolled in this subject's class.")
    if not teacher_can_edit_subject(user, subject):
        raise ForbiddenError("You can only record marks for subjects you teach.")

    marks = as_float(data["marks_obtained"], "marks_obtained", minimum=0)
    max_marks = as_float(data.get("max_marks", 100), "max_marks", minimum=1)
    if marks > max_marks:
        raise ValidationError("'marks_obtained' cannot exceed 'max_marks'.")

    record = AcademicRecord(
        student_id=student.id,
        subject_id=subject.id,
        exam_name=as_str(data["exam_name"], "exam_name", max_len=80),
        marks_obtained=marks,
        max_marks=max_marks,
        exam_date=as_date(data.get("exam_date"), "exam_date", default=date.today()),
        recorded_by=user.id,
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@bp.put("/records/<int:record_id>")
@auth_required
def update_record(record_id: int):
    user = current_user()
    record = get_or_404(AcademicRecord, record_id, "Academic record")
    if not teacher_can_edit_subject(user, record.subject):
        raise ForbiddenError("You can only edit marks for subjects you teach.")
    data = payload()
    if "marks_obtained" in data:
        marks = as_float(data["marks_obtained"], "marks_obtained", minimum=0)
        if marks > record.max_marks:
            raise ValidationError("'marks_obtained' cannot exceed 'max_marks'.")
        record.marks_obtained = marks
    if "max_marks" in data:
        record.max_marks = as_float(data["max_marks"], "max_marks", minimum=1)
    if "exam_name" in data:
        record.exam_name = as_str(data["exam_name"], "exam_name", max_len=80)
    if "exam_date" in data:
        record.exam_date = as_date(data["exam_date"], "exam_date")
    db.session.commit()
    return jsonify(record.to_dict())


@bp.delete("/records/<int:record_id>")
@auth_required
def delete_record(record_id: int):
    user = current_user()
    record = get_or_404(AcademicRecord, record_id, "Academic record")
    if not teacher_can_edit_subject(user, record.subject):
        raise ForbiddenError("You can only delete marks for subjects you teach.")
    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Academic record deleted."})


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
@bp.get("/attendance")
@auth_required
def list_attendance():
    user = current_user()
    query = Attendance.query
    student_id = request.args.get("student_id", type=int)
    if user.role == "student":
        query = query.filter(Attendance.student_id == user.student_profile.id)
    elif student_id:
        require_student_access(get_or_404(Student, student_id, "Student"))
        query = query.filter(Attendance.student_id == student_id)
    subject_id = request.args.get("subject_id", type=int)
    if subject_id:
        query = query.filter(Attendance.subject_id == subject_id)
    if request.args.get("date_from"):
        query = query.filter(Attendance.date >= as_date(request.args["date_from"], "date_from"))
    if request.args.get("date_to"):
        query = query.filter(Attendance.date <= as_date(request.args["date_to"], "date_to"))
    query = query.order_by(Attendance.date.desc()).limit(1000)
    return jsonify([row.to_dict() for row in query.all()])


@bp.post("/attendance")
@auth_required
def record_attendance():
    user = current_user()
    if user.role not in ("admin", "teacher"):
        raise ForbiddenError("Only teachers and administrators can record attendance.")
    data = payload()
    rows = data.get("records") if isinstance(data.get("records"), list) else [data]
    created = 0
    updated = 0
    for row in rows:
        require_fields(row, ["student_id", "status"])
        student = get_or_404(Student, row["student_id"], "Student")
        subject_id = row.get("subject_id")
        if subject_id is not None:
            subject = get_or_404(Subject, subject_id, "Subject")
            if not teacher_can_edit_subject(user, subject):
                raise ForbiddenError("You can only record attendance for subjects you teach.")
        attendance_date = as_date(row.get("date"), "date", default=date.today())
        existing = Attendance.query.filter_by(
            student_id=student.id, subject_id=subject_id, date=attendance_date
        ).first()
        if existing:
            existing.status = as_status(row["status"])
            existing.recorded_by = user.id
            updated += 1
        else:
            db.session.add(
                Attendance(
                    student_id=student.id,
                    subject_id=subject_id,
                    date=attendance_date,
                    status=as_status(row["status"]),
                    recorded_by=user.id,
                )
            )
            created += 1
    db.session.commit()
    return jsonify({"created": created, "updated": updated}), 201


@bp.put("/attendance/<int:attendance_id>")
@auth_required
def update_attendance(attendance_id: int):
    user = current_user()
    if user.role not in ("admin", "teacher"):
        raise ForbiddenError("Only teachers and administrators can update attendance.")
    row = get_or_404(Attendance, attendance_id, "Attendance record")
    if user.role == "teacher" and row.subject and not teacher_can_edit_subject(user, row.subject):
        raise ForbiddenError("You can only update attendance for subjects you teach.")
    data = payload()
    row.status = as_status(data.get("status"))
    db.session.commit()
    return jsonify(row.to_dict())


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------
@bp.get("/assignments")
@auth_required
def list_assignments():
    user = current_user()
    query = Assignment.query
    if user.role == "student":
        student = user.student_profile
        query = query.filter(Assignment.class_id == student.class_id) if student else query.filter(db.false())
    elif user.role == "teacher":
        class_ids = [subject.class_id for subject in teacher_of(user).subjects]
        query = query.filter(Assignment.class_id.in_(class_ids))
    class_id = request.args.get("class_id", type=int)
    if class_id:
        query = query.filter(Assignment.class_id == class_id)
    subject_id = request.args.get("subject_id", type=int)
    if subject_id:
        query = query.filter(Assignment.subject_id == subject_id)
    query = query.order_by(Assignment.due_date.desc())
    return jsonify(paginated(query))


@bp.post("/assignments")
@auth_required
def create_assignment():
    user = current_user()
    if user.role not in ("admin", "teacher"):
        raise ForbiddenError("Only teachers and administrators can create assignments.")
    data = payload()
    require_fields(data, ["subject_id", "title", "due_date"])
    subject = get_or_404(Subject, data["subject_id"], "Subject")
    if not teacher_can_edit_subject(user, subject):
        raise ForbiddenError("You can only create assignments for subjects you teach.")
    assignment = Assignment(
        subject_id=subject.id,
        class_id=subject.class_id,
        title=as_str(data["title"], "title", max_len=160),
        description=as_text(data.get("description"), "description", max_len=2000),
        due_date=as_date(data["due_date"], "due_date"),
        max_marks=as_float(data.get("max_marks", 20), "max_marks", minimum=1),
        created_by=user.id,
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify(assignment.to_dict()), 201


@bp.put("/assignments/<int:assignment_id>")
@auth_required
def update_assignment(assignment_id: int):
    user = current_user()
    assignment = get_or_404(Assignment, assignment_id, "Assignment")
    if not teacher_can_edit_subject(user, assignment.subject):
        raise ForbiddenError("You can only edit assignments for subjects you teach.")
    data = payload()
    if "title" in data:
        assignment.title = as_str(data["title"], "title", max_len=160)
    if "description" in data:
        assignment.description = as_text(data["description"], "description", max_len=2000)
    if "due_date" in data:
        assignment.due_date = as_date(data["due_date"], "due_date")
    if "max_marks" in data:
        assignment.max_marks = as_float(data["max_marks"], "max_marks", minimum=1)
    db.session.commit()
    return jsonify(assignment.to_dict())


@bp.delete("/assignments/<int:assignment_id>")
@auth_required
def delete_assignment(assignment_id: int):
    user = current_user()
    assignment = get_or_404(Assignment, assignment_id, "Assignment")
    if not teacher_can_edit_subject(user, assignment.subject):
        raise ForbiddenError("You can only delete assignments for subjects you teach.")
    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Assignment deleted."})


@bp.get("/submissions")
@auth_required
def list_submissions():
    user = current_user()
    query = AssignmentSubmission.query
    assignment_id = request.args.get("assignment_id", type=int)
    if assignment_id:
        query = query.filter(AssignmentSubmission.assignment_id == assignment_id)
    if user.role == "student":
        query = query.filter(AssignmentSubmission.student_id == user.student_profile.id)
    elif user.role == "teacher":
        assignment_ids = [
            assignment.id
            for subject in teacher_of(user).subjects
            for assignment in subject.assignments
        ]
        query = query.filter(AssignmentSubmission.assignment_id.in_(assignment_ids))
    return jsonify(paginated(query))


@bp.post("/submissions")
@auth_required
def submit_assignment():
    user = current_user()
    if user.role != "student" or not user.student_profile:
        raise ForbiddenError("Only students can submit assignments.")
    data = payload()
    require_fields(data, ["assignment_id"])
    assignment = get_or_404(Assignment, data["assignment_id"], "Assignment")
    if assignment.class_id != user.student_profile.class_id:
        raise ForbiddenError("This assignment is not set for your class.")
    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id, student_id=user.student_profile.id
    ).first()
    if submission is None:
        submission = AssignmentSubmission(
            assignment_id=assignment.id, student_id=user.student_profile.id
        )
        db.session.add(submission)
    submission.status = "late" if date.today() > assignment.due_date else "submitted"
    from datetime import datetime

    submission.submitted_at = datetime.utcnow()
    db.session.commit()
    return jsonify(submission.to_dict()), 201


@bp.put("/submissions/<int:submission_id>")
@auth_required
def grade_submission(submission_id: int):
    user = current_user()
    if user.role not in ("admin", "teacher"):
        raise ForbiddenError("Only teachers and administrators can grade submissions.")
    submission = get_or_404(AssignmentSubmission, submission_id, "Submission")
    if not teacher_can_edit_subject(user, submission.assignment.subject):
        raise ForbiddenError("You can only grade assignments for subjects you teach.")
    data = payload()
    if "status" in data:
        submission.status = as_str(data["status"], "status", max_len=20)
    if "marks" in data:
        submission.marks = as_float(
            data["marks"], "marks", minimum=0, maximum=submission.assignment.max_marks
        )
    db.session.commit()
    return jsonify(submission.to_dict())


# ---------------------------------------------------------------------------
# Learning activity
# ---------------------------------------------------------------------------
@bp.get("/activities")
@auth_required
def list_activities():
    user = current_user()
    student_id = request.args.get("student_id", type=int)
    if user.role == "student":
        student_id = user.student_profile.id
    elif student_id:
        require_student_access(get_or_404(Student, student_id, "Student"))
    query = LearningActivity.query
    if student_id:
        query = query.filter(LearningActivity.student_id == student_id)
    query = query.order_by(LearningActivity.date.desc()).limit(365)
    return jsonify([row.to_dict() for row in query.all()])


@bp.post("/activities")
@auth_required
def record_activity():
    user = current_user()
    if user.role not in ("admin", "teacher"):
        raise ForbiddenError("Only teachers and administrators can record learning activity.")
    data = payload()
    require_fields(data, ["student_id", "date"])
    student = get_or_404(Student, data["student_id"], "Student")
    require_student_access(student)
    activity_date = as_date(data["date"], "date")
    activity = LearningActivity.query.filter_by(
        student_id=student.id, date=activity_date
    ).first()
    if activity is None:
        activity = LearningActivity(student_id=student.id, date=activity_date)
        db.session.add(activity)
    activity.study_hours = as_float(data.get("study_hours", 0), "study_hours", minimum=0, maximum=24)
    activity.participation_score = as_float(
        data.get("participation_score", 0), "participation_score", minimum=0, maximum=10
    )
    activity.engagement_score = as_float(
        data.get("engagement_score", 0), "engagement_score", minimum=0, maximum=10
    )
    activity.assignment_completion = as_float(
        data.get("assignment_completion", 0), "assignment_completion", minimum=0, maximum=100
    )
    activity.notes = as_text(data.get("notes"), "notes", max_len=255)
    db.session.commit()
    return jsonify(activity.to_dict()), 201
