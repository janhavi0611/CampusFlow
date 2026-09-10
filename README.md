# ?? College Event Resource System

A Flask-based web application for managing college events and their resource allocations. Built with role-based access control, atomic conflict detection, and an alternative suggestion engine — all wrapped in a warm, custom design system.

---

## ? Features

| Feature | Description |
|---|---|
| **Role-Based Access** | Admin / Organizer roles with separate permissions |
| **Event Management** | Create, edit, view, and track event status lifecycle |
| **Resource Catalogue** | Manage venue, equipment, and lab resources with capacity |
| **Resource Requests** | Organizers submit structured allocation requests per event |
| **Atomic Allocation** | All-or-nothing approval — a partial conflict rejects the full request |
| **Conflict Detection** | Real-time time-window overlap detection across all bookings |
| **Alternative Suggestions** | On rejection, the system auto-suggests available alternatives |
| **Availability Timeline** | Per-resource hourly view for any date |
| **Dashboard** | Overview of events, requests, and allocation status |
| **Test Suite** | 14 pytest tests covering auth, allocation, conflicts, and workflows |

---

## ??? Project Structure

```
college-event-resource-system/
+-- app/
¦   +-- __init__.py          # App factory + blueprint registration
¦   +-- extensions.py        # SQLAlchemy, LoginManager
¦   +-- services.py          # Core logic: conflict detection, atomic allocation, alternatives
¦   +-- models/
¦   ¦   +-- __init__.py      # Re-exports all models
¦   ¦   +-- user.py          # User model with Flask-Login
¦   ¦   +-- event.py
¦   ¦   +-- resource.py
¦   ¦   +-- resource_request.py
¦   ¦   +-- allocation.py
¦   +-- routes/
¦   ¦   +-- auth.py          # Login / logout
¦   ¦   +-- dashboard.py     # Home dashboard
¦   ¦   +-- events.py        # Event CRUD
¦   ¦   +-- resources.py     # Resource CRUD + availability
¦   ¦   +-- requests.py      # Request submit / approve / reject
¦   +-- utils/
¦   ¦   +-- auth.py          # @admin_required decorator
¦   +-- templates/
¦       +-- base.html
¦       +-- auth/
¦       +-- dashboard/
¦       +-- events/
¦       +-- resources/
¦       +-- requests/
+-- tests/                   # pytest test suite (14 tests)
+-- seed.py                  # Populate demo data
+-- init_db.py               # Create empty tables
+-- run.py                   # Development server entry point
+-- requirements.txt
+-- .env.example
```

---

## ?? Running Locally

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd college-event-resource-system
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and fill in values:

```bash
cp .env.example .env
```

.env should contain:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/college_events.db
```

### 5. Seed the database with demo data

```bash
python seed.py
```

This creates demo accounts and sample data:

| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Organizer | organizer | org123 |
| Organizer | organizer2 | org123 |

### 6. Start the development server

```bash
python run.py
```

Open your browser at http://localhost:5000

---

## ?? Running Tests

```bash
python -m pytest tests/ -v
```

Expected output: 14 passed

---

## ??? Architecture Notes

### Atomic Allocation
The approval workflow is strictly atomic:
1. Validate request window against event schedule
2. Check each requested resource: active status, capacity, time conflicts
3. If ANY check fails: rollback, reject with reason, suggest alternatives
4. If ALL checks pass: create Allocation rows, commit as a single transaction

### Conflict Detection Formula
Two time windows [A_start, A_end) and [B_start, B_end) conflict if:
  A_start < B_end  AND  A_end > B_start

### Alternative Selection
On rejection, the system queries active resources of the same type with sufficient capacity and no conflicts. Returns smallest sufficient capacity (venues) or alphabetically first (equipment).

---

## ?? License

MIT
