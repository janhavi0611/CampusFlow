# CampusFlow — College Event Resource Allocation System

> A Flask-based web application for managing college events, shared resources, resource requests, availability, and resource allocation through a centralized platform.

CampusFlow helps colleges and universities manage events and shared physical resources such as auditoriums, laboratories, projectors, microphones, cameras, and other equipment.

The system provides separate Admin and Organizer roles, resource availability checking, conflict detection, alternative resource suggestions, and an approval-based allocation workflow.

---

## 🚀 Live Demo

**Hosted Application:**

https://college-event-resource-system.onrender.com

> The application is deployed on Render. Since it uses a free deployment instance, the first request after inactivity may take some time to load.

---

# ✨ Features

## 1. Event Management

Organizers can create and manage college events.

### Features

- Create events
- View events
- Edit events
- Cancel events
- Event date and time management
- Expected attendance tracking
- Event status management
- Event validation
- Event ownership checks

Each event contains information such as:

- Event name
- Organizer
- Expected attendance
- Start date and time
- End date and time
- Status

### Event Lifecycle

```text
Draft
  ↓
Pending
  ↓
Approved
  ↓
Completed
```

Events may also be rejected or cancelled depending on their current state.

---

# 2. Resource Management

Administrators can manage the resources available on campus.

Examples include:

- Auditoriums
- Seminar halls
- Laboratories
- Projectors
- Microphones
- Cameras
- Computers
- Other shared equipment

### Admin Resource Operations

Admins can:

- Add resources
- Edit resources
- View resources
- Activate resources
- Deactivate resources
- Check resource availability

Inactive resources are not considered for new allocations.

---

# 3. Resource Requests

Organizers can request one or more resources for an event.

A request can contain multiple resource requirements.

Example:

```
Annual Technical Symposium

Auditorium × 1
Projector × 2
Microphone × 3
```

The system validates the request before it is submitted.

### Request Workflow

```
Organizer
    ↓
Select Event
    ↓
Select Resource Requirements
    ↓
Submit Request
    ↓
Pending
    ↓
Admin Review
    ↓
Approve / Reject
    ↓
Resource Allocation
```

---

# 4. Resource Availability

CampusFlow provides a resource availability checker.

Users can check whether resources are available for a particular time period before making or approving a request.

The availability system considers:

- Resource status
- Existing allocations
- Requested date
- Requested start time
- Requested end time
- Resource quantity
- Existing bookings

This helps reduce scheduling conflicts and double-booking.

---

# 5. Conflict Detection

The system prevents resources from being allocated to overlapping events.

Two time intervals are considered conflicting when:

```
existing.start < requested.end
AND
existing.end > requested.start
```

### Example

```
Existing Booking
10:00 AM ───────────── 2:00 PM

New Request
12:00 PM ───────────── 4:00 PM

Result: ❌ Conflict
```

However, back-to-back bookings are allowed:

```
Existing Booking
10:00 AM ───────────── 2:00 PM

New Request
                    2:00 PM ───────── 4:00 PM

Result: ✅ Allowed
```

This interval-based approach prevents double-booking while still allowing resources to be used immediately after a previous booking ends.

---

# 6. Alternative Resource Suggestions

If a requested resource is unavailable, the system can identify suitable alternatives.

Alternative selection considers:

1. Resource type
2. Active status
3. Capacity requirements
4. Requested quantity
5. Time availability
6. Suitability for the event

For capacity-based resources, suitable alternatives can be ranked according to capacity.

### Example

```
Expected Attendance: 150

Requested:
Auditorium A
Capacity: 100
Status: Unavailable

Possible Alternative:
Auditorium B
Capacity: 200
Status: Available
```

The system can therefore suggest a suitable available resource instead of simply rejecting the request.

---

# 7. Approval & Allocation Workflow

Administrators are responsible for reviewing resource requests.

A request begins in the:

```
Pending
```

state.

The administrator can then:

```
Approve
   OR
Reject
```

