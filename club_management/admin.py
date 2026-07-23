from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash

from .decorators import admin_required

def notify_member(member_id, title, message, notif_type='info'):
    """Create a notification for a member."""
    try:
        from .extensions import get_cursor, commit
        cur = get_cursor()
        cur.execute(
            'INSERT INTO notifications (member_id, title, message, type) VALUES (%s,%s,%s,%s)',
            (member_id, title, message, notif_type)
        )
        commit()
        cur.close()
    except Exception:
        pass
from .extensions import get_cursor, commit
from .auth import is_valid_email, is_strong_enough_password

admin_bp = Blueprint('admin', __name__)
VALID_STATUSES = {'active', 'inactive', 'pending'}
VALID_PRIORITIES = {'low', 'medium', 'high'}
VALID_EVENT_STATUSES = {'scheduled', 'cancelled', 'completed'}


def parse_non_negative_int(value, default=0):
    try:
        number = int(value or default)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def validate_member_form(name, email, password, status, require_password=False):
    if not name:
        return 'Member name is required.'
    if not is_valid_email(email):
        return 'A valid member email is required.'
    if status not in VALID_STATUSES:
        return 'Invalid member status.'
    if (require_password or password) and not is_strong_enough_password(password):
        return 'Password must be at least 8 characters.'
    return None


def validate_event_form(title, event_date, max_attendees, status):
    if not title:
        return 'Event title is required.'
    if not event_date:
        return 'Event date is required.'
    if max_attendees is None:
        return 'Max attendees must be zero or a positive number.'
    if status not in VALID_EVENT_STATUSES:
        return 'Invalid event status.'
    return None


def validate_announcement_form(title, content, priority):
    if not title:
        return 'Announcement title is required.'
    if not content:
        return 'Announcement content is required.'
    if priority not in VALID_PRIORITIES:
        return 'Invalid announcement priority.'
    return None


