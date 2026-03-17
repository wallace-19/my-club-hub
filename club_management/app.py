"""
Club Management System - Flask Backend
=======================================
Run: python app.py
Default Admin: admin@clubmanager.com / admin123
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'club-mgmt-secret-2024-change-in-prod')

# ── MySQL Configuration ────────────────────────────────────────────────────────
app.config['MYSQL_HOST']     = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER']     = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB']       = os.getenv('MYSQL_DB', 'club_management')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ── Auth Decorators ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_cursor():
    return mysql.connection.cursor()

def commit():
    mysql.connection.commit()

# ── Routes: Auth ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('member_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'member')

        cur = get_cursor()
        if role == 'admin':
            cur.execute("SELECT * FROM admins WHERE email = %s", (email,))
        else:
            cur.execute("SELECT * FROM members WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['user_email']= user['email']
            session['role']      = role
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('admin_dashboard' if role == 'admin' else 'member_dashboard'))
        flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        email      = request.form.get('email', '').strip().lower()
        password   = request.form.get('password', '')
        confirm    = request.form.get('confirm_password', '')
        phone      = request.form.get('phone', '').strip()
        affiliation= request.form.get('club_affiliation', 'General').strip()

        if not all([name, email, password]):
            flash('Name, email, and password are required.', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        hashed = generate_password_hash(password)
        try:
            cur = get_cursor()
            cur.execute(
                "INSERT INTO members (name, email, password_hash, phone, club_affiliation) VALUES (%s,%s,%s,%s,%s)",
                (name, email, hashed, phone, affiliation)
            )
            commit()
            cur.close()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Email already registered.', 'danger')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ── Routes: Member ─────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def member_dashboard():
    cur = get_cursor()

    # Upcoming events
    cur.execute("""
        SELECT e.*, 
               (SELECT COUNT(*) FROM event_registrations r WHERE r.event_id = e.id) AS registered_count
        FROM events e
        WHERE e.event_date >= CURDATE()
        ORDER BY e.event_date ASC
        LIMIT 6
    """)
    upcoming_events = cur.fetchall()

    # Latest announcements
    cur.execute("""
        SELECT a.*, ad.name AS author
        FROM announcements a
        LEFT JOIN admins ad ON a.created_by = ad.id
        WHERE (a.expires_at IS NULL OR a.expires_at >= CURDATE())
        ORDER BY a.created_at DESC
        LIMIT 5
    """)
    announcements = cur.fetchall()

    # Member's own registered events
    cur.execute("""
        SELECT e.* FROM events e
        JOIN event_registrations er ON e.id = er.event_id
        WHERE er.member_id = %s AND e.event_date >= CURDATE()
        ORDER BY e.event_date ASC
    """, (session['user_id'],))
    my_events = cur.fetchall()

    cur.close()
    return render_template('member_dashboard.html',
                           upcoming_events=upcoming_events,
                           announcements=announcements,
                           my_events=my_events)

@app.route('/events')
@login_required
def events():
    cur = get_cursor()
    cur.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM event_registrations r WHERE r.event_id = e.id) AS registered_count,
               (SELECT COUNT(*) FROM event_registrations r WHERE r.event_id = e.id AND r.member_id = %s) AS is_registered
        FROM events e
        ORDER BY e.event_date ASC
    """, (session['user_id'],))
    all_events = cur.fetchall()
    cur.close()
    return render_template('events.html', events=all_events)

