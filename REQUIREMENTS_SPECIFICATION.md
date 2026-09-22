# Student Performance Analysis System

## Requirements Specification

**Document status:** Initial requirements baseline  
**Project type:** TYBSc Computer Science academic project  
**Repository baseline:** The repository currently contains no application implementation, database schema, routes, templates, or dependency configuration.

## 1. Functional Requirements

### 1.1 Authentication and Access

- **FR-001:** The system shall allow registered administrators, teachers, and students to authenticate.
- **FR-002:** The system shall identify the authenticated user's role.
- **FR-003:** The system shall restrict each operation according to the permissions defined in Section 3.
- **FR-004:** The system shall provide a logout operation for authenticated users.
- **FR-005:** The authentication fields, password recovery process, session duration, and account activation process are **REQUIRES USER DECISION**.

### 1.2 Administrator Functions

- **FR-006:** An administrator shall be able to create, view, update, and deactivate student records.
- **FR-007:** An administrator shall be able to create, view, update, and deactivate teacher records.
- **FR-008:** An administrator shall be able to create, view, update, and manage class records.
- **FR-009:** An administrator shall be able to create, view, update, and manage subject records.
- **FR-010:** The system shall support administrator management of user accounts where required.
- **FR-011:** The exact user-account operations available to an administrator, including whether deletion is allowed, are **REQUIRES USER DECISION**.
- **FR-012:** An administrator shall be able to view student, class, subject, marks, attendance, assignment, examination, and performance reports permitted by the system.

### 1.3 Teacher Functions

- **FR-013:** A teacher shall be able to authenticate.
- **FR-014:** A teacher shall be able to view the classes and subjects assigned to that teacher.
- **FR-015:** A teacher shall be able to enter marks for students within the teacher's authorized classes and subjects.
- **FR-016:** A teacher shall be able to update marks previously entered within the teacher's authorized classes and subjects.
- **FR-017:** A teacher shall be able to enter attendance records for students within the teacher's authorized classes and subjects.
- **FR-018:** A teacher shall be able to update attendance records previously entered within the teacher's authorized classes and subjects.
- **FR-019:** A teacher shall be able to create and manage assignment records and examination records within the teacher's authorized classes and subjects.
- **FR-020:** A teacher shall be able to view student performance for the teacher's authorized classes and subjects.
- **FR-021:** A teacher shall be able to view reports for the teacher's authorized classes and subjects.
- **FR-022:** The exact teacher permissions for deleting or finalizing marks, attendance, assignments, and examinations are **REQUIRES USER DECISION**.

### 1.4 Student Functions

- **FR-023:** A student shall be able to authenticate.
- **FR-024:** A student shall be able to view that student's own profile.
- **FR-025:** A student shall be able to view that student's own marks.
- **FR-026:** A student shall be able to view that student's own attendance records and attendance percentage when calculable.
- **FR-027:** A student shall be able to view that student's own assignments and examination results.
- **FR-028:** A student shall be able to view that student's own performance analysis.
- **FR-029:** A student shall be able to view charts and reports containing only that student's authorized information.

### 1.5 Analysis Functions

- **FR-030:** The system shall calculate total marks from the applicable recorded marks.
- **FR-031:** The system shall calculate a percentage when obtained marks and the applicable maximum marks are available.
- **FR-032:** The system shall assign or display a grade when an approved grade mapping is available.
- **FR-033:** The system shall provide subject-wise performance analysis.
- **FR-034:** The system shall provide overall performance analysis.
- **FR-035:** The system shall calculate attendance percentage when attendance totals are available.
- **FR-036:** The system shall identify students who may need academic attention using transparent, rule-based conditions.
- **FR-037:** The system shall display or explain the rule-based reason for an academic-attention indicator.
- **FR-038:** Grade mappings, academic-attention conditions, treatment of missing records, treatment of absent students, and handling of incomplete data are **REQUIRES USER DECISION**.

## 2. Non-Functional Requirements

