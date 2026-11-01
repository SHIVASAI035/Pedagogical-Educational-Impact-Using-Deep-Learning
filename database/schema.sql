-- Pedagogical and Educational Impact Using Deep Learning
-- MySQL 8.0 schema (authoritative DDL). Generated from the SQLAlchemy models.
-- Apply with:  mysql -u root -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS pedagogical_education_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pedagogical_education_db;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	email VARCHAR(190) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	`role` VARCHAR(20) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_role ON users (`role`);

CREATE TABLE recommendations (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	audience VARCHAR(20) NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	message VARCHAR(400) NOT NULL, 
	rationale VARCHAR(600) NOT NULL, 
	priority VARCHAR(10) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_recommendations_audience ON recommendations (audience);
CREATE INDEX ix_recommendations_user_id ON recommendations (user_id);

CREATE TABLE teachers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	employee_code VARCHAR(40) NOT NULL, 
	department VARCHAR(120), 
	specialization VARCHAR(160), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_teachers_employee_code ON teachers (employee_code);

CREATE TABLE classes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(80) NOT NULL, 
	section VARCHAR(20) NOT NULL, 
	academic_year VARCHAR(20) NOT NULL, 
	class_teacher_id INTEGER, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_class_section_year UNIQUE (name, section, academic_year), 
	FOREIGN KEY(class_teacher_id) REFERENCES teachers (id) ON DELETE SET NULL
);


CREATE TABLE students (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	roll_number VARCHAR(40) NOT NULL, 
	class_id INTEGER, 
	guardian_name VARCHAR(120), 
	date_of_birth DATE, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(class_id) REFERENCES classes (id)
);

CREATE INDEX ix_students_class_id ON students (class_id);
CREATE UNIQUE INDEX ix_students_roll_number ON students (roll_number);

CREATE TABLE subjects (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	class_id INTEGER NOT NULL, 
	teacher_id INTEGER, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_subject_code_class UNIQUE (code, class_id), 
	FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE, 
	FOREIGN KEY(teacher_id) REFERENCES teachers (id) ON DELETE SET NULL
);

CREATE INDEX ix_subjects_teacher_id ON subjects (teacher_id);
CREATE INDEX ix_subjects_code ON subjects (code);
CREATE INDEX ix_subjects_class_id ON subjects (class_id);