@app.route('/events/register/<int:event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    try:
        cur = get_cursor()
        cur.execute(
            "INSERT IGNORE INTO event_registrations (event_id, member_id) VALUES (%s, %s)",
            (event_id, session['user_id'])
        )
        commit()
        cur.close()
        flash('Successfully registered for event!', 'success')
    except Exception:
        flash('Could not register for event.', 'danger')
    return redirect(url_for('events'))

@app.route('/events/unregister/<int:event_id>', methods=['POST'])
@login_required
def unregister_event(event_id):
    cur = get_cursor()
    cur.execute(
        "DELETE FROM event_registrations WHERE event_id = %s AND member_id = %s",
        (event_id, session['user_id'])
    )
    commit()
    cur.close()
    flash('Unregistered from event.', 'info')
    return redirect(url_for('events'))

@app.route('/announcements')
@login_required
def announcements():
    cur = get_cursor()
    cur.execute("""
        SELECT a.*, ad.name AS author
        FROM announcements a
        LEFT JOIN admins ad ON a.created_by = ad.id
        WHERE (a.expires_at IS NULL OR a.expires_at >= CURDATE())
        ORDER BY a.priority DESC, a.created_at DESC
    """)
    items = cur.fetchall()
    cur.close()
    return render_template('announcements.html', announcements=items)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    cur = get_cursor()
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        phone       = request.form.get('phone', '').strip()
        affiliation = request.form.get('club_affiliation', '').strip()
        bio         = request.form.get('profile_bio', '').strip()
        cur.execute("""
            UPDATE members SET name=%s, phone=%s, club_affiliation=%s, profile_bio=%s
            WHERE id=%s
        """, (name, phone, affiliation, bio, session['user_id']))
        commit()
        session['user_name'] = name
        flash('Profile updated!', 'success')

    cur.execute("SELECT * FROM members WHERE id=%s", (session['user_id'],))
    member = cur.fetchone()
    cur.close()
    return render_template('profile.html', member=member)

# ── Routes: Admin ──────────────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    cur = get_cursor()

    cur.execute("SELECT COUNT(*) AS cnt FROM members")
    total_members = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM members WHERE status='active'")
    active_members = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM events WHERE event_date >= CURDATE()")
    upcoming_events = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM announcements WHERE (expires_at IS NULL OR expires_at >= CURDATE())")
    active_announcements = cur.fetchone()['cnt']

    cur.execute("""
        SELECT e.*, COUNT(er.id) AS registered_count
        FROM events e LEFT JOIN event_registrations er ON e.id=er.event_id
        WHERE e.event_date >= CURDATE()
        GROUP BY e.id ORDER BY e.event_date ASC LIMIT 5
    """)
    events = cur.fetchall()

    cur.execute("""
        SELECT a.*, ad.name AS author
        FROM announcements a LEFT JOIN admins ad ON a.created_by=ad.id
        ORDER BY a.created_at DESC LIMIT 5
    """)
    announcements = cur.fetchall()

    cur.execute("SELECT * FROM members ORDER BY joined_at DESC LIMIT 5")
    recent_members = cur.fetchall()

    # Monthly member signups (last 6 months)
    cur.execute("""
        SELECT DATE_FORMAT(joined_at, '%b %Y') AS month, COUNT(*) AS cnt
        FROM members
        WHERE joined_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY YEAR(joined_at), MONTH(joined_at)
        ORDER BY joined_at ASC
    """)
    monthly_signups = cur.fetchall()

    cur.close()
    return render_template('admin_dashboard.html',
        total_members=total_members,
        active_members=active_members,
        upcoming_events=upcoming_events,
        active_announcements=active_announcements,
        events=events,
        announcements=announcements,
        recent_members=recent_members,
        monthly_signups=monthly_signups
    )

# ── Admin: Members ─────────────────────────────────────────────────────────────
@app.route('/admin/members')
@admin_required
def admin_members():
    search = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    cur = get_cursor()

    query = "SELECT * FROM members WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE %s OR email LIKE %s OR club_affiliation LIKE %s)"
        like = f'%{search}%'
        params.extend([like, like, like])
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
    query += " ORDER BY joined_at DESC"

    cur.execute(query, params)
    members = cur.fetchall()
    cur.close()
    return render_template('admin_members.html', members=members, search=search, status_filter=status_filter)

@app.route('/admin/members/add', methods=['GET', 'POST'])
@admin_required
def admin_add_member():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        email       = request.form.get('email', '').strip().lower()
        password    = request.form.get('password', '')
        phone       = request.form.get('phone', '').strip()
        affiliation = request.form.get('club_affiliation', 'General').strip()
        status      = request.form.get('status', 'active')

        try:
            hashed = generate_password_hash(password or 'changeme123')
            cur = get_cursor()
            cur.execute("""
                INSERT INTO members (name, email, password_hash, phone, club_affiliation, status)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (name, email, hashed, phone, affiliation, status))
            commit()
            cur.close()
            flash('Member added successfully!', 'success')
            return redirect(url_for('admin_members'))
        except Exception:
            flash('Email already exists.', 'danger')

    return render_template('admin_member_form.html', member=None, action='add')

@app.route('/admin/members/edit/<int:member_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_member(member_id):
    cur = get_cursor()
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        email       = request.form.get('email', '').strip().lower()
        phone       = request.form.get('phone', '').strip()
        affiliation = request.form.get('club_affiliation', 'General').strip()
        status      = request.form.get('status', 'active')
        new_pass    = request.form.get('password', '')

        if new_pass:
            hashed = generate_password_hash(new_pass)
            cur.execute("""
                UPDATE members SET name=%s, email=%s, phone=%s, club_affiliation=%s,
                status=%s, password_hash=%s WHERE id=%s
            """, (name, email, phone, affiliation, status, hashed, member_id))
        else:
            cur.execute("""
                UPDATE members SET name=%s, email=%s, phone=%s, club_affiliation=%s,
                status=%s WHERE id=%s
            """, (name, email, phone, affiliation, status, member_id))
        commit()
        cur.close()
        flash('Member updated!', 'success')
        return redirect(url_for('admin_members'))

    cur.execute("SELECT * FROM members WHERE id=%s", (member_id,))
    member = cur.fetchone()
    cur.close()
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('admin_members'))
    return render_template('admin_member_form.html', member=member, action='edit')

@app.route('/admin/members/delete/<int:member_id>', methods=['POST'])
@admin_required
def admin_delete_member(member_id):
    cur = get_cursor()
    cur.execute("DELETE FROM members WHERE id=%s", (member_id,))
    commit()
    cur.close()
    flash('Member deleted.', 'info')
    return redirect(url_for('admin_members'))

# ── Admin: Events ──────────────────────────────────────────────────────────────
@app.route('/admin/events')
@admin_required
def admin_events():
    cur = get_cursor()
    cur.execute("""
        SELECT e.*, COUNT(er.id) AS registered_count
        FROM events e LEFT JOIN event_registrations er ON e.id=er.event_id
        GROUP BY e.id ORDER BY e.event_date DESC
    """)
    events = cur.fetchall()
    cur.close()
    return render_template('admin_events.html', events=events)

@app.route('/admin/events/add', methods=['GET', 'POST'])
@admin_required
def admin_add_event():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        event_date  = request.form.get('event_date')
        event_time  = request.form.get('event_time') or None
        location    = request.form.get('location', '').strip()
        category    = request.form.get('category', 'General').strip()
        max_att     = request.form.get('max_attendees', 0) or 0
        try:
            cur = get_cursor()
            cur.execute("""
                INSERT INTO events (title, description, event_date, event_time, location, category, max_attendees, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (title, description, event_date, event_time, location, category, max_att, session['user_id']))
            commit()
            cur.close()
            flash('Event created!', 'success')
            return redirect(url_for('admin_events'))
        except Exception as e:
            flash(f'Error creating event: {e}', 'danger')
    return render_template('admin_event_form.html', event=None, action='add')

@app.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_event(event_id):
    cur = get_cursor()
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        event_date  = request.form.get('event_date')
        event_time  = request.form.get('event_time') or None
        location    = request.form.get('location', '').strip()
        category    = request.form.get('category', 'General').strip()
        max_att     = request.form.get('max_attendees', 0) or 0
        cur.execute("""
            UPDATE events SET title=%s, description=%s, event_date=%s, event_time=%s,
            location=%s, category=%s, max_attendees=%s WHERE id=%s
        """, (title, description, event_date, event_time, location, category, max_att, event_id))
        commit()
        cur.close()
        flash('Event updated!', 'success')
        return redirect(url_for('admin_events'))

    cur.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    event = cur.fetchone()
    cur.close()
    return render_template('admin_event_form.html', event=event, action='edit')

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    cur = get_cursor()
    cur.execute("DELETE FROM events WHERE id=%s", (event_id,))
    commit()
    cur.close()
    flash('Event deleted.', 'info')
    return redirect(url_for('admin_events'))

# ── Admin: Announcements ───────────────────────────────────────────────────────
@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    cur = get_cursor()
    cur.execute("""
        SELECT a.*, ad.name AS author FROM announcements a
        LEFT JOIN admins ad ON a.created_by=ad.id
        ORDER BY a.created_at DESC
    """)
    items = cur.fetchall()
    cur.close()
    return render_template('admin_announcements.html', announcements=items)

@app.route('/admin/announcements/add', methods=['GET', 'POST'])
@admin_required
def admin_add_announcement():
    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        content  = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'medium')
        expires  = request.form.get('expires_at') or None
        cur = get_cursor()
        cur.execute("""
            INSERT INTO announcements (title, content, priority, created_by, expires_at)
            VALUES (%s,%s,%s,%s,%s)
        """, (title, content, priority, session['user_id'], expires))
        commit()
        cur.close()
        flash('Announcement posted!', 'success')
        return redirect(url_for('admin_announcements'))
    return render_template('admin_announcement_form.html', announcement=None, action='add')

@app.route('/admin/announcements/edit/<int:ann_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_announcement(ann_id):
    cur = get_cursor()
    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        content  = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'medium')
        expires  = request.form.get('expires_at') or None
        cur.execute("""
            UPDATE announcements SET title=%s, content=%s, priority=%s, expires_at=%s
            WHERE id=%s
        """, (title, content, priority, expires, ann_id))
        commit()
        cur.close()
        flash('Announcement updated!', 'success')
        return redirect(url_for('admin_announcements'))

    cur.execute("SELECT * FROM announcements WHERE id=%s", (ann_id,))
    ann = cur.fetchone()
    cur.close()
    return render_template('admin_announcement_form.html', announcement=ann, action='edit')

@app.route('/admin/announcements/delete/<int:ann_id>', methods=['POST'])
@admin_required
def admin_delete_announcement(ann_id):
    cur = get_cursor()
    cur.execute("DELETE FROM announcements WHERE id=%s", (ann_id,))
    commit()
    cur.close()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('admin_announcements'))