- **NFR-001 Simplicity:** The system shall remain suitable for implementation, maintenance, and explanation in a TYBSc Computer Science project viva.
- **NFR-002 Maintainability:** The codebase shall use clear naming, a simple structure, and separation between presentation, application logic, and database operations.
- **NFR-003 Correctness:** Calculations and displayed records shall be consistent with the approved business rules and stored data.
- **NFR-004 Explainability:** Analysis results and academic-attention indicators shall be understandable to users and shall not depend on opaque models.
- **NFR-005 Usability:** The interface shall provide clear navigation and validation messages for the three supported user roles.
- **NFR-006 Performance:** Normal record entry, retrieval, calculation, and report views shall complete within a reasonable response time for the expected academic-project dataset. The exact performance target is **REQUIRES USER DECISION**.
- **NFR-007 Availability:** The required availability, backup schedule, and recovery time are **REQUIRES USER DECISION**.
- **NFR-008 Compatibility:** The system shall use HTML5, CSS3, vanilla JavaScript, Python Flask, MySQL, and Chart.js as specified for the project.
- **NFR-009 Portability:** The system shall be runnable in the project's documented development environment.
- **NFR-010 Testing:** Server-side validation and role-based authorization shall be testable independently of frontend controls.

## 3. User Roles and Permissions

### 3.1 Administrator

An administrator may:

- authenticate and log out;
- manage student, teacher, class, and subject records;
- manage user accounts where required;
- view permitted system-wide records and reports; and
- view analysis for the records the administrator is authorized to access.

The exact scope of administrator account management and whether an administrator may permanently delete records are **REQUIRES USER DECISION**.

### 3.2 Teacher

A teacher may:

- authenticate and log out;
- view assigned classes and subjects;
- enter and update marks and attendance for assigned classes and subjects;
- manage assignment and examination records for assigned classes and subjects; and
- view performance and reports for assigned classes and subjects.

A teacher shall not access or modify records outside the teacher's assigned classes and subjects. The approval or finalization workflow for teacher-entered records is **REQUIRES USER DECISION**.

### 3.3 Student

A student may:

- authenticate and log out;
- view the student's own profile;
- view the student's own marks, attendance, assignments, examination results, performance charts, and reports.

A student shall not create or modify academic records and shall not view another student's information.

## 4. Data Requirements

The system shall store and relate the following approved data categories:

- **Student data:** information needed to identify and manage a student. The exact fields are **REQUIRES USER DECISION**.
- **Teacher data:** information needed to identify and manage a teacher. The exact fields are **REQUIRES USER DECISION**.
- **Class data:** class records and their relationships to students, teachers, and subjects as applicable. The exact structure is **REQUIRES USER DECISION**.
- **Subject data:** subject records and their relationships to classes and teachers as applicable. The exact structure is **REQUIRES USER DECISION**.
- **User-account data:** authentication data and role information for administrators, teachers, and students. The exact fields and account lifecycle are **REQUIRES USER DECISION**.
- **Marks data:** recorded marks, the related student, subject, class, and assessment context where applicable. The marks distribution and maximum-mark structure are **REQUIRES USER DECISION**.
- **Attendance data:** attendance records, the related student, subject, class, and attendance event or total where applicable. The recording format is **REQUIRES USER DECISION**.
- **Assignment data:** assignment records and their related student, class, subject, marks, or results as applicable. The exact fields are **REQUIRES USER DECISION**.
- **Examination data:** examination records and their related student, class, subject, marks, or results as applicable. The examination structure is **REQUIRES USER DECISION**.
- **Analysis data:** calculated totals, percentages, grades, performance summaries, attendance percentages, and academic-attention indicators where applicable.

Additional data requirements:

- **DR-001:** Each academic record shall be associated with the correct student and relevant academic context before it is used in analysis.
- **DR-002:** The system shall preserve data relationships needed to identify who entered or updated an academic record, if auditability is approved. Audit fields are **REQUIRES USER DECISION**.
- **DR-003:** The system shall define behavior for duplicate records, incomplete records, corrections, and deletion or archival. These policies are **REQUIRES USER DECISION**.
- **DR-004:** Database identifiers, required fields, uniqueness constraints, retention period, and backup requirements are **REQUIRES USER DECISION**.

## 5. Business Rules

Only the following calculation concepts are defined by the approved scope. Institutional thresholds and mappings must not be assumed.

- **BR-001 Total marks:** Total marks shall be calculated from the marks included by the approved assessment structure. The included assessment types and aggregation method are **REQUIRES USER DECISION**.
- **BR-002 Percentage:** When the applicable maximum marks are defined and non-zero, percentage may be calculated as:

  `percentage = (obtained marks / maximum marks) * 100`

  The maximum marks, rounding method, decimal precision, and handling of missing marks are **REQUIRES USER DECISION**.
