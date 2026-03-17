# My Club Hub - Web-Based Club Management System

## Project Overview
**My Club Hub** is a web-based application designed to help manage clubs efficiently. The system allows administrators to manage club members, organize events, post announcements, and view member information. Members can register, view upcoming events, and stay updated with club activities.  

This project is built using:  
- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Python (Flask)  
- **Database:** MySQL  

---

## Features

### Member Features:
- Member registration and login
- View club information
- View upcoming events
- Receive announcements

### Admin Features:
- Admin login and dashboard
- Add, edit, and delete members
- Create and manage club events
- Post announcements
- View member list and event list

---

## Project Structure
my-club-hub/
│
├── frontend/
│ ├── index.html # Home page
│ ├── register.html # Member registration page
│ ├── style.css # CSS styles
│ └── script.js # Frontend JavaScript
│
├── backend/
│ └── app.py # Python Flask backend
│
├── database/
│ └── club_management.sql # MySQL database schema
│
└── README.md # Project documentation


---

## Installation & Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/my-club-hub.git

2. Install Python dependencies

pip install flask mysql-connector-python

3. Setup MySQL database

 Create a database named club_management

Import the SQL file (club_management.sql) to create tables

4, Run the backend server

python backend/app.py

5. Open the frontend

Open frontend/index.html in a web browser

Usage

. Admin can log in to manage members, events, and announcements

. Members can register, view events, and see announcements

. Use the navigation menu to switch between pages

Database Schema

Tables:

1. members - Stores member information

2. admins - Stores admin credentials

3. events - Stores club events

4. announcements - Stores announcements

Technologies Used

. Frontend: HTML, CSS, JavaScript

. Backend: Python Flask

. Database: MySQL

. API: RESTful API for frontend-backend communication

Future Enhancements

. Add image upload for events and member profiles

. Implement role-based access control for admins and members

. Add email notifications for events and announcements

. Deploy the system online for real-world access

Author

Wallace Macharia
Computer Science Student | Embu, Kenya
Email: wallacemacharia31@email.com
Phone: +254 7XX XXX XXX
