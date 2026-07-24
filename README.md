# ClubHub — Club Management System

> A modern full-stack web application for managing clubs, members, events, attendance, announcements, notifications, and membership operations from one centralized platform.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-ClubHub-brightgreen)](https://my-club-hub.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-black)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL-orange)](https://www.mysql.com/)
[![Deployment](https://img.shields.io/badge/Deployed%20on-Render-purple)](https://render.com/)

---

## 🌐 Live Demo

### [Visit ClubHub](https://my-club-hub.onrender.com)

ClubHub is deployed as a live web application using Render and Gunicorn.


---

## 📖 About ClubHub

ClubHub is a full-stack club management system designed to simplify the administration of organized clubs while providing members with a modern and convenient digital experience.

Traditional club management often relies on spreadsheets, paper records, messaging applications, and manually maintained attendance lists. ClubHub brings these processes together into a centralized platform.

The system allows administrators to manage members, events, attendance, announcements, reports, and membership renewals, while members can access their club information, register for events, receive notifications, and interact with the club digitally.

ClubHub is designed to support different types of organizations and club structures, including:

* ⚽ Sports Clubs
* 🔐 Private Membership Clubs
* 🎓 Campus Clubs
* 🏋️ Fitness Studios

---

# ✨ Features

## 🏢 Multi-Club-Type Support

ClubHub supports four different club categories, each with dedicated dashboard experiences:

### ⚽ Sports Clubs

Designed for sports organizations that need to manage members, events, attendance, and club activities.

### 🔐 Private Membership Clubs

Designed for private organizations that require structured membership management and renewal tracking.

### 🎓 Campus Clubs

Designed for student organizations and campus-based clubs that organize events and manage student members.

### 🏋️ Fitness Studios

Designed for fitness organizations that need to manage members, activities, events, and membership information.

---

## 👥 Member Management

Administrators can manage club members through a centralized administration interface.

Features include:

* Member profiles
* New member registration
* Member approval workflow
* Membership tiers
* Membership status
* Renewal tracking
* Member search
* Member filtering
* Member record management

---

## 📅 Event Management

Club administrators can create and manage events from the administrative dashboard.

Features include:

* Create events
* Edit events
* Schedule events
* Event registration
* View registered members
* Attendance management
* Event attendance marking
* Event search and filtering

---

## 📋 Attendance Tracking

ClubHub provides tools for tracking member attendance during club events.

Administrators can:

* View registered attendees
* Mark attendance
* Monitor event participation
* Generate attendance-related reports

---

## 📢 Announcements

Administrators can publish club-wide announcements to keep members informed.

Announcements can be used for:

* Club news
* Event updates
* Important notices
* Membership information
* General communication

---

## 🔔 In-App Notifications

ClubHub includes an in-app notification system.

Members can:

* View notifications
* Monitor unread notifications
* Receive updates related to club activities
* Access important information from within the platform

The interface includes a notification bell and unread notification indicator.

---

## 📊 Reports & CSV Export

Administrators can access reports and export important club data.

Supported reporting areas include:

* Members
* Event attendance
* Membership renewals

CSV exports make it possible to process and analyze club data using spreadsheet applications.

---

## 🔎 Search & Filtering

The platform provides search and filtering functionality across important areas of the application.

Administrators can quickly locate:

* Members
* Events
* Relevant club records

---

## 🔐 Authentication & Access Control

ClubHub includes an authentication and authorization system designed to separate administrative and member functionality.

Security-related features include:

* User authentication
* Password hashing
* Session-based authentication
* CSRF protection
* Role-based access control
* Protected administrative routes
* Secure environment configuration

The project also includes dedicated route decorators for handling access control and permissions.

---

## 📱 Responsive Design

ClubHub is designed to provide a responsive experience across different screen sizes.

The application is intended to work on:

* Desktop computers
* Laptops
* Tablets
* Mobile devices

---

## 🎨 Public Landing Page

ClubHub includes a public-facing landing page designed to introduce the platform to potential users.

The landing page includes:

* Product introduction
* Feature highlights
* Pricing information
* Testimonials
* Frequently Asked Questions
* Call-to-action sections

---

# 🛠 Technology Stack

| Layer                | Technology                           |
| -------------------- | ------------------------------------ |
| Programming Language | Python 3.12                          |
| Backend Framework    | Flask                                |
| Database             | MySQL                                |
| Database Driver      | Flask-MySQLdb                        |
| Frontend             | HTML5, CSS3, JavaScript              |
| Templating Engine    | Jinja2                               |
| Production Server    | Gunicorn                             |
| Deployment Platform  | Render                               |
| Styling Fonts        | Cormorant Garamond, DM Sans, DM Mono |

---

# 📁 Project Structure

```text
my-club-hub/
│
├── club_management/
│   │
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── admin.py
│   ├── member.py
│   ├── pages.py
│   ├── decorators.py
│   ├── extensions.py
│   ├── filters.py
│   │
│   ├── migrations/
│   │
│   ├── schema.sql
│   ├── schema_updates.sql
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── images/
│   │   ├── js/
│   │   └── uploads/
│   │
│   ├── templates/
│   │   ├── pages/
│   │   ├── admin_*.html
│   │   ├── member_*.html
│   │   ├── announcements.html
│   │   ├── events.html
│   │   ├── notifications.html
│   │   ├── profile.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── ...
│   │
│   ├── requirements.txt
│   └── README.md
│
├── render.yaml
├── requirements.txt
├── package-lock.json
├── TODO.md
└── README.md
```

> Development-only directories such as `venv/` and `__pycache__/` should not be committed to the repository and should be excluded using `.gitignore`.

---

# 🚀 Local Development Setup

## Prerequisites

Before running ClubHub locally, make sure you have:

* Python 3.12 or compatible Python version
* MySQL Server
* Git
* pip
* A virtual environment tool

---

## 1. Clone the Repository

```bash
git clone https://github.com/wallace-19/my-club-hub.git
```

Navigate into the project:

```bash
cd my-club-hub
```

---

## 2. Create a Virtual Environment

Create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate it on Linux/macOS:

```bash
source venv/bin/activate
```

On Windows:

```powershell
venv\Scripts\activate
```

---

## 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

If the project is configured to use the dependency file inside `club_management`, use:

```bash
pip install -r club_management/requirements.txt
```

> Use the requirements file that contains the dependencies required by the current application configuration.

---

## 4. Configure Environment Variables

Create your environment configuration according to the variables expected by the application.

Typical configuration may include:

```env
SECRET_KEY=your-secret-key

MYSQL_HOST=localhost
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=clubhub
```

Never commit real credentials or secret keys to GitHub.

---

## 5. Create the Database

Open MySQL:

```bash
mysql -u root -p
```

Create the database:

```sql
CREATE DATABASE clubhub;
```

Exit MySQL:

```sql
EXIT;
```

Import the main database schema:

```bash
mysql -u root -p clubhub < club_management/schema.sql
```

If required, apply subsequent database changes:

```bash
mysql -u root -p clubhub < club_management/schema_updates.sql
```

> Only run `schema_updates.sql` if the updates have not already been applied to your database.

---

## 6. Run ClubHub

From the project root, run:

```bash
python club_management/app.py
```

Alternatively, depending on the Flask application configuration:

```bash
cd club_management
python app.py
```

---

# ⚙️ Environment Variables

ClubHub uses environment variables to keep sensitive configuration separate from application source code.

| Variable         | Description                                                 |
| ---------------- | ----------------------------------------------------------- |
| `SECRET_KEY`     | Flask secret key used for sessions and application security |
| `MYSQL_HOST`     | MySQL server hostname                                       |
| `MYSQL_USER`     | MySQL database username                                     |
| `MYSQL_PASSWORD` | MySQL database password                                     |
| `MYSQL_DB`       | MySQL database name                                         |

Production environment variables should be configured through the hosting platform rather than stored directly in source code.

---

# ☁️ Deployment

ClubHub is deployed using:

* **Hosting:** Render
* **Application Server:** Gunicorn
* **Database:** MySQL

Deployment configuration is managed through:

```text
render.yaml

---

# 🔒 Security

ClubHub implements several application-level security measures, including:

* Password hashing
* CSRF protection
* Session-based authentication
* Role-based access control
* Environment-based secret configuration

For a production environment handling real user information, additional security practices should be considered:

* HTTPS enforcement
* Secure cookie configuration
* Rate limiting
* Login throttling
* Strong password policies
* Input validation
* Secure file upload handling
* Database backups
* Dependency updates
* Audit logging
* Monitoring and error tracking

Security should be continuously reviewed as the application evolves.

---


# 🔮 Roadmap & Future Improvements

Potential improvements planned for future versions of ClubHub include:

* [ ] Online membership payments
* [ ] M-PESA payment integration
* [ ] Email notifications
* [ ] WhatsApp notifications
* [ ] Advanced analytics dashboards
* [ ] Automated membership renewal reminders
* [ ] QR-code-based event attendance
* [ ] Digital membership ID cards
* [ ] Advanced permissions and role management
* [ ] Multi-club organization support
* [ ] REST API
* [ ] Mobile application
* [ ] Automated database backups
* [ ] Comprehensive automated testing
* [ ] Improved reporting and data visualization

---

# 🤝 Contributing

Contributions, ideas, and improvements are welcome.

To contribute:

### 1. Fork the repository

Create your own fork of the ClubHub repository.

### 2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

### 3. Make your changes

Implement and test your changes locally.

### 4. Commit your changes

```bash
git add .
git commit -m "Add your feature"
```

### 5. Push your branch

```bash
git push origin feature/your-feature
```

### 6. Open a Pull Request

Submit your changes for review.

---

# 📌 Project Status

ClubHub is an actively developed full-stack club management platform.

The current system provides core functionality for:

* Club administration
* Member management
* Event management
* Attendance tracking
* Announcements
* Notifications
* Membership renewals
* Reports and CSV exports
* Role-based access
* Responsive user interfaces

Additional features and improvements may be introduced as the project continues to evolve.

---

# 👨‍💻 Author

## Wallace

ClubHub was designed and developed as a full-stack software project during an **IT Attachment in 2026**.

### Links

* 🌐 Live Demo: https://my-club-hub.onrender.com
* 💻 GitHub: https://github.com/wallace-19

---

# 📄 License

This project is currently maintained as a personal and educational software project.

If ClubHub is later released as an open-source project, an appropriate open-source license such as the MIT License can be added.

---

## ⭐ Support the Project

If you find ClubHub interesting or useful, consider giving the repository a ⭐ on GitHub.

Your feedback and suggestions are welcome as the platform continues to develop.