If approved, the resources can be allocated.

### Allocation Workflow

```
Pending Request
      ↓
Admin Review
      ↓
Approve
      ↓
Check Availability
      ↓
Allocate Resources
      ↓
Allocated
```

If the administrator rejects the request:

```
Pending
   ↓
Rejected
```

---

# 8. Atomic Resource Allocation

Resource allocation follows an all-or-nothing approach.

For example, if a request requires:

```
Auditorium × 1
Projector × 2
Microphone × 2
```

and one of the required resources cannot be allocated, the system avoids leaving the request partially allocated.

Conceptually:

```
Check all requested resources
          ↓
   ┌──────┴──────┐
   ↓             ↓
All available   One unavailable
   ↓             ↓
Allocate all    Allocate none
```

This keeps the database state consistent and prevents partially fulfilled requests.

---

# 9. Approval-Time Validation

Resource availability can change between the time a request is submitted and the time an administrator approves it.

Therefore, the system performs availability validation during the allocation process as well.

Example:

```
Organizer submits request
        ↓
Resource is available
        ↓
Another request gets allocated
        ↓
Admin reviews original request
        ↓
Availability checked again
        ↓
Conflict detected if necessary
```

This prevents stale availability information from resulting in invalid allocations.

---

# 👥 Role-Based Access Control

CampusFlow supports two main roles:

- Admin
- Organizer

Authorization is enforced on the backend.

## Admin

Administrators can:

- Access the dashboard
- Manage resources
- Create resources
- Edit resources
- Activate/deactivate resources
- View resource availability
- View submitted resource requests
- Approve resource requests
- Reject resource requests
- Allocate resources
- Cancel allocations
- Manage system-level operations

## Organizer

Organizers can:

- Access the dashboard
- Create events
- View events
- Edit permitted events
- Cancel permitted events
- Submit resource requests
- View their resource requests
- Check resource availability

Organizers cannot:

- Manage resources
- Approve resource requests
- Reject resource requests
- Allocate resources
- Perform administrator-only operations

### Permission Overview

OperationAdminOrganizerView Dashboard✅✅Create Event✅✅View Events✅✅Edit Events✅✅Cancel Events✅✅Manage Resources✅❌Activate/Deactivate Resources✅❌Check Availability✅✅Create Resource Request✅✅View Resource Requests✅Own RequestsApprove Requests✅❌Reject Requests✅❌Allocate Resources✅❌Cancel Allocation✅❌

---

# 📊 Dashboard

The dashboard provides a centralized overview of college operations.

It displays information such as:

- Total events
- Active resources
- Pending approvals
- Upcoming events
- Allocated requests
- Rejected requests
- Cancelled requests
- Inactive resources

The dashboard also provides quick access to:

- Creating events
- Requesting resources
- Viewing events
- Viewing resources
- Viewing requests
- Checking resource availability

---

# 🧪 Testing

The project includes automated tests using `pytest`.

Run the complete test suite with:

```
pytest tests/ -v
```

The tests are designed to verify important application workflows and business rules.

### Testing Areas

AreaPurposeAuthorizationAuthentication and role-based accessEventsEvent creation and validationResourcesResource managementRequestsResource request validationConflictsDouble-booking preventionAlternativesAlternative resource selectionAllocationResource allocation and cancellationRole WorkflowAdmin and Organizer workflows

Testing helps ensure that changes to the application do not break existing functionality.

---

# 🛠️ Technology Stack

LayerTechnologyPurposeBackendPythonApplication developmentWeb FrameworkFlaskRouting and application logicORMSQLAlchemyDatabase interactionDatabaseSQLiteLocal/demo databaseAuthenticationFlask-LoginUser authenticationPassword HashingWerkzeugSecure password storageMigrationsFlask-Migrate / AlembicDatabase schema migrationsTemplatesJinja2Dynamic HTML renderingStylingTailwind CSSResponsive user interfaceJavaScriptVanilla JavaScriptClient-side interactionsTestingpytestAutomated testingServerGunicornProduction WSGI serverDeploymentRenderCloud deployment

