# Student Performance Analysis System

## 1. Project Purpose

The Student Performance Analysis System is a TYBSc Computer Science college project for managing academic structure and student academic records through role-based web workflows.

## 2. Problem Statement

Academic information such as students, teachers, classes, subjects, assessments, marks, and attendance can become difficult to manage when it is kept in disconnected records. This project provides a centralized application for authorized users to manage those records and for students to view their own stored academic information.

## 3. Main Objectives

- Centralize academic structure and account management.
- Restrict access according to Admin, Teacher, and Student roles.
- Support teacher assignment, assessment, marks, and attendance workflows.
- Allow students to view only their own academic records.
- Provide a maintainable Flask/MySQL foundation for future approved performance analysis and reporting.

## 4. Implemented Features

### Public and Authentication

- Public landing page and login page.
- One-time first-administrator setup at `/auth/setup` when no administrator exists.
- Server-side login validation and role-based redirects.
- Logout with session clearing.
- Authenticated password change.
- Administrator password reset for Teacher and Student accounts.
- Passwords stored using Werkzeug password hashing.

### Admin

- Student and Teacher account creation, editing, deactivation, and password reset.
- Class and Subject creation, listing, editing, and safe deletion.
- Class enrollment management.
- Class-Subject relationship management.
- Teacher-Class-Subject assignment management.
- Safe removal checks for enrollments and class-subject relationships with related academic records.

### Teacher

- Teacher dashboard scoped to the authenticated teacher.
- Assigned class and subject views.
- Authorized enrolled-student views.
- Assessment creation, listing, editing, and safe deletion.
- Marks entry and editing with server-side bounds validation.
- Attendance entry and editing for enrolled students by date.

### Student

- Own profile view.
- Own marks, assignments, and examination result views.
- Own attendance record view.
- Raw subject and overall recorded-mark views.
- Existing Chart.js views for raw subject marks and examination trends.

The following are deliberately **not implemented**: AI/ML, prediction, grades, weighted percentages, attendance percentages, academic-support decisions, and report routes.

## 5. Technology Stack

- Python
- Flask 3.x
- MySQL
- `mysql-connector-python`
- HTML5 and Jinja templates
- CSS3
- Vanilla JavaScript
- Chart.js through the existing performance page integration

The application does not use PHP, Django, Node.js/Express, React, Vue, Angular, Bootstrap, or AI services.

## 6. System Roles

### Admin

Manages accounts, classes, subjects, enrollments, class-subject relationships, and teacher assignments.

### Teacher

Views only assigned classes and subjects, enrolled students within those assignments, and manages authorized assessments, marks, and attendance.

### Student

Views only the student’s own profile, results, marks, attendance, and currently available raw performance views.

## 7. Complete Implemented Workflow

1. Apply the database schema and configure environment variables.
2. Create the first administrator through the one-time setup flow.
3. The Admin creates Teacher and Student accounts.
4. The Admin creates classes and subjects.
5. The Admin enrolls students in classes.
6. The Admin adds subjects to classes and assigns Teachers to class-subject relationships.
7. A Teacher signs in and sees only assigned classes, subjects, and students.
8. The Teacher creates assessments and enters or edits marks for enrolled students.
9. The Teacher records or edits attendance by assigned subject and date.
10. A Student signs in and sees only that student’s stored records.
11. Users can change their own password and log out.

## 8. Project Structure

```text
app.py                         Flask application factory and public routes
config.py                      Environment-based Flask/MySQL configuration
auth/                          Authentication, sessions, CSRF, password lifecycle
admin/                         Admin routes, validation, transactions, and SQL
teacher/                       Teacher routes, validation, transactions, and SQL
student/                       Student routes and own-record SQL
database/schema.sql            MySQL schema
templates/                    Jinja pages and role-specific layouts
static/css/style.css           Shared responsive styling
static/js/                     Small frontend helpers and existing Chart.js integration
scripts/seed_demo.py           Development-only insert-only demo data
tests/test_application.py      Isolated Flask workflow and security tests
requirements.txt               Python dependencies
DEMO_DATA.md                   Local demo-data instructions and fake credentials
```

## 9. Database Overview

The existing schema contains:

- `users`, `students`, and `teachers` for accounts and role records.
- `classes` and `subjects` for academic structure.
- `class_students` for enrollment.
- `class_subjects` for subjects belonging to classes.
- `teacher_class_subjects` for Teacher authorization.
- `assessments` for assignment/examination definitions.
- `assessment_results` for stored marks.
- `attendance` for dated attendance status records.

