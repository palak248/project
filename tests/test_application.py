import unittest
from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import Mock, patch

import mysql.connector
from werkzeug.security import check_password_hash

from app import create_app
from admin import routes as admin_routes
from auth import routes as auth_routes
from student import routes as student_routes
from teacher import routes as teacher_routes
from teacher import service as teacher_service


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = 1800
    MYSQL_HOST = "127.0.0.1"
    MYSQL_PORT = 3306
    MYSQL_USER = ""
    MYSQL_PASSWORD = ""
    MYSQL_DATABASE = ""
    MYSQL_CONFIGURED = False


class FakeConnection:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


class MarksRepository:
    def __init__(self):
        self.saved = []

    def get_assessment_for_teacher(self, user_id, assessment_id):
        return {"assessment_id": assessment_id, "max_marks": Decimal("20.00")}

    def list_assessment_students(self, user_id, assessment_id):
        return [{"student_id": 3}]

    def upsert_assessment_result(
        self, connection, user_id, assessment_id, student_id, obtained_marks
    ):
        self.saved.append((user_id, assessment_id, student_id, obtained_marks))
        return 1


class AttendanceRepository:
    def __init__(self):
        self.saved = []

    def get_subject_for_teacher(self, user_id, class_subject_id):
        return {"class_subject_id": class_subject_id}

    def list_attendance_students(self, user_id, class_subject_id, attendance_date):
        return [{"student_id": 3}]

    def upsert_attendance(
        self, connection, user_id, class_subject_id, student_id, attendance_date, status
    ):
        self.saved.append(
            (user_id, class_subject_id, student_id, attendance_date.isoformat(), status)
        )
        return 1


class ApplicationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.active_roles = {}
        self.role_patch = patch(
            "auth.decorators.get_active_user_role",
            side_effect=lambda user_id: self.active_roles.get(user_id),
        )
        self.role_patch.start()
        self.addCleanup(self.role_patch.stop)

    def set_session(self, user_id, role, csrf=True):
        with self.client.session_transaction() as session:
            session.clear()
            session["user_id"] = user_id
            session["role"] = role
            if csrf:
                session["csrf_token"] = "test-csrf"
        self.active_roles[user_id] = role

    def csrf(self):
        return {"csrf_token": "test-csrf"}


