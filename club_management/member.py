
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from .decorators import member_required
from .extensions import get_cursor, commit, rollback

member_bp = Blueprint('member', __name__)



def create_notification(member_id, title, message, notif_type='info'):
    """Helper to insert a notification for a member."""
    try:
        cur = get_cursor()
        cur.execute(
            'INSERT INTO notifications (member_id, title, message, type) VALUES (%s,%s,%s,%s)',
            (member_id, title, message, notif_type)
        )
        commit()
        cur.close()
    except Exception:
        pass


@member_bp.route('/notifications')
@member_required
def notifications():
    cur = get_cursor()
    cur.execute("""
        SELECT * FROM notifications
        WHERE member_id=%s
        ORDER BY created_at DESC LIMIT 50
    """, (session['user_id'],))
    items = cur.fetchall()

    # Mark all as read
    cur.execute("""
        UPDATE notifications SET is_read=1
        WHERE member_id=%s AND is_read=0
    """, (session['user_id'],))
    commit()
    cur.close()
    return render_template('notifications.html', notifications=items)


@member_bp.route('/notifications/dismiss/<int:notif_id>', methods=['POST'])
@member_required
def dismiss_notification(notif_id):
    cur = get_cursor()
    cur.execute(
        'DELETE FROM notifications WHERE id=%s AND member_id=%s',
        (notif_id, session['user_id'])
    )
    commit()
    cur.close()
    return redirect(url_for('member.notifications'))


@member_bp.route('/notifications/dismiss-all', methods=['POST'])
@member_required
def dismiss_all_notifications():
    cur = get_cursor()
    cur.execute('DELETE FROM notifications WHERE member_id=%s', (session['user_id'],))
    commit()
    cur.close()
    flash('All notifications cleared.', 'success')
    return redirect(url_for('member.notifications'))

import os


@member_bp.route('/dashboard')
@member_required
def member_dashboard():
    cur = get_cursor()
    club_type = session.get('club_type', 'sports')
    member_id = session['user_id']

    # ── Common queries ──────────────────────────────────────────
    cur.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM event_registrations r WHERE r.event_id = e.id) AS registered_count
        FROM events e
        WHERE e.event_date >= CURDATE() AND e.status = 'scheduled'
        ORDER BY e.event_date ASC LIMIT 6
    """)
    upcoming_events = cur.fetchall()

    cur.execute("""
        SELECT a.*, ad.name AS author
        FROM announcements a
        LEFT JOIN admins ad ON a.created_by = ad.id
        WHERE (a.expires_at IS NULL OR a.expires_at >= CURDATE())
        ORDER BY a.created_at DESC LIMIT 5
    """)
    announcements = cur.fetchall()

    cur.execute("""
        SELECT e.* FROM events e
        JOIN event_registrations er ON e.id = er.event_id
        WHERE er.member_id = %s
          AND e.event_date >= CURDATE()
          AND e.status IN ('scheduled', 'cancelled')
        ORDER BY e.event_date ASC
    """, (member_id,))
    my_events = cur.fetchall()

    cur.execute('SELECT * FROM members WHERE id=%s', (member_id,))
    member = cur.fetchone()

    # ── Club-type specific queries ──────────────────────────────
    extra = {}

    if club_type == 'sports':
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM event_registrations er
            JOIN events e ON er.event_id = e.id
            WHERE er.member_id = %s
        """, (member_id,))
        extra['total_sessions_registered'] = cur.fetchone()['cnt']

        cur.execute("""
            SELECT COUNT(*) AS cnt FROM attendance
            WHERE member_id = %s
        """, (member_id,))
        extra['sessions_attended'] = cur.fetchone()['cnt']

        cur.execute("""
            SELECT e.title, e.event_date, e.location, e.category
            FROM attendance a JOIN events e ON a.event_id = e.id
            WHERE a.member_id = %s
            ORDER BY e.event_date DESC LIMIT 5
        """, (member_id,))
        extra['recent_attendance'] = cur.fetchall()

    elif club_type == 'private':
        extra['membership_tier'] = member.get('membership_tier', 'Standard') if member else 'Standard'
        extra['renewal_date'] = member.get('renewal_date') if member else None

        cur.execute("""
            SELECT e.*, COUNT(er.id) AS registered_count
            FROM events e LEFT JOIN event_registrations er ON e.id = er.event_id
            WHERE e.event_date >= CURDATE() AND e.status = 'scheduled'
            GROUP BY e.id ORDER BY e.event_date ASC LIMIT 3
        """)
        extra['exclusive_events'] = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) AS cnt FROM event_registrations
            WHERE member_id = %s
        """, (member_id,))
        extra['events_attended'] = cur.fetchone()['cnt']

    elif club_type == 'campus':
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM event_registrations er
            JOIN events e ON er.event_id = e.id
            WHERE er.member_id = %s
            AND YEAR(e.event_date) = YEAR(CURDATE())
        """, (member_id,))
        extra['meetings_this_semester'] = cur.fetchone()['cnt']

        cur.execute("""
            SELECT COUNT(*) AS cnt FROM events
            WHERE event_date >= CURDATE() AND status = 'scheduled'
        """)
        extra['upcoming_meetings'] = cur.fetchone()['cnt']

    elif club_type == 'fitness':
        cur.execute("""
            SELECT e.*, COUNT(er.id) AS check_ins
            FROM events e LEFT JOIN event_registrations er ON e.id = er.event_id
            WHERE e.event_date = CURDATE()
            GROUP BY e.id ORDER BY e.event_time ASC
        """)
        extra['todays_classes'] = cur.fetchall()

        extra['membership_plan'] = member.get('membership_tier', 'Standard') if member else 'Standard'
        extra['renewal_date'] = member.get('renewal_date') if member else None

        cur.execute("""
            SELECT COUNT(*) AS cnt FROM event_registrations er
            JOIN events e ON er.event_id = e.id
            WHERE er.member_id = %s
            AND MONTH(e.event_date) = MONTH(CURDATE())
        """, (member_id,))
        extra['classes_this_month'] = cur.fetchone()['cnt']

    cur.close()

    template_map = {
        'sports':  'member_dashboard_sports.html',
        'private': 'member_dashboard_private.html',
        'campus':  'member_dashboard_campus.html',
        'fitness': 'member_dashboard_fitness.html',
    }
    template = template_map.get(club_type, 'member_dashboard.html')
    return render_template(template,
        upcoming_events=upcoming_events,
        announcements=announcements,
        my_events=my_events,
        member=member,
        **extra
    )