CREATE TABLE academic_records (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	student_id INTEGER NOT NULL, 
	subject_id INTEGER NOT NULL, 
	exam_name VARCHAR(80) NOT NULL, 
	marks_obtained FLOAT NOT NULL, 
	max_marks FLOAT NOT NULL, 
	exam_date DATE NOT NULL, 
	recorded_by INTEGER, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(subject_id) REFERENCES subjects (id) ON DELETE CASCADE, 
	FOREIGN KEY(recorded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_academic_records_subject_id ON academic_records (subject_id);
CREATE INDEX ix_academic_records_student_id ON academic_records (student_id);
CREATE INDEX ix_record_student_subject_date ON academic_records (student_id, subject_id, exam_date);

CREATE TABLE assignments (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	subject_id INTEGER NOT NULL, 
	class_id INTEGER NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	description TEXT, 
	due_date DATE NOT NULL, 
	max_marks FLOAT NOT NULL, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id) ON DELETE CASCADE, 
	FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_assignments_subject_id ON assignments (subject_id);
CREATE INDEX ix_assignments_class_id ON assignments (class_id);

CREATE TABLE attendance (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	student_id INTEGER NOT NULL, 
	subject_id INTEGER, 
	date DATE NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	recorded_by INTEGER, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_attendance_student_subject_date UNIQUE (student_id, subject_id, date), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(subject_id) REFERENCES subjects (id) ON DELETE SET NULL, 
	FOREIGN KEY(recorded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_attendance_subject_id ON attendance (subject_id);
CREATE INDEX ix_attendance_date ON attendance (date);
CREATE INDEX ix_attendance_student_id ON attendance (student_id);

CREATE TABLE classroom_observations (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	teacher_id INTEGER NOT NULL, 
	class_id INTEGER, 
	subject_id INTEGER, 
	methodology VARCHAR(60) NOT NULL, 
	observation_date DATE NOT NULL, 
	interaction_score FLOAT NOT NULL, 
	clarity_score FLOAT NOT NULL, 
	engagement_score FLOAT NOT NULL, 
	practical_examples_score FLOAT NOT NULL, 
	material_usage_score FLOAT NOT NULL, 
	observer_notes TEXT, 
	observer_id INTEGER, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(teacher_id) REFERENCES teachers (id) ON DELETE CASCADE, 
	FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE SET NULL, 
	FOREIGN KEY(subject_id) REFERENCES subjects (id) ON DELETE SET NULL, 
	FOREIGN KEY(observer_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_classroom_observations_teacher_id ON classroom_observations (teacher_id);
CREATE INDEX ix_classroom_observations_observation_date ON classroom_observations (observation_date);
CREATE INDEX ix_classroom_observations_class_id ON classroom_observations (class_id);
CREATE INDEX ix_classroom_observations_methodology ON classroom_observations (methodology);
CREATE INDEX ix_classroom_observations_subject_id ON classroom_observations (subject_id);

CREATE TABLE learning_activity (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	student_id INTEGER NOT NULL, 
	date DATE NOT NULL, 
	study_hours FLOAT NOT NULL, 
	participation_score FLOAT NOT NULL, 
	engagement_score FLOAT NOT NULL, 
	assignment_completion FLOAT NOT NULL, 
	notes VARCHAR(255), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_activity_student_date UNIQUE (student_id, date), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX ix_learning_activity_student_id ON learning_activity (student_id);
CREATE INDEX ix_learning_activity_date ON learning_activity (date);

CREATE TABLE predictions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	student_id INTEGER NOT NULL, 
	model_version VARCHAR(60) NOT NULL, 
	predicted_score FLOAT NOT NULL, 
	risk_level VARCHAR(20) NOT NULL, 
	features JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX ix_predictions_risk_level ON predictions (risk_level);
CREATE INDEX ix_predictions_student_id ON predictions (student_id);
CREATE INDEX ix_predictions_created_at ON predictions (created_at);

CREATE TABLE student_feedback (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	student_id INTEGER NOT NULL, 
	teacher_id INTEGER NOT NULL, 
	subject_id INTEGER, 
	clarity_rating INTEGER NOT NULL, 
	interaction_rating INTEGER NOT NULL, 
	methodology_rating INTEGER NOT NULL, 
	practical_rating INTEGER NOT NULL, 
	difficulty_rating INTEGER NOT NULL, 
	overall_rating INTEGER NOT NULL, 
	comments TEXT, 
	sentiment_label VARCHAR(12), 
	sentiment_score FLOAT, 
	is_anonymous BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(teacher_id) REFERENCES teachers (id) ON DELETE CASCADE, 
	FOREIGN KEY(subject_id) REFERENCES subjects (id) ON DELETE SET NULL
);

CREATE INDEX ix_student_feedback_teacher_id ON student_feedback (teacher_id);
CREATE INDEX ix_student_feedback_sentiment_label ON student_feedback (sentiment_label);
CREATE INDEX ix_student_feedback_subject_id ON student_feedback (subject_id);
CREATE INDEX ix_student_feedback_student_id ON student_feedback (student_id);
CREATE INDEX ix_student_feedback_created_at ON student_feedback (created_at);

CREATE TABLE teaching_methods (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	teacher_id INTEGER NOT NULL, 
	subject_id INTEGER, 
	methodology VARCHAR(60) NOT NULL, 
	description TEXT, 
	date_used DATE NOT NULL, 
	duration_minutes INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(teacher_id) REFERENCES teachers (id) ON DELETE CASCADE, 
	FOREIGN KEY(subject_id) REFERENCES subjects (id) ON DELETE SET NULL
);

CREATE INDEX ix_teaching_methods_methodology ON teaching_methods (methodology);
CREATE INDEX ix_teaching_methods_subject_id ON teaching_methods (subject_id);
CREATE INDEX ix_teaching_methods_date_used ON teaching_methods (date_used);
CREATE INDEX ix_teaching_methods_teacher_id ON teaching_methods (teacher_id);

CREATE TABLE assignment_submissions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	assignment_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	marks FLOAT, 
	submitted_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_submission_assignment_student UNIQUE (assignment_id, student_id), 
	FOREIGN KEY(assignment_id) REFERENCES assignments (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX ix_assignment_submissions_assignment_id ON assignment_submissions (assignment_id);
CREATE INDEX ix_assignment_submissions_student_id ON assignment_submissions (student_id);

SET FOREIGN_KEY_CHECKS = 1;