class AuthenticationTests(ApplicationTestCase):
    def test_student_registration_hashes_password(self):
        connection = FakeConnection()
        with patch.object(auth_routes.service, "get_db_connection", return_value=connection), patch.object(
            auth_routes.service.admin_repository, "create_student", return_value=12
        ) as create_student:
            result = auth_routes.service.register_student(
                {
                    "full_name": "New Student",
                    "student_number": "S-101",
                    "login_identifier": "student-101",
                    "password": "student-pass",
                    "password_confirmation": "student-pass",
                }
            )
        self.assertEqual(result, 12)
        password_hash = create_student.call_args.args[4]
        self.assertNotEqual(password_hash, "student-pass")
        self.assertTrue(check_password_hash(password_hash, "student-pass"))
        self.assertTrue(connection.committed)

    def test_student_registration_creates_student_without_role_selection(self):
        self.set_session(7, "student")
        with patch.object(auth_routes.service, "register_student") as register_student:
            response = self.client.post(
                "/auth/register",
                data={
                    **self.csrf(),
                    "full_name": "New Student",
                    "student_number": "S-100",
                    "login_identifier": "new_student",
                    "password": "student-pass",
                    "password_confirmation": "student-pass",
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/auth/login"))
        register_student.assert_called_once()
        self.assertNotIn(b"name=\"role\"", self.client.get("/auth/register").data)

    def test_student_registration_validation_error_is_returned(self):
        self.set_session(7, "student")
        with patch.object(
            auth_routes.service,
            "register_student",
            side_effect=auth_routes.service.ValidationError("Password is invalid."),
        ):
            response = self.client.post(
                "/auth/register",
                data={**self.csrf(), "login_identifier": "new_student"},
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Password is invalid", response.data)

    def test_student_registration_duplicate_is_rejected(self):
        self.set_session(7, "student")
        with patch.object(
            auth_routes.service,
            "register_student",
            side_effect=mysql.connector.IntegrityError("duplicate"),
        ):
            response = self.client.post(
                "/auth/register",
                data={**self.csrf(), "login_identifier": "existing"},
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn(b"already exists", response.data)

    def test_registered_student_login_uses_student_redirect(self):
        with patch.object(
            auth_routes.service,
            "authenticate_user",
            return_value={"user_id": 88, "role": "student"},
        ):
            self.set_session(88, "student")
            response = self.client.post(
                "/auth/login",
                data={**self.csrf(), "login_identifier": "new_student", "password": "student-pass"},
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/student"))

    def test_valid_login_redirects_by_role(self):
        for role, target in (
            ("admin", "/admin"),
            ("teacher", "/teacher"),
            ("student", "/student"),
        ):
            with self.subTest(role=role), patch.object(
                auth_routes.service,
                "authenticate_user",
                return_value={"user_id": 7, "role": role},
            ):
                self.set_session(7, role)
                response = self.client.post(
                    "/auth/login",
                    data={**self.csrf(), "login_identifier": "user", "password": "valid"},
                )
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.headers["Location"].endswith(target))

    def test_invalid_login_is_generic(self):
        with patch.object(auth_routes.service, "authenticate_user", return_value=None):
            self.set_session(7, "student")
            response = self.client.post(
                "/auth/login",
                data={**self.csrf(), "login_identifier": "unknown", "password": "bad"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid login identifier or password", response.data)

    def test_logout_invalidates_session(self):
        self.set_session(7, "student")
        response = self.client.post("/auth/logout", data=self.csrf())
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)
            self.assertNotIn("role", session)

    def test_unauthenticated_protected_access_redirects(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

    def test_deactivated_session_is_invalidated(self):
        self.set_session(7, "admin")
        self.active_roles[7] = None
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)


class AuthorizationTests(ApplicationTestCase):
    def test_each_role_can_reach_its_own_area(self):
        with patch.object(admin_routes.repository, "dashboard_counts", return_value={
            "student_count": 1, "teacher_count": 1, "class_count": 1,
            "subject_count": 1, "assignment_count": 1,
        }), patch.object(teacher_routes.repository, "get_profile", return_value={"full_name": "T"}), patch.object(
            teacher_routes.repository,
            "get_dashboard_summary",
            return_value={"assignment_count": 1, "class_count": 1, "subject_count": 1, "student_count": 1},
        ), patch.object(student_routes.repository, "get_profile", return_value={"full_name": "S"}), patch.object(
            student_routes.repository,
            "get_dashboard_summary",
            return_value={"result_count": 0, "obtained_marks": 0, "maximum_marks": 0, "subject_count": 0, "attendance_count": 0},
        ):
            for user_id, role, path in ((1, "admin", "/admin"), (2, "teacher", "/teacher"), (3, "student", "/student")):
                with self.subTest(role=role):
                    self.set_session(user_id, role)
                    self.assertEqual(self.client.get(path).status_code, 200)

    def test_cross_role_denial(self):
        for role in ("admin", "teacher", "student"):
            for path in ("/admin", "/teacher", "/student"):
                expected = 200 if path == {"admin": "/admin", "teacher": "/teacher", "student": "/student"}[role] else 403
                with self.subTest(role=role, path=path):
                    self.set_session(10, role)
                    response = self.client.get(path)
                    self.assertIn(response.status_code, (expected, 503) if expected == 200 else (403,))

    def test_student_reads_use_session_user_only(self):
        captured = []
        student_routes.repository.list_results = lambda user_id, assessment_type=None: captured.append(user_id) or []
        student_routes.repository.list_attendance = lambda user_id: captured.append(user_id) or []
        self.set_session(44, "student")
        self.assertEqual(self.client.get("/student/marks").status_code, 200)
        self.assertEqual(self.client.get("/student/attendance").status_code, 200)
        self.assertEqual(captured, [44, 44])
        self.assertEqual(self.client.get("/student/marks/999").status_code, 404)

    def test_teacher_assignment_isolation(self):
        teacher_routes.repository.get_class_for_teacher = lambda user_id, class_id: None
        teacher_routes.repository.get_subject_for_teacher = lambda user_id, subject_id: None
        teacher_routes.repository.get_assessment_for_teacher = lambda user_id, assessment_id: None
        self.set_session(55, "teacher")
        self.assertEqual(self.client.get("/teacher/classes/999").status_code, 404)
        self.assertEqual(self.client.get("/teacher/subjects/999").status_code, 404)
        self.assertEqual(self.client.get("/teacher/subjects/999/attendance").status_code, 404)
        self.assertEqual(self.client.get("/teacher/assessments/999/marks").status_code, 404)


class AdminTests(ApplicationTestCase):
    def test_admin_can_create_another_admin(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.service, "create_admin") as create_admin:
            response = self.client.post(
                "/admin/admins/new",
                data={**self.csrf(), "login_identifier": "second_admin", "password": "admin-pass"},
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/admins"))
        create_admin.assert_called_once()

    def test_non_admin_cannot_create_another_admin(self):
        for role in ("teacher", "student"):
            with self.subTest(role=role):
                self.set_session(1, role)
                response = self.client.post(
                    "/admin/admins/new",
                    data={**self.csrf(), "login_identifier": "blocked", "password": "admin-pass"},
                )
                self.assertEqual(response.status_code, 403)

    def test_admin_creation_duplicate_is_rejected(self):
        self.set_session(1, "admin")
        with patch.object(
            admin_routes.service,
            "create_admin",
            side_effect=mysql.connector.IntegrityError("duplicate"),
        ):
            response = self.client.post(
                "/admin/admins/new",
                data={**self.csrf(), "login_identifier": "Adarsh", "password": "admin-pass"},
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn(b"already exists", response.data)

    def test_student_management(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.service, "create_student") as create_student:
            response = self.client.post("/admin/students/new", data={**self.csrf(), "full_name": "S"})
        self.assertEqual(response.status_code, 302)
        create_student.assert_called_once()

    def test_teacher_management(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.service, "create_teacher") as create_teacher:
            response = self.client.post("/admin/teachers/new", data={**self.csrf(), "full_name": "T"})
        self.assertEqual(response.status_code, 302)
        create_teacher.assert_called_once()

    def test_class_management(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.service, "create_class") as create_class:
            response = self.client.post("/admin/classes/new", data={**self.csrf(), "class_name": "A"})
        self.assertEqual(response.status_code, 302)
        create_class.assert_called_once()

    def test_subject_management(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.service, "create_subject") as create_subject:
            response = self.client.post("/admin/subjects/new", data={**self.csrf(), "subject_name": "Math"})
        self.assertEqual(response.status_code, 302)
        create_subject.assert_called_once()

    def test_enrollment(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.service, "enroll_student") as enroll:
            response = self.client.post("/admin/classes/2/students", data={**self.csrf(), "student_id": "3"})
        self.assertEqual(response.status_code, 302)
        enroll.assert_called_once()

    def test_teacher_assignment(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.service, "create_assignment") as assign:
            response = self.client.post("/admin/assignments", data={**self.csrf(), "teacher_id": "2", "class_subject_id": "4"})
        self.assertEqual(response.status_code, 302)
        assign.assert_called_once()

    def test_account_mutation_without_csrf_is_rejected(self):
        self.set_session(1, "admin")
        response = self.client.post("/admin/students/new", data={"full_name": "S"})
        self.assertEqual(response.status_code, 400)


class TeacherTests(ApplicationTestCase):
    def test_assigned_classes_and_subjects(self):
        self.set_session(2, "teacher")
        with patch.object(teacher_routes.repository, "list_classes", return_value=[]), patch.object(
            teacher_routes.repository, "list_assignments", return_value=[]
        ):
            self.assertEqual(self.client.get("/teacher/classes").status_code, 200)
            self.assertEqual(self.client.get("/teacher/subjects").status_code, 200)

    def test_authorized_students_and_denial(self):
        self.set_session(2, "teacher")
        teacher_routes.repository.get_class_for_teacher = lambda user_id, class_id: {"class_id": class_id} if class_id == 4 else None
        teacher_routes.repository.list_class_assignments = lambda user_id, class_id: []
        teacher_routes.repository.list_class_students = lambda user_id, class_id: []
        self.assertEqual(self.client.get("/teacher/classes/4").status_code, 200)
        self.assertEqual(self.client.get("/teacher/classes/5").status_code, 404)

    def test_assessment_create_edit_validation_and_authorization(self):
        self.set_session(2, "teacher")
        teacher_routes.repository.get_subject_for_teacher = lambda user_id, class_subject_id: {"class_subject_id": 4, "subject_name": "Math", "subject_code": "M", "class_name": "A", "academic_year": "2026"} if class_subject_id == 4 else None
        with patch.object(teacher_routes.service, "create_assessment") as create_assessment:
            response = self.client.post("/teacher/subjects/4/assessments/new", data={**self.csrf(), "title": "Test"})
        self.assertEqual(response.status_code, 302)
        create_assessment.assert_called_once()
        teacher_routes.repository.get_assessment_for_teacher = lambda user_id, assessment_id: {
            "assessment_id": assessment_id,
            "title": "Test",
            "assessment_type": "assignment",
            "assessment_date": None,
            "max_marks": "20.00",
            "subject_name": "Math",
            "subject_code": "M",
            "class_name": "A",
            "academic_year": "2026",
        }
        with patch.object(teacher_routes.service, "update_assessment") as update_assessment:
            response = self.client.post(
                "/teacher/assessments/8/edit",
                data={**self.csrf(), "title": "Updated", "assessment_type": "assignment", "max_marks": "20"},
            )
        self.assertEqual(response.status_code, 302)
        update_assessment.assert_called_once()
        with patch.object(
            teacher_routes.service,
            "update_assessment",
            side_effect=teacher_routes.service.ValidationError("invalid assessment"),
        ):
            response = self.client.post(
                "/teacher/assessments/8/edit",
                data={**self.csrf(), "title": "", "assessment_type": "assignment", "max_marks": "20"},
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/teacher/subjects/99/assessments/new").status_code, 404)

    def test_marks_valid_and_invalid(self):
        repository = MarksRepository()
        connection = FakeConnection()
        with patch.object(teacher_service, "repository", repository), patch.object(
            teacher_service, "get_db_connection", return_value=connection
        ):
            teacher_service.save_marks(2, 8, {"marks_3": "15.00"})
            self.assertEqual(repository.saved[0][-1], Decimal("15.00"))
            for value in ("-1", "20.01"):
                with self.subTest(value=value), self.assertRaises(teacher_service.ValidationError):
                    teacher_service.save_marks(2, 8, {"marks_3": value})

    @unittest.skip("No approved performance calculation rules have been supplied")
    def test_approved_performance_rules(self):
        pass


class AttendanceTests(ApplicationTestCase):
    def test_valid_attendance_entry(self):
        repository = AttendanceRepository()
        connection = FakeConnection()
        with patch.object(teacher_service, "repository", repository), patch.object(
            teacher_service, "get_db_connection", return_value=connection
        ):
            teacher_service.save_attendance(
                2,
                4,
                {"attendance_date": "2026-09-24", "status_3": "Recorded"},
            )
        self.assertEqual(repository.saved[0][-1], "Recorded")
        self.assertTrue(connection.committed)

    def test_invalid_attendance_data(self):
        repository = AttendanceRepository()
        with patch.object(teacher_service, "repository", repository):
            with self.assertRaises(teacher_service.ValidationError):
                teacher_service.save_attendance(2, 4, {"attendance_date": "bad", "status_3": "Recorded"})
            with self.assertRaises(teacher_service.ValidationError):
                teacher_service.save_attendance(2, 4, {"attendance_date": "2026-09-24", "status_3": ""})

    def test_attendance_authorization_and_csrf(self):
        self.set_session(2, "teacher")
        teacher_routes.repository.get_subject_for_teacher = lambda user_id, class_subject_id: None
        self.assertEqual(self.client.get("/teacher/subjects/99/attendance").status_code, 404)
        teacher_routes.repository.get_subject_for_teacher = lambda user_id, class_subject_id: {"class_subject_id": 4}
        self.assertEqual(self.client.post("/teacher/subjects/4/attendance", data={"attendance_date": "2026-09-24"}).status_code, 302)

    def test_student_attendance_isolation(self):
        captured = []
        student_routes.repository.list_attendance = lambda user_id: captured.append(user_id) or []
        self.set_session(9, "student")
        self.assertEqual(self.client.get("/student/attendance").status_code, 200)
        self.assertEqual(captured, [9])


class DashboardReportTests(ApplicationTestCase):
    @unittest.skip("No report routes currently exist")
    def test_reports_are_role_scoped(self):
        pass

    def test_role_dashboard_access(self):
        self.set_session(1, "admin")
        with patch.object(admin_routes.repository, "dashboard_counts", return_value={"student_count": 0, "teacher_count": 0, "class_count": 0, "subject_count": 0, "assignment_count": 0}):
            self.assertEqual(self.client.get("/admin").status_code, 200)
        self.set_session(2, "teacher")
        with patch.object(teacher_routes.repository, "get_profile", return_value={"full_name": "T"}), patch.object(teacher_routes.repository, "get_dashboard_summary", return_value={"assignment_count": 0, "class_count": 0, "subject_count": 0, "student_count": 0}):
            self.assertEqual(self.client.get("/teacher").status_code, 200)
        self.set_session(3, "student")
        with patch.object(student_routes.repository, "get_profile", return_value={"full_name": "S"}), patch.object(student_routes.repository, "get_dashboard_summary", return_value={"result_count": 0, "obtained_marks": 0, "maximum_marks": 0, "subject_count": 0, "attendance_count": 0}):
            self.assertEqual(self.client.get("/student").status_code, 200)


if __name__ == "__main__":
    unittest.main()