@member_bp.route('/events')
@member_required
def events():
    cur = get_cursor()
    cur.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM event_registrations r WHERE r.event_id = e.id) AS registered_count,
               (SELECT COUNT(*) FROM event_registrations r WHERE r.event_id = e.id AND r.member_id = %s) AS is_registered
        FROM events e
        WHERE e.event_date >= CURDATE() AND e.status = 'scheduled'
        ORDER BY e.event_date ASC
    """, (session['user_id'],))
    all_events = cur.fetchall()
    cur.close()
    return render_template('events.html', events=all_events)


@member_bp.route('/events/register/<int:event_id>', methods=['POST'])
@member_required
def register_event(event_id):
    cur = None
    try:
        cur = get_cursor()
        cur.execute(
            "SELECT * FROM events WHERE id = %s AND event_date >= CURDATE() AND status = 'scheduled' FOR UPDATE",
            (event_id,)
        )
        event = cur.fetchone()
        if not event:
            rollback()
            flash('Event is not available for registration.', 'danger')
            return redirect(url_for('member.events'))

        cur.execute('SELECT COUNT(*) AS cnt FROM event_registrations WHERE event_id = %s', (event_id,))
        registered_count = cur.fetchone()['cnt']
        if event['max_attendees'] and registered_count >= event['max_attendees']:
            rollback()
            flash('This event is already full.', 'warning')
            return redirect(url_for('member.events'))

        cur.execute(
            'INSERT IGNORE INTO event_registrations (event_id, member_id) VALUES (%s, %s)',
            (event_id, session['user_id'])
        )
        commit()
        if cur.rowcount:
            # Get event details for notification
            cur.execute('SELECT title, event_date FROM events WHERE id=%s', (event_id,))
            ev = cur.fetchone()
            if ev:
                create_notification(
                    session['user_id'],
                    'Event Registration Confirmed',
                    f'You are registered for "{ev["title"]}" on {ev["event_date"].strftime("%b %d, %Y") if ev["event_date"] else ""}.',
                    'success'
                )
            flash('Successfully registered for event!', 'success')
        else:
            flash('You are already registered for this event.', 'info')
    except Exception:
        rollback()
        flash('Could not register for event.', 'danger')
    finally:
        if cur:
            cur.close()
    return redirect(url_for('member.events'))


@member_bp.route('/events/unregister/<int:event_id>', methods=['POST'])
@member_required
def unregister_event(event_id):
    cur = get_cursor()
    cur.execute(
        'DELETE FROM event_registrations WHERE event_id = %s AND member_id = %s',
        (event_id, session['user_id'])
    )
    commit()
    cur.close()
    flash('Unregistered from event.', 'info')
    return redirect(url_for('member.events'))


@member_bp.route('/announcements')
@member_required
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


@member_bp.route('/profile', methods=['GET', 'POST'])
@member_required
def profile():
    cur = get_cursor()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        affiliation = request.form.get('club_affiliation', '').strip()
        bio = request.form.get('profile_bio', '').strip()
        if not name:
            flash('Name is required.', 'danger')
        else:
            # ── Handle profile picture upload ───────────────────
            pic_file = request.files.get('profile_pic')
            new_pic_filename = None
            if pic_file and pic_file.filename:
                original_name = pic_file.filename
                ext = os.path.splitext(original_name)[1].lower()
                if ext not in {'.png', '.jpg', '.jpeg'}:
                    flash('Only .png and .jpeg files are allowed for profile pictures.', 'danger')
                    cur.close()
                    return redirect(url_for('member.profile'))
                # Securely rename using member ID, normalise jpeg → jpg
                safe_ext = '.jpg' if ext in {'.jpg', '.jpeg'} else '.png'
                new_pic_filename = f"member_{session['user_id']}{safe_ext}"
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'profile_pics')
                os.makedirs(upload_dir, exist_ok=True)
                pic_file.save(os.path.join(upload_dir, new_pic_filename))

            # ── Update member record ────────────────────────────
            if new_pic_filename:
                cur.execute("""
                    UPDATE members SET name=%s, phone=%s, club_affiliation=%s, profile_bio=%s, profile_pic=%s
                    WHERE id=%s
                """, (name, phone, affiliation, bio, new_pic_filename, session['user_id']))
                session['profile_pic'] = new_pic_filename
            else:
                cur.execute("""
                    UPDATE members SET name=%s, phone=%s, club_affiliation=%s, profile_bio=%s
                    WHERE id=%s
                """, (name, phone, affiliation, bio, session['user_id']))
            commit()
            session['user_name'] = name
            flash('Profile updated!', 'success')

    cur.execute('SELECT * FROM members WHERE id=%s', (session['user_id'],))
    member = cur.fetchone()

    # Attendance stats
    cur.execute("""
        SELECT COUNT(*) AS cnt FROM event_registrations
        WHERE member_id=%s
    """, (session['user_id'],))
    sessions_registered = cur.fetchone()['cnt']

    cur.execute("""
        SELECT COUNT(*) AS cnt FROM attendance
        WHERE member_id=%s
    """, (session['user_id'],))
    sessions_attended = cur.fetchone()['cnt']

    cur.execute("""
        SELECT COUNT(*) AS cnt FROM event_registrations er
        JOIN events e ON er.event_id=e.id
        WHERE er.member_id=%s AND e.event_date >= CURDATE()
    """, (session['user_id'],))
    upcoming_count = cur.fetchone()['cnt']

    cur.close()

    # Affiliation options by club type
    club_type = session.get('club_type', 'sports')
    affiliation_options = {
        'sports':  ['General','Running','Swimming','Tennis','Football','Basketball','Athletics','Rowing','Cycling'],
        'private': ['Full Member','Associate Member','Honorary Member','Corporate Member','Social Member'],
        'campus':  ['General','Arts','Science','Business','Engineering','Medicine','Law','Education'],
        'fitness': ['General','Yoga','CrossFit','Cardio','Weights','Pilates','Zumba','HIIT'],
    }.get(club_type, ['General'])

    return render_template('profile.html',
        member=member,
        sessions_registered=sessions_registered,
        sessions_attended=sessions_attended,
        upcoming_count=upcoming_count,
        affiliation_options=affiliation_options,
        club_type=club_type
    )
