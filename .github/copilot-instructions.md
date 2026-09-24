# Copilot Instructions

## Project Context

This is the Student Performance Analysis System, a Flask and MySQL college project. Keep the existing stack:

- Python and Flask for the backend.
- MySQL through `mysql-connector-python` for persistence.
- Server-rendered HTML5/Jinja templates, CSS3, and plain JavaScript for the frontend.
- Chart.js only where the existing performance views already use it.

Do not introduce PHP, Django, Node.js/Express as a backend, React, Vue, Angular, Bootstrap, AI/ML, chatbots, predictive models, or unnecessary external services.

## Existing Project Architecture

Inspect the relevant implementation before making changes. Reuse the current architecture and naming conventions:

- `app.py` creates the Flask app, configures logging, registers the `auth`, `admin`, and `student` blueprints, and owns the home, health, and teacher placeholder routes.
- `config.py` reads Flask and MySQL settings from environment variables. Keep credentials and secrets out of source files.
- `auth/routes.py` owns login/logout. `auth/service.py` authenticates active users with Werkzeug password hashes. `auth/decorators.py` provides `login_required` and `role_required`.
- `admin/routes.py` handles admin HTTP requests. `admin/service.py` validates input, hashes new passwords, and manages transactions. `admin/repository.py` owns administrative SQL and transaction helpers.
- `student/routes.py` handles student views. `student/repository.py` owns student read queries and scopes them using the authenticated `user_id`.
- `database/connection.py` provides `get_db_connection()` from the current Flask configuration. `database/schema.sql` is the source of the current MySQL schema.
- `templates/` contains shared pages and separate `admin/` and `student/` layouts. Reuse those layouts and existing flash-message, form, table, empty-state, and chart patterns.
- `static/css/style.css` is the shared stylesheet. `static/js/performance-charts.js` displays server-provided chart data; it is not an authority for academic calculations.

Keep module and function names descriptive and consistent with the existing `routes`, `service`, `repository`, and `database` naming. Do not create duplicate implementations or rebuild working functionality.

## Existing Project First

- Inspect only files relevant to the current task before editing.
- Identify the owning route, service, repository, template, or static asset before changing behavior.
- Reuse existing routes, templates, services, repositories, database helpers, CSS, and JavaScript where appropriate.
- Make the smallest safe change that completely satisfies the task.
- Avoid unrelated refactoring, speculative abstractions, unnecessary files, and repeated repository-wide scans.
- Do not reproduce large unchanged files in explanations.

## Requirements and Decisions

- Do not invent requirements, business rules, relationships, grade ranges, attendance thresholds, assessment weightages, pass/fail rules, or academic-support thresholds.
- If an essential, materially affecting decision is undefined, stop and state exactly what decision is required. Do not guess.
- If the task is sufficiently defined, implement it without unnecessary questions.

## Database Safety

- Read `database/schema.sql` and relevant repository code before changing persistence.
- Never drop, truncate, reset, recreate, or delete database data unless explicitly instructed.
- Do not create duplicate tables or duplicate relationships.
- Add migrations or schema changes only when genuinely required, and document them clearly.
- Preserve existing relationships and historical academic data. Prefer controlled, compatible changes.
- Use `get_db_connection()` and the repository layer. Use parameterized SQL values; never interpolate user input into SQL.
- Preserve repository transaction behavior: commit successful mutations, roll back failures, and close cursors/connections.
- Do not use production data for testing.

## Security and Role Isolation

Authentication and authorization must be enforced server-side. Hiding a button or relying on an obscure URL is not authorization.

- Roles are `admin`, `teacher`, and `student`, matching the database enum and session role values.
- Protect routes with the existing decorators and add explicit ownership or assignment checks where needed.
- Students may access only their own profile, marks, performance, attendance, and other academic information. Do not trust a URL parameter in place of `session["user_id"]`.
- Teachers may access only classes, subjects, students, and academic records they are authorized to manage through existing assignment relationships.
- Admins may manage administrative data according to the existing system design.
- Use server-side validation for every input and return understandable errors.
- Preserve Werkzeug password hashing. Never store or log plaintext passwords.
- Use environment configuration for secrets and credentials.
- Protect state-changing requests against CSRF where appropriate, especially POST form actions.
- Preserve secure session settings and clear sessions on logout or reauthentication.
- Avoid exposing credentials, secrets, stack traces, or development/debug controls in user-facing pages.

## Business Logic

- Centralize performance, percentage, grade, attendance, and other academic calculations in backend business logic, normally a service or repository-owned calculation boundary appropriate to the existing design.
- Do not duplicate calculations in routes, Jinja templates, or JavaScript.
- JavaScript may format or display server-provided values, but it must not be the authoritative source of academic results.
- Do not implement undefined academic rules without explicit approval.

## UI and UX

- Preserve the current visual language and improve consistency rather than replacing the frontend.
- Reuse `static/css/style.css`, existing layouts, components, and accessible markup. Do not add Bootstrap.
- Keep pages responsive and preserve the admin/student navigation structure.
- Give important forms server-side validation and clear, useful error messages.
- Provide useful empty states for missing records and chart data.
- Keep Chart.js usage aligned with the existing `performance-charts.js` integration; do not move authoritative calculations into the browser.

## Controlled Development Lifecycle

Work in these phases and do not automatically continue into the next phase after completing the requested phase:

Requirements -> Analysis -> Design -> Implementation -> Testing -> Security Review -> Documentation -> Final Verification

Before implementation:

- Identify relevant files.
- Briefly explain the planned change.
- Identify whether database or schema changes are needed.

After implementation, report:

- Modified files.
- Created files.
- Deleted files.
- Dependency changes.
- Database/schema changes.
- Implemented behavior.
- Exact tests performed.
- Failures and unresolved issues, honestly.

## Testing and Verification

Do not claim completion merely because code was written. Test the relevant slice, including as applicable:

- Normal behavior.
- Invalid input and validation errors.
- Unauthenticated and unauthorized access.
- Role isolation and ownership/assignment boundaries.
- Edge cases and empty states.
- Database queries, transactions, constraints, and error handling.
- The relevant rendered UI flow and responsive behavior.

Use the narrowest relevant executable check first. Do not automatically fix unrelated failures discovered during implementation.

## Change Control and Efficiency

- Keep responses concise but complete. Do not spend tokens explaining obvious code or rewriting unchanged code.
- Do not inspect unrelated files or document features outside the current task.
- Do not create unnecessary abstractions or files.
- Before editing, make the planned scope explicit. After editing, verify the exact files and behavior changed.
- The goal is a reliable, maintainable end-to-end academic workflow, not maximum code volume.