@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    cur = get_cursor()
    club_type = session.get('club_type', 'sports')

    # ── Common queries ──────────────────────────────────────────
    cur.execute('SELECT COUNT(*) AS cnt FROM members')
    total_members = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM members WHERE status='active'")
    active_members = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM members WHERE status='pending'")
    pending_members = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM events WHERE event_date >= CURDATE() AND status='scheduled'")
    upcoming_events = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM announcements WHERE (expires_at IS NULL OR expires_at >= CURDATE())")
    active_announcements = cur.fetchone()['cnt']

    cur.execute("""
        SELECT e.*, COUNT(er.id) AS registered_count
        FROM events e LEFT JOIN event_registrations er ON e.id=er.event_id
        WHERE e.event_date >= CURDATE() AND e.status='scheduled'
        GROUP BY e.id ORDER BY e.event_date ASC LIMIT 5
    """)
    events = cur.fetchall()

    cur.execute("""
        SELECT a.*, COALESCE(ad.name, 'Admin') AS author
        FROM announcements a LEFT JOIN admins ad ON a.created_by=ad.id
        WHERE (a.expires_at IS NULL OR a.expires_at >= CURDATE())
        ORDER BY a.created_at DESC LIMIT 4
    """)
    announcements = cur.fetchall()

    cur.execute("SELECT * FROM members ORDER BY joined_at DESC LIMIT 5")
    recent_members = cur.fetchall()

    cur.execute("""
        SELECT DATE_FORMAT(MIN(joined_at), '%b %Y') AS month, COUNT(*) AS cnt
        FROM members
        WHERE joined_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY YEAR(joined_at), MONTH(joined_at)
        ORDER BY YEAR(joined_at), MONTH(joined_at)
    """)
    monthly_signups = cur.fetchall()

    # ── Club-type specific queries ──────────────────────────────
    extra = {}

    if club_type == 'sports':
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM events
            WHERE MONTH(event_date)=MONTH(CURDATE()) AND YEAR(event_date)=YEAR(CURDATE())
        """)
        extra['sessions_this_month'] = cur.fetchone()['cnt']

        cur.execute("""
            SELECT COUNT(DISTINCT a.member_id) AS attended,
                   COUNT(DISTINCT er.member_id) AS registered
            FROM events e
            LEFT JOIN event_registrations er ON e.id=er.event_id
            LEFT JOIN attendance a ON e.id=a.event_id
            WHERE e.event_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        row = cur.fetchone()
        attended = row['attended'] or 0
        registered = row['registered'] or 0
        extra['attendance_rate'] = round(attended/registered*100) if registered else 0

        cur.execute("""
            SELECT m.name, m.club_affiliation, COUNT(a.id) AS sessions
            FROM attendance a JOIN members m ON a.member_id=m.id
            GROUP BY m.id ORDER BY sessions DESC LIMIT 5
        """)
        extra['top_athletes'] = cur.fetchall()

    elif club_type == 'private':
        cur.execute("""
            SELECT membership_tier, COUNT(*) AS cnt
            FROM members GROUP BY membership_tier ORDER BY cnt DESC
        """)
        extra['tiers'] = cur.fetchall()

        cur.execute("""
            SELECT name, email, renewal_date, membership_tier
            FROM members
            WHERE renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            AND status='active' ORDER BY renewal_date ASC LIMIT 8
        """)
        extra['renewals_due'] = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) AS cnt FROM members
            WHERE renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """)
        extra['renewals_count'] = cur.fetchone()['cnt']

    elif club_type == 'campus':
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM event_registrations er
            JOIN events e ON er.event_id=e.id
            WHERE MONTH(e.event_date)=MONTH(CURDATE())
        """)
        extra['meeting_attendance'] = cur.fetchone()['cnt']

        cur.execute("""
            SELECT COUNT(*) AS cnt FROM members
            WHERE joined_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        """)
        extra['new_this_semester'] = cur.fetchone()['cnt']

        cur.execute("""
            SELECT club_affiliation AS faculty, COUNT(*) AS cnt
            FROM members GROUP BY club_affiliation ORDER BY cnt DESC LIMIT 6
        """)
        extra['faculty_distribution'] = cur.fetchall()

    elif club_type == 'fitness':
        cur.execute("""
            SELECT e.*, COUNT(er.id) AS check_ins,
                CASE WHEN e.max_attendees > 0
                     THEN ROUND(COUNT(er.id)/e.max_attendees*100) ELSE 0
                END AS capacity_pct
            FROM events e LEFT JOIN event_registrations er ON e.id=er.event_id
            WHERE e.event_date=CURDATE()
            GROUP BY e.id
        """)
        extra['todays_classes'] = cur.fetchall()

        cur.execute("""
            SELECT membership_tier AS plan, COUNT(*) AS cnt
            FROM members GROUP BY membership_tier ORDER BY cnt DESC
        """)
        extra['plans'] = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) AS cnt FROM members
            WHERE renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            AND status='active'
        """)
        extra['renewals_this_month'] = cur.fetchone()['cnt']

        cur.execute("""
            SELECT COALESCE(ROUND(AVG(cap)),0) AS avg_cap FROM (
                SELECT CASE WHEN e.max_attendees > 0
                       THEN ROUND(COUNT(er.id)/e.max_attendees*100) ELSE 0 END AS cap
                FROM events e LEFT JOIN event_registrations er ON e.id=er.event_id
                WHERE e.event_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                AND e.max_attendees > 0 GROUP BY e.id
            ) sub
        """)
        extra['avg_capacity'] = cur.fetchone()['avg_cap']

    cur.close()

    template_map = {
        'sports':  'admin_dashboard_sports.html',
        'private': 'admin_dashboard_private.html',
        'campus':  'admin_dashboard_campus.html',
        'fitness': 'admin_dashboard_fitness.html',
    }
    template = template_map.get(club_type, 'admin_dashboard.html')
    return render_template(template,
        total_members=total_members,
        active_members=active_members,
        pending_members=pending_members,
        upcoming_events=upcoming_events,
        active_announcements=active_announcements,
        events=events,
        announcements=announcements,
        recent_members=recent_members,
        monthly_signups=monthly_signups,
        **extra
    )



@admin_bp.route('/admin/reports')
@admin_required
def admin_reports():
    cur = get_cursor()
    club_type = session.get('club_type', 'sports')

    cur.execute("SELECT COUNT(*) AS cnt FROM members WHERE status='active'")
    active_members = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM members WHERE status='pending'")
    pending_members = cur.fetchone()['cnt']

    cur.execute("""
        SELECT COUNT(*) AS cnt FROM members
        WHERE renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        AND status='active'
    """)
    renewals_due = cur.fetchone()['cnt']

    cur.execute("""
        SELECT e.title, e.event_date, e.location, e.category,
               COUNT(DISTINCT er.id) AS registered,
               COUNT(DISTINCT a.id) AS attended
        FROM events e
        LEFT JOIN event_registrations er ON e.id=er.event_id
        LEFT JOIN attendance a ON e.id=a.event_id
        GROUP BY e.id ORDER BY e.event_date DESC LIMIT 10
    """)
    event_stats = cur.fetchall()

    cur.execute("""
        SELECT club_affiliation, COUNT(*) AS cnt
        FROM members GROUP BY club_affiliation ORDER BY cnt DESC
    """)
    affiliation_stats = cur.fetchall()

    cur.execute("""
        SELECT membership_tier, COUNT(*) AS cnt
        FROM members GROUP BY membership_tier ORDER BY cnt DESC
    """)
    tier_stats = cur.fetchall()

    cur.close()
    return render_template('admin_reports.html',
        active_members=active_members,
        pending_members=pending_members,
        renewals_due=renewals_due,
        event_stats=event_stats,
        affiliation_stats=affiliation_stats,
        tier_stats=tier_stats,
        club_type=club_type
    )


@admin_bp.route('/admin/reports/export/members')
@admin_required
def export_members():
    import csv, io
    from flask import Response
    cur = get_cursor()
    cur.execute("""
        SELECT name, email, phone, club_affiliation, club_type,
               membership_tier, renewal_date, status,
               joined_at
        FROM members ORDER BY joined_at DESC
    """)
    members = cur.fetchall()
    cur.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name','Email','Phone','Affiliation','Club Type',
                     'Membership Tier','Renewal Date','Status','Joined'])
    for m in members:
        writer.writerow([
            m['name'], m['email'], m['phone'] or '',
            m['club_affiliation'], m['club_type'],
            m['membership_tier'] or 'Standard',
            m['renewal_date'].strftime('%Y-%m-%d') if m['renewal_date'] else '',
            m['status'],
            m['joined_at'].strftime('%Y-%m-%d') if m['joined_at'] else ''
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=members.csv'}
    )


@admin_bp.route('/admin/reports/export/attendance')
@admin_required
def export_attendance():
    import csv, io
    from flask import Response
    cur = get_cursor()
    cur.execute("""
        SELECT e.title, e.event_date, e.location, e.category,
               m.name AS member_name, m.email, m.club_affiliation,
               a.marked_at
        FROM attendance a
        JOIN events e ON a.event_id=e.id
        JOIN members m ON a.member_id=m.id
        ORDER BY e.event_date DESC, m.name
    """)
    rows = cur.fetchall()
    cur.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Event','Date','Location','Category',
                     'Member','Email','Program','Marked At'])
    for r in rows:
        writer.writerow([
            r['title'],
            r['event_date'].strftime('%Y-%m-%d') if r['event_date'] else '',
            r['location'] or '',
            r['category'],
            r['member_name'], r['email'],
            r['club_affiliation'],
            r['marked_at'].strftime('%Y-%m-%d %H:%M') if r['marked_at'] else ''
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=attendance.csv'}
    )


@admin_bp.route('/admin/reports/export/renewals')
@admin_required
def export_renewals():
    import csv, io
    from flask import Response
    cur = get_cursor()
    cur.execute("""
        SELECT name, email, phone, club_affiliation,
               membership_tier, renewal_date, status
        FROM members
        WHERE renewal_date IS NOT NULL
        ORDER BY renewal_date ASC
    """)
    rows = cur.fetchall()
    cur.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name','Email','Phone','Program',
                     'Membership Tier','Renewal Date','Status'])
    for r in rows:
        writer.writerow([
            r['name'], r['email'], r['phone'] or '',
            r['club_affiliation'],
            r['membership_tier'] or 'Standard',
            r['renewal_date'].strftime('%Y-%m-%d') if r['renewal_date'] else '',
            r['status']
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=renewals.csv'}
    )



@admin_bp.route('/admin/members')
@admin_required
def admin_members():
    search = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    cur = get_cursor()

    query = 'SELECT * FROM members WHERE 1=1'
    params = []
    if search:
        query += ' AND (name LIKE %s OR email LIKE %s OR club_affiliation LIKE %s)'
        like = f'%{search}%'
        params.extend([like, like, like])
    if status_filter:
        query += ' AND status = %s'
        params.append(status_filter)
    query += ' ORDER BY joined_at DESC'

    cur.execute(query, params)
    members = cur.fetchall()
    cur.close()
    return render_template('admin_members.html', members=members, search=search, status_filter=status_filter)


@admin_bp.route('/admin/members/add', methods=['GET', 'POST'])
@admin_required
def admin_add_member():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        affiliation = request.form.get('club_affiliation', 'General').strip()
        status = request.form.get('status', 'active')
        member_club_type = request.form.get('club_type', 'sports')
        membership_tier = request.form.get('membership_tier', 'Standard').strip()
        renewal_date = request.form.get('renewal_date') or None
        error = validate_member_form(name, email, password, status, require_password=True)
        if error:
            flash(error, 'danger')
            return render_template('admin_member_form.html', member=None, action='add')

        try:
            hashed = generate_password_hash(password)
            cur = get_cursor()
            cur.execute(
                'INSERT INTO members (name, email, password_hash, phone, club_affiliation, status, club_type, membership_tier, renewal_date)'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (name, email, hashed, phone, affiliation, status, member_club_type, membership_tier, renewal_date)
            )
            commit()
            cur.close()
            flash('Member added successfully!', 'success')
            return redirect(url_for('admin.admin_members'))
        except Exception:
            flash('Email already exists.', 'danger')

    return render_template('admin_member_form.html', member=None, action='add')


@admin_bp.route('/admin/members/edit/<int:member_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_member(member_id):
    cur = get_cursor()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        affiliation = request.form.get('club_affiliation', 'General').strip()
        status = request.form.get('status', 'active')
        new_pass = request.form.get('password', '')
        error = validate_member_form(name, email, new_pass, status)
        if error:
            flash(error, 'danger')
            cur.execute('SELECT * FROM members WHERE id=%s', (member_id,))
            member = cur.fetchone()
            cur.close()
            return render_template('admin_member_form.html', member=member, action='edit')

        member_club_type = request.form.get('club_type', 'sports')
        membership_tier = request.form.get('membership_tier', 'Standard').strip()
        renewal_date = request.form.get('renewal_date') or None

        if new_pass:
            hashed = generate_password_hash(new_pass)
            cur.execute(
                'UPDATE members SET name=%s, email=%s, phone=%s, club_affiliation=%s, '
                'status=%s, password_hash=%s, club_type=%s, membership_tier=%s, renewal_date=%s WHERE id=%s',
                (name, email, phone, affiliation, status, hashed, member_club_type, membership_tier, renewal_date, member_id)
            )
        else:
            cur.execute(
                'UPDATE members SET name=%s, email=%s, phone=%s, club_affiliation=%s, '
                'status=%s, club_type=%s, membership_tier=%s, renewal_date=%s WHERE id=%s',
                (name, email, phone, affiliation, status, member_club_type, membership_tier, renewal_date, member_id)
            )
        commit()
        cur.close()
        flash('Member updated!', 'success')
        return redirect(url_for('admin.admin_members'))

    cur.execute('SELECT * FROM members WHERE id=%s', (member_id,))
    member = cur.fetchone()
    cur.close()
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('admin.admin_members'))
    return render_template('admin_member_form.html', member=member, action='edit')


@admin_bp.route('/admin/members/delete/<int:member_id>', methods=['POST'])
@admin_required
def admin_delete_member(member_id):
    cur = get_cursor()
    cur.execute('DELETE FROM members WHERE id=%s', (member_id,))
    commit()
    cur.close()
    flash('Member deleted.', 'info')
    return redirect(url_for('admin.admin_members'))


@admin_bp.route('/admin/members/approve/<int:member_id>', methods=['POST'])
@admin_required
def admin_approve_member(member_id):
    cur = get_cursor()
    cur.execute("UPDATE members SET status='active' WHERE id=%s AND status='pending'", (member_id,))
    commit()
    changed = cur.rowcount
    cur.close()

    if changed:
        flash('Member approved.', 'success')
    else:
        flash('Member was not pending or could not be found.', 'warning')
    return redirect(url_for('admin.admin_members', status='pending'))


@admin_bp.route('/admin/members/reject/<int:member_id>', methods=['POST'])
@admin_required
def admin_reject_member(member_id):
    cur = get_cursor()
    cur.execute("UPDATE members SET status='inactive' WHERE id=%s AND status='pending'", (member_id,))
    commit()
    changed = cur.rowcount
    cur.close()

    if changed:
        flash('Member rejected and marked inactive.', 'info')
    else:
        flash('Member was not pending or could not be found.', 'warning')
    return redirect(url_for('admin.admin_members', status='pending'))


@admin_bp.route('/admin/events')
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



@admin_bp.route('/admin/events/<int:event_id>/attendance', methods=['GET'])
@admin_required
def admin_event_attendance(event_id):
    cur = get_cursor()
    cur.execute('SELECT * FROM events WHERE id=%s', (event_id,))
    event = cur.fetchone()
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('admin.admin_events'))

    cur.execute("""
        SELECT m.id, m.name, m.email, m.club_affiliation,
               (SELECT COUNT(*) FROM attendance a WHERE a.event_id=%s AND a.member_id=m.id) AS attended
        FROM members m
        JOIN event_registrations er ON m.id=er.member_id
        WHERE er.event_id=%s
        ORDER BY m.name
    """, (event_id, event_id))
    members = cur.fetchall()

    cur.execute('SELECT COUNT(*) AS cnt FROM attendance WHERE event_id=%s', (event_id,))
    attended_count = cur.fetchone()['cnt']
    cur.close()

    return render_template('admin_event_attendance.html',
        event=event,
        members=members,
        attended_count=attended_count
    )


@admin_bp.route('/admin/events/<int:event_id>/attendance', methods=['POST'])
@admin_required
def admin_save_attendance(event_id):
    cur = get_cursor()
    cur.execute('SELECT id FROM events WHERE id=%s', (event_id,))
    if not cur.fetchone():
        flash('Event not found.', 'danger')
        return redirect(url_for('admin.admin_events'))

    attended_ids = request.form.getlist('attended')

    cur.execute('DELETE FROM attendance WHERE event_id=%s', (event_id,))

    for member_id in attended_ids:
        try:
            cur.execute(
                'INSERT IGNORE INTO attendance (event_id, member_id) VALUES (%s,%s)',
                (event_id, int(member_id))
            )
        except Exception:
            pass

    commit()
    cur.close()
    # Notify each attended member
    cur2 = get_cursor()
    cur2.execute('SELECT title, event_date FROM events WHERE id=%s', (event_id,))
    ev = cur2.fetchone()
    cur2.close()
    if ev:
        for mid in attended_ids:
            notify_member(int(mid),
                'Attendance Marked',
                f'Your attendance for "{ev["title"]}" on {ev["event_date"].strftime("%b %d, %Y") if ev["event_date"] else ""} has been recorded.',
                'success')
    flash(f'Attendance saved — {len(attended_ids)} member(s) marked present.', 'success')
    return redirect(url_for('admin.admin_event_attendance', event_id=event_id))

@admin_bp.route('/admin/events/add', methods=['GET', 'POST'])
@admin_required
def admin_add_event():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        event_date = request.form.get('event_date')
        event_time = request.form.get('event_time') or None
        location = request.form.get('location', '').strip()
        category = request.form.get('category', 'General').strip()
        max_att = parse_non_negative_int(request.form.get('max_attendees'), 0)
        status = request.form.get('status', 'scheduled')
        error = validate_event_form(title, event_date, max_att, status)
        if error:
            flash(error, 'danger')
            return render_template('admin_event_form.html', event=None, action='add')

        try:
            cur = get_cursor()
            cur.execute(
                'INSERT INTO events (title, description, event_date, event_time, location, category, max_attendees, status, created_by) '
                'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (title, description, event_date, event_time, location, category, max_att, status, session['user_id'])
            )
            commit()
            cur.close()
            flash('Event created!', 'success')
            return redirect(url_for('admin.admin_events'))
        except Exception as e:
            flash(f'Error creating event: {e}', 'danger')
    return render_template('admin_event_form.html', event=None, action='add')


@admin_bp.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_event(event_id):
    cur = get_cursor()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        event_date = request.form.get('event_date')
        event_time = request.form.get('event_time') or None
        location = request.form.get('location', '').strip()
        category = request.form.get('category', 'General').strip()
        max_att = parse_non_negative_int(request.form.get('max_attendees'), 0)
        status = request.form.get('status', 'scheduled')
        error = validate_event_form(title, event_date, max_att, status)
        if error:
            flash(error, 'danger')
            cur.execute('SELECT * FROM events WHERE id=%s', (event_id,))
            event = cur.fetchone()
            cur.close()
            return render_template('admin_event_form.html', event=event, action='edit')

        cur.execute(
            'UPDATE events SET title=%s, description=%s, event_date=%s, event_time=%s, '
            'location=%s, category=%s, max_attendees=%s, status=%s WHERE id=%s',
            (title, description, event_date, event_time, location, category, max_att, status, event_id)
        )
        commit()
        cur.close()
        flash('Event updated!', 'success')
        return redirect(url_for('admin.admin_events'))

    cur.execute('SELECT * FROM events WHERE id=%s', (event_id,))
    event = cur.fetchone()
    cur.close()
    return render_template('admin_event_form.html', event=event, action='edit')


@admin_bp.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    cur = get_cursor()
    cur.execute('DELETE FROM events WHERE id=%s', (event_id,))
    commit()
    cur.close()
    flash('Event deleted.', 'info')
    return redirect(url_for('admin.admin_events'))


@admin_bp.route('/admin/events/status/<int:event_id>/<status>', methods=['POST'])
@admin_required
def admin_update_event_status(event_id, status):
    if status not in VALID_EVENT_STATUSES:
        flash('Invalid event status.', 'danger')
        return redirect(url_for('admin.admin_events'))

    cur = get_cursor()
    cur.execute('UPDATE events SET status=%s WHERE id=%s', (status, event_id))
    commit()
    changed = cur.rowcount
    cur.close()

    if changed:
        flash(f'Event marked {status}.', 'success')
    else:
        flash('Event could not be found.', 'warning')
    return redirect(url_for('admin.admin_events'))


@admin_bp.route('/admin/announcements')
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


@admin_bp.route('/admin/announcements/add', methods=['GET', 'POST'])
@admin_required
def admin_add_announcement():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'medium')
        expires = request.form.get('expires_at') or None
        error = validate_announcement_form(title, content, priority)
        if error:
            flash(error, 'danger')
            return render_template('admin_announcement_form.html', announcement=None, action='add')

        cur = get_cursor()
        cur.execute(
            'INSERT INTO announcements (title, content, priority, created_by, expires_at) VALUES (%s,%s,%s,%s,%s)',
            (title, content, priority, session['user_id'], expires)
        )
        commit()
        cur.close()
        flash('Announcement posted!', 'success')
        return redirect(url_for('admin.admin_announcements'))
    return render_template('admin_announcement_form.html', announcement=None, action='add')


@admin_bp.route('/admin/announcements/edit/<int:ann_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_announcement(ann_id):
    cur = get_cursor()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'medium')
        expires = request.form.get('expires_at') or None
        error = validate_announcement_form(title, content, priority)
        if error:
            flash(error, 'danger')
            cur.execute('SELECT * FROM announcements WHERE id=%s', (ann_id,))
            ann = cur.fetchone()
            cur.close()
            return render_template('admin_announcement_form.html', announcement=ann, action='edit')

        cur.execute(
            'UPDATE announcements SET title=%s, content=%s, priority=%s, expires_at=%s '
            'WHERE id=%s',
            (title, content, priority, expires, ann_id)
        )
        commit()
        cur.close()
        flash('Announcement updated!', 'success')
        return redirect(url_for('admin.admin_announcements'))

    cur.execute('SELECT * FROM announcements WHERE id=%s', (ann_id,))
    ann = cur.fetchone()
    cur.close()
    return render_template('admin_announcement_form.html', announcement=ann, action='edit')


@admin_bp.route('/admin/announcements/delete/<int:ann_id>', methods=['POST'])
@admin_required
def admin_delete_announcement(ann_id):
    cur = get_cursor()
    cur.execute('DELETE FROM announcements WHERE id=%s', (ann_id,))
    commit()
    cur.close()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('admin.admin_announcements'))


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    cur = get_cursor()
    cur.execute("""
        SELECT DATE_FORMAT(MIN(joined_at),'%b') AS month, COUNT(*) AS count
        FROM members WHERE joined_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY YEAR(joined_at), MONTH(joined_at)
        ORDER BY YEAR(joined_at), MONTH(joined_at)
    """)
    signups = cur.fetchall()

    cur.execute('SELECT club_affiliation, COUNT(*) AS count FROM members GROUP BY club_affiliation')
    affiliations = cur.fetchall()
    cur.close()

    return jsonify({'signups': signups, 'affiliations': affiliations})