- **BR-003 Grade:** A grade shall be determined only from an approved grade mapping. Grade letters or numeric bands are **REQUIRES USER DECISION**.
- **BR-004 Subject-wise performance:** Subject-wise analysis shall use records belonging to the selected student, subject, and applicable academic context.
- **BR-005 Overall performance:** Overall analysis shall combine the applicable subject or assessment results according to an approved aggregation method. The aggregation method is **REQUIRES USER DECISION**.
- **BR-006 Attendance percentage:** When the applicable attendance totals are defined and the denominator is non-zero, attendance percentage may be calculated as:

  `attendance percentage = (attendance counted as present / total attendance counted) * 100`

  The definitions of present, absent, excused, cancelled, and counted attendance are **REQUIRES USER DECISION**.
- **BR-007 Academic attention:** An academic-attention indicator shall be produced only from transparent conditions approved for this project. The conditions, threshold values, combination logic, and display wording are **REQUIRES USER DECISION**.
- **BR-008 No invented policy:** The system shall not infer or invent grading thresholds, attendance thresholds, marks distribution, examination structure, or institutional rules.
- **BR-009 Authorization scope:** A user shall only view or change records permitted by the user's role and assignment scope.
- **BR-010 Invalid calculations:** The system shall not present a misleading percentage, grade, or attendance percentage when the required source data is missing or invalid. The exact user-facing message is **REQUIRES USER DECISION**.

## 6. Security Requirements

- **SEC-001:** Passwords shall not be stored as plaintext; they shall be stored using an appropriate one-way password-hashing mechanism.
- **SEC-002:** Secrets and database credentials shall not be hard-coded in source files and shall be supplied through environment or deployment configuration.
- **SEC-003:** The server shall validate all submitted data, regardless of frontend validation.
- **SEC-004:** Database operations shall use parameterized queries or an equivalent safe database API.
- **SEC-005:** Authorization shall be enforced on the server for every protected operation; hiding a frontend control shall not be treated as authorization.
- **SEC-006:** Students shall be prevented from accessing another student's records by changing request parameters or URLs.
- **SEC-007:** Teachers shall be prevented from accessing or modifying records outside their assigned classes and subjects.
- **SEC-008:** Authentication sessions shall be protected against unauthorized reuse. Session timeout, cookie settings, password policy, and account lockout requirements are **REQUIRES USER DECISION**.
- **SEC-009:** The system shall avoid exposing passwords, secrets, or unnecessary personal data in error messages, reports, and logs.
- **SEC-010:** The required audit logging for authentication and academic-record changes is **REQUIRES USER DECISION**.

## 7. Reporting Requirements

- **REP-001:** The system shall provide administrator reports covering the records and analysis the administrator is authorized to view.
- **REP-002:** The system shall provide teacher reports for assigned classes and subjects.
- **REP-003:** The system shall provide students with reports containing only their own records and analysis.
- **REP-004:** Reports shall support, as applicable, student information, marks, attendance, assignments, examinations, percentages, grades, subject-wise performance, overall performance, and academic-attention indicators.
- **REP-005:** The system shall provide graphical reports using Chart.js for approved performance and attendance views.
- **REP-006:** Graphs shall be based on the same validated data and calculations shown in the corresponding report.
- **REP-007:** Report filters, sorting, date or academic-period selection, export formats, printing, and pagination are **REQUIRES USER DECISION**.
- **REP-008:** The exact report list, chart types, labels, rounding, and empty-data messages are **REQUIRES USER DECISION**.

## 8. Out-of-Scope Features

The following are outside the approved scope unless separately authorized:

- artificial intelligence, machine learning, predictive models, or automated prediction;
- opaque or non-explainable academic risk scoring;
- PHP, Bootstrap, Tailwind, React, Vue, Angular, Node.js, Django, or another unapproved framework;
- unnecessary third-party services or external APIs;
- online payment, fee management, library management, hostel management, transport management, or payroll management;
- messaging, chat, video conferencing, or social features;
- biometric attendance, hardware integration, or device tracking;
- automated timetable generation;
- plagiarism detection or proctoring;
- public student profiles or public report sharing;
- mobile-native applications;
- predictive admissions, dropout prediction, or career prediction; and
- any grading, attendance, marks, examination, or institutional policy not explicitly approved by the institution or project owner.

## Pending Decisions

The following decisions must be approved before implementation of the affected behavior:

- authentication fields, password policy, account lifecycle, and session policy;
- exact fields and relationships for all entities;
- marks distribution, maximum marks, assessment types, and examination structure;
- grade mapping and rounding rules;
- attendance categories and attendance calculation rules;
- academic-attention conditions and threshold values;
- handling of missing, incomplete, duplicate, corrected, deleted, or archived records;
- teacher record-finalization permissions;
- report list, filters, charts, export, and printing requirements; and
- performance, availability, backup, retention, audit, and recovery targets.