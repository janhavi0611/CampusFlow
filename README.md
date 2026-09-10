# 🎓 CampusFlow — College Event Resource Allocation System

CampusFlow is a Flask web application for planning university events and reserving shared campus facilities and equipment. It brings event organizers and administrators into one workflow for requesting, reviewing, allocating, and tracking resources such as auditoriums, laboratories, projectors, microphones, cameras, and computers.

The application uses role-based access control, an hourly availability view, time-overlap checks, capacity-aware venue selection, and an all-or-nothing allocation process to help prevent double-booking and incomplete reservations.

| Link | Destination |
| --- | --- |
| GitHub repository | [janhavi0611/college-event-resource-system](https://github.com/janhavi0611/college-event-resource-system) |
| Live demo | [college-event-resource-system.onrender.com](https://college-event-resource-system.onrender.com/) |

> The live demo is hosted on Render. A free instance may take a short time to wake after inactivity.

---

## What CampusFlow Provides

| Capability | Description |
| --- | --- |
| Event workspace | Create, view, edit, and track events with dates, attendance, descriptions, and lifecycle status. |
| Resource catalogue | Maintain named campus resources across six supported categories and activate or deactivate them when needed. |
| Flexible requests | Request particular resources, quantity-based resource requirements, or both for an event time window. |
| Admin review | Administrators allocate pending requests atomically or reject them with a recorded reason. |
| Availability planner | See an active resource's schedule in hourly slots from 08:00 to 20:00. |
| Collision protection | Reject allocations that overlap an active reservation for the same resource. |
| Smart fallback | Offer a suitable available resource when a selected one is inactive, too small, or already booked. |
| Ownership protection | Organizers are limited to their own events and requests; administrators have system-wide access. |
| Automated checks | A `pytest` suite covers authentication, events, requests, availability, alternatives, conflicts, allocation, and role flow. |

---

## Application Flow

CampusFlow follows a review-based reservation process:

```text
Organizer creates an event
          ↓
Organizer submits a resource request
          ↓
Administrator reviews the pending request
          ↓
Availability, capacity, and conflicts are checked again
          ↓
Allocated in full  ─── or ───  Rejected with a reason and possible alternatives
```

An event records its own schedule and status independently from a resource request. Resource-request times must fall within the selected event's start and end times.

### Event status progression

```text
Draft → Submitted → Approved → Completed
  └──────────────→ Cancelled
Submitted ───────→ Draft
Approved ────────→ Cancelled
```

The application only permits the status transitions defined by the event model.

### Resource-request statuses

| Status | Meaning |
| --- | --- |
| `Pending` | Submitted and awaiting an administrator's decision. |
| `Allocated` | Every required resource passed validation and has been reserved. |
| `Rejected` | Allocation could not be completed, or an administrator declined it. |
| `Cancelled` | The request was cancelled and any associated allocations were released. |

---

## Resource Safeguards

### Preventing booking clashes

An existing allocation conflicts with a requested interval when both conditions are true:

```text
existing_start < requested_end
AND
existing_end > requested_start
```

This correctly catches partial, complete, contained, and enclosing overlaps. Reservations that meet exactly at a boundary are allowed, so a booking ending at 14:00 does not block another booking beginning at 14:00.

Cancelled allocations are excluded from conflict checks, which makes their resources available again.

### Allocation

An administrator's approval runs through one allocation service. It validates the request's status and timing, checks the requested resources or quantities, verifies active status, confirms venue capacity where applicable, and looks for time conflicts.

```text
Validate every required resource
        ↓
All checks pass? ── Yes → create all allocations → mark request Allocated
        │
        No
        ↓
create no partial allocation → mark request Rejected → store reason
```

The database transaction is rolled back on any failed validation, preventing a request from being only partly fulfilled.

### Choosing an alternative

When the requested resource cannot be used, CampusFlow searches active resources of the same type that are free during the requested window. For auditoriums and laboratories, the alternative must also accommodate the event's expected attendance.

Venue candidates are ordered by the smallest sufficient capacity, then by name; equipment candidates are ordered by name. This favors a suitable venue without unnecessarily occupying a larger one.

---

## Roles and Permissions

Authentication is handled by Flask-Login, with user records stored in the database and passwords stored as hashes.

| Action | Administrator | Organizer |
| --- | :---: | :---: |
| Sign in and view dashboard | ✓ | ✓ |
| Create events | ✓ | ✓ |
| View events | All | Own events |
| Edit or cancel events | All | Own events |
| Submit resource requests | ✓ | Own events only |
| View requests | All | Own requests |
| Cancel requests | ✓ | Own requests |
| View availability | ✓ | ✓ |
| Add or edit resources | ✓ | — |
| Activate or deactivate resources | ✓ | — |
| Approve and allocate requests | ✓ | — |
| Reject requests and add a reason | ✓ | — |

Backend checks enforce the administrator role and event/request ownership; restrictions are not only a user-interface convention.

---

## Technology

| Area | Tools used |
| --- | --- |
| Language | Python |
| Web framework | Flask 3.1.3 |
| Data layer | SQLAlchemy with Flask-SQLAlchemy |
| Database migrations | Flask-Migrate / Alembic |
| Authentication | Flask-Login |
| Password security | Werkzeug password hashing |
| Templates | Jinja2 |
| Local database default | SQLite (`instance/app.db`) |
| Testing | pytest |
| Production server | Gunicorn |
| Hosted demo | Render |

---

## Project Layout

```text
college-event-resource-system/
├── app/
│   ├── models/                 # User, event, resource, request, and allocation models
│   ├── routes/                 # Authentication, dashboard, event, resource, and request routes
│   ├── templates/              # Jinja templates, including error pages
│   ├── utils/auth.py           # Role and ownership helpers
│   ├── services.py             # Conflict, availability, alternative, and allocation logic
│   ├── extensions.py           # Database and migration extensions
│   └── __init__.py             # Flask application factory
├── migrations/                 # Alembic migration history
├── tests/                      # Automated pytest test suite
├── .env.example                # Environment-variable template
├── init_db.py                  # Database initialization helper
├── seed.py                     # Fresh demo-data setup
├── requirements.txt            # Python dependencies
└── run.py                      # Local application entry point
```

### Architecture at a glance

```text
Browser → Flask routes → services → SQLAlchemy models → SQLite / configured database
                    ↓
              Jinja templates
```

Routes coordinate HTTP requests and authorization. The service layer keeps core allocation behavior—such as overlap detection and alternative selection—separate from route handlers. Models represent the persistent data and relationships.

---

## Run Locally

### Before you begin

- Python 3.10 or later
- `pip`
- Git (if cloning the repository)

### 1. Get the code

```bash
git clone https://github.com/janhavi0611/college-event-resource-system.git
cd college-event-resource-system
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add local configuration

Copy `.env.example` to a new file named `.env`, then replace the placeholder with a long, random secret:

```env
SECRET_KEY=replace-with-a-long-random-secret-key
```

The default local database location is `instance/app.db`. To use a different database, set `DATABASE_URL` in `.env`, for example:

```env
DATABASE_URL=sqlite:///app.db
```

Keep `.env` private; it is already excluded by `.gitignore`.

### 5. Create the database

Apply the tracked schema migrations:

```bash
flask db upgrade
```

### 6. Add sample data (optional)

```bash
python seed.py
```

> **Caution:** `seed.py` drops and recreates all tables before adding demo users, resources, events, requests, and an example allocation. Use it only for a fresh local demo database, never for data you need to keep.

### 7. Start the application

```bash
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

To enable Flask debugging locally, set `FLASK_DEBUG=true` in `.env` before starting the app.

---

## Demo Accounts

After running `python seed.py`, use any of the following accounts:

| Role | Username | Password | Sample user |
| --- | --- | --- | --- |
| Administrator | `admin` | `admin123` | Administrator |
| Organizer | `organizer` | `org123` | Sarah Jenkins |
| Organizer | `organizer2` | `org123` | David Chen |

These accounts exist solely for local demonstration. Change or remove them in a real deployment.

---

## Database 

CampusFlow models the following core records:

| Record | Purpose |
| --- | --- |
| `User` | Stores account identity, role, and password hash. |
| `Event` | Stores event details, owner, time range, attendance, and lifecycle state. |
| `Resource` | Stores a named facility or item, its category, optional capacity, and active flag. |
| `ResourceRequest` | Connects an event and requester to a requested time range and review status. |
| `ResourceRequestItem` | Represents a particular selected resource. |
| `ResourceRequirement` | Represents a category-and-quantity need, such as two projectors. |
| `Allocation` | Represents the final resource booking and its status. |

The migration files in `migrations/` are the source of truth for evolving an existing database schema. For a normal update, use `flask db upgrade` rather than deleting a working database.

---

## Quality Checks

Run the complete test suite from the project root:

```bash
pytest -q
```

For more detailed test names and output:

```bash
pytest tests/ -v
```

| Test focus | What is verified |
| --- | --- |
| Authentication and authorization | Login behavior and administrator-only route protection. |
| Events | Permitted event status transitions. |
| Resources | Resource creation, activation, and hourly availability generation. |
| Requests | Request persistence and selected-resource relationships. |
| Conflict detection | Overlaps, back-to-back bookings, and cancelled allocations. |
| Alternative selection | Capacity-aware fallback resource selection. |
| Atomic allocation | Successful allocation and no partial allocation after a conflict. |
| Role workflow | An organizer-to-allocation end-to-end scenario. |

Tests use an in-memory SQLite database, so they do not need or alter the local demo database.

---


## Author

**Janhavi**

- GitHub: [janhavi0611](https://github.com/janhavi0611)
- Project repository: [college-event-resource-system](https://github.com/janhavi0611/college-event-resource-system)

---

CampusFlow was built as a college event and shared-resource management project.
