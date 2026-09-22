-- Student Performance Analysis System
-- Minimum MySQL schema. No credentials or seed/demo data are included.
-- Run this file after selecting the target application database.

CREATE TABLE users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    login_identifier VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_login_identifier (login_identifier),
    KEY idx_users_role_active (role, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE students (
    student_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    student_number VARCHAR(50) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id),
    UNIQUE KEY uq_students_user_id (user_id),
    UNIQUE KEY uq_students_student_number (student_number),
    KEY idx_students_full_name (full_name),
    CONSTRAINT fk_students_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE teachers (
    teacher_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    teacher_number VARCHAR(50) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (teacher_id),
    UNIQUE KEY uq_teachers_user_id (user_id),
    UNIQUE KEY uq_teachers_teacher_number (teacher_number),
    KEY idx_teachers_full_name (full_name),
    CONSTRAINT fk_teachers_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE classes (
    class_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    class_name VARCHAR(100) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (class_id),
    UNIQUE KEY uq_classes_name_year (class_name, academic_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE subjects (
    subject_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    subject_code VARCHAR(30) NOT NULL,
    subject_name VARCHAR(150) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (subject_id),
    UNIQUE KEY uq_subjects_code (subject_code),
    KEY idx_subjects_name (subject_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE class_students (
    class_id BIGINT UNSIGNED NOT NULL,
    student_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (class_id, student_id),
    KEY idx_class_students_student_class (student_id, class_id),
    CONSTRAINT fk_class_students_class
        FOREIGN KEY (class_id) REFERENCES classes (class_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_class_students_student
        FOREIGN KEY (student_id) REFERENCES students (student_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE class_subjects (
    class_subject_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    class_id BIGINT UNSIGNED NOT NULL,
    subject_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (class_subject_id),
    UNIQUE KEY uq_class_subjects_class_subject (class_id, subject_id),
    KEY idx_class_subjects_subject_class (subject_id, class_id),
    CONSTRAINT fk_class_subjects_class
        FOREIGN KEY (class_id) REFERENCES classes (class_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_class_subjects_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE teacher_class_subjects (
    assignment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    teacher_id BIGINT UNSIGNED NOT NULL,
    class_subject_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (assignment_id),
    UNIQUE KEY uq_teacher_class_subject (teacher_id, class_subject_id),
    KEY idx_teacher_class_subject_class_subject (class_subject_id, teacher_id),
    CONSTRAINT fk_teacher_class_subjects_teacher
        FOREIGN KEY (teacher_id) REFERENCES teachers (teacher_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_teacher_class_subjects_class_subject
        FOREIGN KEY (class_subject_id) REFERENCES class_subjects (class_subject_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE assessments (
    assessment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    class_subject_id BIGINT UNSIGNED NOT NULL,
    assessment_type ENUM('assignment', 'examination') NOT NULL,
    title VARCHAR(150) NOT NULL,
    assessment_date DATE NULL,
    max_marks DECIMAL(8,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (assessment_id),
    KEY idx_assessments_class_subject_type (class_subject_id, assessment_type),
    KEY idx_assessments_date (assessment_date),
    CONSTRAINT chk_assessments_max_marks_positive CHECK (max_marks > 0),
    CONSTRAINT fk_assessments_class_subject
        FOREIGN KEY (class_subject_id) REFERENCES class_subjects (class_subject_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE assessment_results (
    assessment_result_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    assessment_id BIGINT UNSIGNED NOT NULL,
    student_id BIGINT UNSIGNED NOT NULL,
    obtained_marks DECIMAL(8,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (assessment_result_id),
    UNIQUE KEY uq_assessment_results_assessment_student (assessment_id, student_id),
    KEY idx_assessment_results_student_assessment (student_id, assessment_id),
    CONSTRAINT chk_assessment_results_marks_nonnegative CHECK (obtained_marks >= 0),
    CONSTRAINT fk_assessment_results_assessment
        FOREIGN KEY (assessment_id) REFERENCES assessments (assessment_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_assessment_results_student
        FOREIGN KEY (student_id) REFERENCES students (student_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE attendance (
    attendance_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    class_subject_id BIGINT UNSIGNED NOT NULL,
    student_id BIGINT UNSIGNED NOT NULL,
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (attendance_id),
    UNIQUE KEY uq_attendance_class_subject_student_date
        (class_subject_id, student_id, attendance_date),
    KEY idx_attendance_student_date (student_id, attendance_date),
    KEY idx_attendance_class_subject_date (class_subject_id, attendance_date),
    CONSTRAINT fk_attendance_class_subject
        FOREIGN KEY (class_subject_id) REFERENCES class_subjects (class_subject_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id) REFERENCES students (student_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
