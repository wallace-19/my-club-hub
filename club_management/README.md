# ◈ ClubHub — Web-Based Club Management System

A full-stack club management platform built with **Flask**, **MySQL**, and a polished dark editorial frontend.

---

## ✦ Features

### Admin Portal
- **Dashboard** — live stats (members, events, announcements), charts (member growth, affiliation breakdown)
- **Member Management** — add, edit, delete, filter/search members; manage status (active/inactive/pending)
- **Event Management** — create and manage events with date, time, location, category, and capacity
- **Announcements** — post announcements with priority levels (high/medium/low) and optional expiry dates

### Member Portal
- **Registration & Login** — secure account creation with hashed passwords
- **Dashboard** — personalized view of registered events and latest announcements
- **Events** — browse all events, register/unregister
- **Announcements** — read all active club announcements
- **Profile** — update name, phone, club affiliation, and bio

---

## ✦ Technology Stack

| Layer     | Technology                    |
|-----------|-------------------------------|
| Frontend  | HTML5, CSS3, Vanilla JavaScript |
| Charts    | Chart.js 4.4                  |
| Backend   | Python 3.10+ / Flask 3.0      |
| Database  | MySQL 8.0+                    |
| Auth      | Werkzeug password hashing     |

---

## ✦ Project Structure

```
club_management/
├── app.py                  # Flask application (all routes + logic)
├── schema.sql              # MySQL database schema + seed data
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── README.md
├── static/
│   ├── css/
│   │   └── style.css       # Complete stylesheet
│   └── js/
│       └── main.js         # Charts, sidebar, modals, animations
└── templates/
    ├── base.html                    # Base layout (sidebar + topbar)
    ├── login.html                   # Login page
    ├── register.html                # Member registration
    ├── setup.html                   # Initial admin setup
    ├── admin_dashboard.html         # Admin overview
    ├── admin_members.html           # Members list
    ├── admin_member_form.html       # Add/edit member
    ├── admin_events.html            # Events list
    ├── admin_event_form.html        # Add/edit event
    ├── admin_announcements.html     # Announcements list
    ├── admin_announcement_form.html # Add/edit announcement
    ├── member_dashboard.html        # Member home
    ├── events.html                  # Member events view
    ├── announcements.html           # Member announcements view
    └── profile.html                 # Member profile editor
```

---

## ✦ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### 2. Clone / Download
```bash
cd club_management
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

> **Note:** On Ubuntu/Debian you may need:
> ```bash
> sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
> ```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your MySQL credentials and a strong SECRET_KEY
```

### 5. Initialize the Database
```bash
# Log into MySQL
mysql -u root -p

# Run the schema
source schema.sql;
# OR: mysql -u root -p < schema.sql
```

### 6. Create the First Admin
Option A — Use the setup route (only works when no admins exist):
```
http://localhost:5000/setup
```

Option B — Insert directly into MySQL:
```sql
USE club_management;
INSERT INTO admins (name, email, password_hash) VALUES (
  'Your Name',
  'admin@yourclub.com',
  -- Generate hash with Python:
  -- python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"
  'paste_hash_here'
);
```

### 7. Run the Application
```bash
python app.py
```

Visit: **http://localhost:5000**

---

## ✦ Default Credentials (Demo)

| Role  | Email                    | Password  |
|-------|--------------------------|-----------|
| Admin | admin@clubmanager.com    | admin123  |

> ⚠️ Change these immediately in production!

---

## ✦ Production Deployment

For production use:

1. **Use a WSGI server** (Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. **Use a reverse proxy** (Nginx) in front of Gunicorn

3. **Set environment variables** securely (don't commit `.env`)

4. **Change `SECRET_KEY`** to a long random string:
   ```python
   import secrets; print(secrets.token_hex(32))
   ```

5. **Enable HTTPS** via Let's Encrypt / Certbot

---

## ✦ Database Schema Overview

```
admins          — id, name, email, password_hash, created_at
members         — id, name, email, password_hash, phone, club_affiliation, status, joined_at, profile_bio
events          — id, title, description, event_date, event_time, location, category, max_attendees, created_by
announcements   — id, title, content, priority, created_by, created_at, expires_at
event_registrations — id, event_id, member_id, registered_at
```

---

## ✦ API Endpoints

| Method | Route                              | Description                    |
|--------|------------------------------------|--------------------------------|
| GET    | `/`                                | Redirect to dashboard or login |
| GET/POST | `/login`                         | Login                          |
| GET/POST | `/register`                      | Member registration            |
| GET    | `/logout`                          | Logout                         |
| GET    | `/dashboard`                       | Member dashboard               |
| GET    | `/events`                          | Member events list             |
| POST   | `/events/register/<id>`            | Register for event             |
| POST   | `/events/unregister/<id>`          | Unregister from event          |
| GET    | `/announcements`                   | Member announcements           |
| GET/POST | `/profile`                       | Member profile                 |
| GET    | `/admin`                           | Admin dashboard                |
| GET    | `/admin/members`                   | Admin members list             |
| GET/POST | `/admin/members/add`             | Add member                     |
| GET/POST | `/admin/members/edit/<id>`       | Edit member                    |
| POST   | `/admin/members/delete/<id>`       | Delete member                  |
| GET    | `/admin/events`                    | Admin events list              |
| GET/POST | `/admin/events/add`              | Create event                   |
| GET/POST | `/admin/events/edit/<id>`        | Edit event                     |
| POST   | `/admin/events/delete/<id>`        | Delete event                   |
| GET    | `/admin/announcements`             | Admin announcements list       |
| GET/POST | `/admin/announcements/add`       | Post announcement              |
| GET/POST | `/admin/announcements/edit/<id>` | Edit announcement              |
| POST   | `/admin/announcements/delete/<id>` | Delete announcement            |
| GET    | `/api/stats`                       | JSON stats for charts          |
| GET/POST | `/setup`                         | Initial admin setup            |