Foreign keys, unique keys, restrictive deletes, and existing check constraints are preserved. No derived performance table is used.

## 10. Installation and Setup

Create a virtual environment and install the declared dependencies:

```text
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The project has been developed for a local Python and MySQL environment.

## 11. Environment Configuration

Use [.env.example](.env.example) as a reference and export values in the shell or deployment environment:

```text
FLASK_SECRET_KEY=replace-with-a-local-secret
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=student_performance_app
MYSQL_PASSWORD=replace-with-local-password
MYSQL_DATABASE=student_performance
```

Additional settings include `SESSION_LIFETIME_MINUTES` and `SESSION_COOKIE_SECURE`. Secure cookies default to enabled; for local HTTP-only development, explicitly set `SESSION_COOKIE_SECURE=false`.

Never commit real credentials or secrets.

## 12. Database Setup

Create a local database, then apply the schema:

```text
mysql -u <local-user> -p <local-database> < database/schema.sql
```

The application does not automatically create or reset the database.

## 13. First-Admin Setup

For the required local development account, apply the schema and run:

```text
python scripts/bootstrap_admin.py
```

This creates the predefined development administrator `Adarsh` with the local
development password documented in [DEMO_DATA.md](DEMO_DATA.md), only when
that login identifier does not already exist. It is idempotent and never
updates, deletes, or resets an existing account.

The application also provides a first-administrator setup link on the login
page when no administrator exists.

The setup flow:

- validates the login identifier and password;
- hashes the password server-side;
- uses a transaction and setup lock;
- closes once an administrator exists; and
- does not create additional public registration routes.

## 14. Demo Data

Demo data is development-only. Follow [DEMO_DATA.md](DEMO_DATA.md).

Preview the plan without connecting to MySQL:

```text
python scripts/seed_demo.py --dry-run
```

Insert synthetic data into a disposable local database:

```text
python scripts/seed_demo.py --print-credentials
```

The script is insert-only, aborts on non-empty databases by default, and never drops, truncates, resets, updates, or deletes rows. `--allow-existing` is an explicit opt-in for inserting into an existing development database; it does not enable reset behavior.

## 15. Running the Application

With the virtual environment active and environment variables configured:

```text
python app.py
```

Then open the local Flask URL shown by the development server. For local HTTP sessions, set `SESSION_COOKIE_SECURE=false` explicitly.

## 16. Testing

Run the isolated automated suite with:

```text
python -m unittest discover -s tests -p 'test_*.py' -v
```

The latest verified run reported:

- 27 tests run
- 25 passed
- 0 failed
- 2 skipped

The skipped tests cover report routes, which do not exist yet, and approved performance calculation rules, which have not been supplied.

Tests use isolated Flask configuration and mocked repository/service boundaries. They do not use production or development database data.

## 17. Security Features

- Werkzeug password hashing.
- Generic invalid-login responses.
- Server-side role and active-account revalidation.
- Role and ownership/assignment checks on protected operations.
- Student records scoped to the authenticated student session.
- Teacher records scoped to Teacher-Class-Subject assignments and enrollment.
- CSRF protection on state-changing authentication, administration, assessment, marks, enrollment, assignment, and attendance forms.
- Parameterized SQL values.
- Environment-based database credentials and Flask secrets.
- HTTP-only, SameSite session cookies and configurable session lifetime.
- Secure cookie default for production deployments.
- Transactional mutations and restrictive database relationships.

## 18. Known Limitations

- No approved centralized performance engine exists yet.
- No percentage, grade, weighting, pass/fail, attendance-percentage, or academic-support rules have been approved or implemented.
- Current performance pages show raw obtained/max marks and existing raw-mark charts only.
- Attendance status is stored as free text because the schema has no approved status vocabulary.
- No report routes, print-specific report pages, exports, or generated PDFs exist.
- No live MySQL integration test has been run in the current environment.
- The database does not independently enforce `obtained_marks <= max_marks`; application validation enforces it during marks entry.
- First-admin setup assumes deployment access is controlled while the database is empty.

## 19. Future Scope

Future work requires explicit academic approval before implementation:

- Centralized performance service based on approved aggregation, weighting, rounding, and minimum-data rules.
- Approved grade and pass/fail mapping.
- Approved attendance status and percentage rules.
- Missing, absent, and incomplete-record policy.
- Transparent academic-support rules.
- Teacher and Admin performance dashboards using the centralized service.
- Print-friendly reports and optional export workflows.
- Live MySQL integration tests and deployment verification.

These items are future enhancements, not current implemented features.