---

# 🏗️ Project Structure

```
college-event-resource-system/
│
├── app/
│   ├── __init__.py
│   ├── constants.py
│   ├── extensions.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py
│   │   ├── resource.py
│   │   ├── resource_request.py
│   │   └── user.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── events.py
│   │   ├── resources.py
│   │   └── requests.py
│   │
│   └── templates/
│       ├── auth/
│       ├── events/
│       ├── resources/
│       ├── requests/
│       ├── dashboard.html
│       └── base.html
│
├── migrations/
│   ├── versions/
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│
├── instance/
│
├── requirements.txt
├── run.py
├── seed.py
├── init_db.py
├── .env.example
└── README.md
```

---

# 💻 Installation & Running Locally

## Prerequisites

Make sure the following are installed:

- Python 3.10+
- Git
- pip

---

## 1. Clone the Repository

```
git clone https://github.com/janhavi0611/college-event-resource-system.git
cd college-event-resource-system
```

---

## 2. Create a Virtual Environment

### Windows

```
python -m venv venv
```

Activate it:

```
.\venv\Scripts\Activate.ps1
```

### macOS / Linux

```
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db
```

For local development, use a secure random secret key.

You can generate one with:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Do not commit the `.env` file to GitHub.

---

# 🗄️ Database Setup

The project uses Flask-Migrate and Alembic for database migrations.

Apply the existing migrations using:

```
flask db upgrade
```

This creates/updates the database schema based on the migration files.

If you are working with a fresh local database, make sure the database is initialized before starting the application.

---

# 🌱 Database Seeding

The project includes database seeding functionality for creating initial/demo data.

Depending on the current configuration, the database can be initialized using:

```
python seed.py
```

This can be used to populate the application with sample users, events, and resources for testing/demo purposes.

---

# ▶️ Running the Application

Start the Flask development server:

```
python run.py
```

The application will be available at:

```
http://127.0.0.1:5000
```

Open the URL in your browser.

---

# 🔄 Complete System Workflow

The complete CampusFlow workflow can be represented as:

```
                    ┌───────────────┐
                    │     Login     │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 ↓                     ↓
            Organizer                 Admin
                 │                     │
                 ↓                     ↓
          Create Event          Manage Resources
                 │                     │
                 ↓                     ↓
        Request Resources       Check Availability
                 │                     │
                 ↓                     │
              Pending ←────────────────┘
                 │
                 ↓
            Admin Review
                 │
          ┌──────┴──────┐
          ↓             ↓
       Reject        Approve
          │             │
          ↓             ↓
      Rejected     Availability Check
                        │
                        ↓
                  Allocate Resources
                        │
                        ↓
                    Allocated
```

---

# 📐 Conflict Detection Logic

Resource conflicts are detected using interval overlap.

For two bookings:

```
A = [A_start, A_end)
B = [B_start, B_end)
```

A conflict exists when:

```
A_start < B_end
AND
B_start < A_end
```

### Examples

Existing BookingNew BookingResult10:00–14:0012:00–16:00❌ Conflict10:00–14:0014:00–16:00✅ Allowed10:00–14:0008:00–10:00✅ Allowed10:00–14:0009:00–15:00❌ Conflict10:00–14:0011:00–12:00❌ Conflict

Using strict `<` comparisons means that bookings that meet exactly at the boundary are allowed.

---

# 📦 Resource Allocation Model

The system separates resource requests from actual allocations.

A resource request represents what an organizer wants:

```
Resource Request
    ↓
Requested Resource Requirements
```

Actual physical resources are committed during the allocation stage:

```
Resource Request
       ↓
Admin Approval
       ↓
Allocation
       ↓
Physical Resource
```

This separation allows the system to validate availability before resources are actually committed.

---

# 🗃️ Database & Migrations