# ── Admin Setup Route (create first admin) ─────────────────────────────────────
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Only works if no admins exist."""
    cur = get_cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM admins")
    count = cur.fetchone()['cnt']
    cur.close()
    if count > 0:
        flash('Setup already complete.', 'info')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        hashed   = generate_password_hash(password)
        cur = get_cursor()
        cur.execute("INSERT INTO admins (name, email, password_hash) VALUES (%s,%s,%s)",
                    (name, email, hashed))
        commit()
        cur.close()
        flash('Admin account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('setup.html')

# ── API: Stats (for dashboard charts) ─────────────────────────────────────────
@app.route('/api/stats')
@admin_required
def api_stats():
    cur = get_cursor()
    cur.execute("""
        SELECT DATE_FORMAT(joined_at,'%b') AS month, COUNT(*) AS count
        FROM members WHERE joined_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY YEAR(joined_at), MONTH(joined_at)
        ORDER BY joined_at
    """)
    signups = cur.fetchall()

    cur.execute("SELECT club_affiliation, COUNT(*) AS count FROM members GROUP BY club_affiliation")
    affiliations = cur.fetchall()
    cur.close()
    return jsonify({'signups': signups, 'affiliations': affiliations})

# ── Template Filters ───────────────────────────────────────────────────────────
@app.template_filter('format_date')
def format_date(value):
    if not value:
        return ''
    if isinstance(value, (datetime, date)):
        return value.strftime('%B %d, %Y')
    return str(value)

@app.template_filter('format_time')
def format_time(value):
    if not value:
        return ''
    if hasattr(value, 'strftime'):
        return value.strftime('%I:%M %p')
    return str(value)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
