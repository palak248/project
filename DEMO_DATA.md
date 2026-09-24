# Local Demo Data

This is development-only data for the Student Performance Analysis System. All names, identifiers, passwords, classes, subjects, marks, and attendance values are synthetic. Do not use these credentials outside a disposable local environment.

## Setup

1. Create a disposable local MySQL database.
2. Apply the schema:

```text
mysql -u <local-user> -p <local-database> < database/schema.sql
```

3. Export the application database configuration from `.env.example` or the shell.
4. Create the required development bootstrap administrator:

```text
python scripts/bootstrap_admin.py
```

This creates `Adarsh` with the documented local development password only when
no administrator exists and the login identifier is unused. If any
administrator already exists, it makes no changes. It never updates, deletes,
or resets an existing account.

5. Preview the seed plan without connecting to MySQL:

```text
python scripts/seed_demo.py --dry-run
```

6. Insert the demo data:

```text
python scripts/seed_demo.py --print-credentials
```

The seed process requires `MYSQL_USER` and `MYSQL_DATABASE`. It uses the existing `MYSQL_HOST`, `MYSQL_PORT`, and `MYSQL_PASSWORD` environment variables. Demo password overrides are supported through:

- `DEMO_ADMIN_PASSWORD`
- `DEMO_TEACHER_PASSWORD`
- `DEMO_STUDENT_PASSWORD`

## Demo Credentials

Default passwords are fake local-development values and are never production credentials:

| Role | Login identifier | Default password |
|---|---|---|
| Admin | `demo_admin` | `DemoAdmin!2026` |
| Teacher | `demo_teacher_1` | `DemoTeacher!2026` |
| Teacher | `demo_teacher_2` | `DemoTeacher!2026` |
| Teacher | `demo_teacher_3` | `DemoTeacher!2026` |
| Student | `demo_student_1` | `DemoStudent!2026` |
| Student | `demo_student_2` | `DemoStudent!2026` |
| Student | `demo_student_3` | `DemoStudent!2026` |
| Student | `demo_student_4` | `DemoStudent!2026` |
| Student | `demo_student_5` | `DemoStudent!2026` |
| Student | `demo_student_6` | `DemoStudent!2026` |

## Safety

- The script checks that every required application table exists.
- By default it aborts when any required table contains rows.
- `--allow-existing` is required to insert into a non-empty development database.
- Even with `--allow-existing`, it never drops, truncates, resets, updates, or deletes data.
- Existing demo identifiers cause an abort rather than an overwrite.
- All inserts run in one transaction and roll back on failure.
- There is no reset or rebuild command.

## Seeded Workflow Coverage

The seed includes:

- one admin, three teachers, and six students;
- two classes and three subjects;
- class enrollments;
- class-subject relationships;
- teacher-class-subject assignments;
- assignment and examination assessments;
- assessment results within each assessment maximum;
- dated attendance records with synthetic `Present` and `Absent` text values.

The data can exercise local login, admin management, teacher assignment-scoped classes/subjects/students, assessment management, marks entry, attendance entry, student result/attendance views, and the existing raw-mark performance charts.

The project currently has no approved performance calculation engine and no report routes. The seed does not invent grades, percentages, weighting, attendance thresholds, or academic-support rules, and those parts cannot be end-to-end verified until approved rules and report functionality exist.