The application uses SQLAlchemy models and Flask-Migrate/Alembic.

The migration files are stored under:

```
migrations/versions/
```

Common commands:

### Create a migration

```
flask db migrate -m "describe your change"
```

### Apply migrations

```
flask db upgrade
```

### Roll back a migration

```
flask db downgrade
```

Database migrations should be used when modifying database models instead of manually changing the database schema.

---

# 🚀 Deployment

The application is deployed on Render as a Python Web Service.

### Build Command

```
pip install -r requirements.txt
```

### Start Command

```
gunicorn run:app
```

### Environment Variables

Configure the required environment variables in the Render dashboard.

Example:

```
SECRET_KEY=<secure-random-secret>
DATABASE_URL=<database-url>
```

Never commit production secrets to the GitHub repository.

---

# ⚠️ SQLite Deployment Note

SQLite is used for local development and the current demonstration deployment.

SQLite is convenient and lightweight, but it is not ideal for a high-concurrency production application.

For a production-scale deployment, PostgreSQL or another persistent relational database would be recommended.

```
Development
    ↓
SQLite

Demo / Internship Deployment
    ↓
SQLite

Production Scale
    ↓
PostgreSQL
```

---

# 🔐 Security

The application includes:

- Authentication
- Password hashing
- Session management
- Role-based authorization
- Server-side permission checks
- Organizer ownership checks
- Resource availability validation
- Conflict detection
- Protected administrative routes

Authorization is enforced on the backend and is not dependent only on hiding frontend buttons.

---

# 📌 Important Business Rules

### Event Validation

An event must have a valid start and end time.

```
start_datetime < end_datetime
```

### Resource Request Validation

Requested resources must be valid and compatible with the event.

### Availability

A resource cannot be allocated to overlapping active bookings.

### Back-to-Back Bookings

Bookings ending exactly when another booking begins are allowed.

### Inactive Resources

Inactive resources cannot be newly allocated.

### Authorization

Admin-only operations cannot be performed by organizers.

### Allocation

Resource allocation is handled as an all-or-nothing operation to prevent partial allocation states.

---

# 📈 Future Improvements

Potential future improvements include:

- PostgreSQL production database
- Email notifications
- Calendar integration
- Advanced resource search
- Pagination
- Audit logs
- Resource usage analytics
- Exportable reports
- Password reset functionality
- CSRF protection
- Timezone-aware scheduling
- REST API
- Docker support
- Automated CI/CD improvements

---

# 🧩 Architecture

```
                    Browser
                       │
                       ↓
                Flask Application
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
     Authentication   Routes      Templates
          │            │            │
          └────────────┼────────────┘
                       ↓
                Business Logic
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
      Availability   Conflict    Allocation
       Checking     Detection     Engine
          │            │            │
          └────────────┼────────────┘
                       ↓
                 SQLAlchemy ORM
                       │
                       ↓
                    SQLite
```

---

# 📊 Main Entities

The system is built around the following major entities:

```
User
  │
  ├── Organizer
  └── Admin

Event
  │
  └── Resource Request
          │
          ├── Resource Requirements
          │
          └── Allocations

Resource
```

These entities work together to represent the complete event resource management workflow.

---

# 🧪 Development Workflow

A typical development workflow is:

```
1. Modify application code
        ↓
2. Update database models if required
        ↓
3. Create migration
        ↓
4. Apply migration
        ↓
5. Run application
        ↓
6. Test functionality
        ↓
7. Run automated tests
        ↓
8. Commit changes
        ↓
9. Push to GitHub
        ↓
10. Render deploys latest version
```

---

# 📁 Repository

GitHub:

[https://github.com/janhavi0611/college-event-resource-system](https://github.com/janhavi0611/college-event-resource-system)

Live Application:

[https://college-event-resource-system.onrender.com](https://college-event-resource-system.onrender.com)

---

# 👩‍💻 Author

**Janhavi**

College Event Resource Allocation System developed as an internship/project assignment.
