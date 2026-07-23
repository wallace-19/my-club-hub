import re
import secrets
import hashlib

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import get_cursor, commit


def _fetch_user_by_email(role: str, email: str):
    cur = get_cursor()
    if role == 'admin':
        cur.execute('SELECT * FROM admins WHERE email = %s', (email,))
    else:
        cur.execute('SELECT * FROM members WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()
    return user



auth_bp = Blueprint('auth', __name__)
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def is_valid_email(email):
    return bool(EMAIL_RE.match(email or ''))


def is_strong_enough_password(password):
    return len(password or '') >= 8


def _make_token():
    # URL-safe reset token
    return secrets.token_urlsafe(32)


def _hash_token(token: str) -> str:
    # Store only a hash of the token
    return hashlib.sha256(token.encode('utf-8')).hexdigest()





@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'member')

        if role not in {'admin', 'member'}:
            flash('Invalid login role.', 'danger')
            return render_template('login.html', show_admin_tab=False)

        if not is_valid_email(email) or not password:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', show_admin_tab=False)

        cur = get_cursor()
        if role == 'admin':
            cur.execute('SELECT * FROM admins WHERE email = %s', (email,))
        else:
            cur.execute('SELECT * FROM members WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()

        if role == 'member' and user and user.get('status') != 'active':
            flash('Your account is not active. Please contact an administrator.', 'warning')
            return render_template('login.html', show_admin_tab=False)

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = role
            session['club_type'] = user.get('club_type', 'sports')
            session['club_name'] = user.get('club_name', 'My Club')
            session['profile_pic'] = user.get('profile_pic')
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('admin.admin_dashboard' if role == 'admin' else 'member.member_dashboard'))
        flash('Invalid email or password.', 'danger')

    return render_template('login.html', show_admin_tab=False)


@auth_bp.route('/club-admin-portal-9x7k', methods=['GET', 'POST'])
def admin_login():
    """Secret admin login URL — not linked anywhere on the site."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'admin')
        if role not in {'admin', 'member'}:
            flash('Invalid login role.', 'danger')
            return render_template('login.html', show_admin_tab=True)
        if not is_valid_email(email) or not password:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', show_admin_tab=True)
        cur = get_cursor()
        if role == 'admin':
            cur.execute('SELECT * FROM admins WHERE email = %s', (email,))
        else:
            cur.execute('SELECT * FROM members WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        if role == 'member' and user and user.get('status') != 'active':
            flash('Your account is not active.', 'warning')
            return render_template('login.html', show_admin_tab=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = role
            session['club_type'] = user.get('club_type', 'sports')
            session['club_name'] = user.get('club_name', 'My Club')
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('admin.admin_dashboard' if role == 'admin' else 'member.member_dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', show_admin_tab=True)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Get club info from admin table to show on registration page
    cur = get_cursor()
    cur.execute('SELECT club_name, club_type FROM admins LIMIT 1')
    club_info = cur.fetchone()
    cur.close()
    club_name = club_info['club_name'] if club_info else 'ClubHub'
    club_type = club_info['club_type'] if club_info else 'sports'

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        affiliation = request.form.get('club_affiliation', 'General').strip()
        member_club_type = request.form.get('club_type', club_type)

        if not all([name, email, password]):
            flash('Name, email, and password are required.', 'danger')
            return render_template('register.html', club_name=club_name, club_type=club_type)

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html', club_name=club_name, club_type=club_type)

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', club_name=club_name, club_type=club_type)

        if not is_strong_enough_password(password):
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('register.html', club_name=club_name, club_type=club_type)

        hashed = generate_password_hash(password)
        try:
            cur = get_cursor()
            cur.execute(
                'INSERT INTO members (name, email, password_hash, phone, club_affiliation, club_type, status) '
                'VALUES (%s,%s,%s,%s,%s,%s,%s)',
                (name, email, hashed, phone, affiliation, member_club_type, 'pending')
            )
            commit()
            cur.close()
            flash('Account created! An administrator must approve it before you can log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            flash('Email already registered.', 'danger')

    return render_template('register.html', club_name=club_name, club_type=club_type)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'member')

        if role not in {'admin', 'member'}:
            flash('Invalid role.', 'danger')
            return render_template('forgot_password.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('forgot_password.html')

        user = _fetch_user_by_email(role, email)

        # Always show a generic message to prevent account enumeration.
        flash('If that email exists, a reset code has been generated.', 'success')

        # If user does not exist, do not create token.
        if not user:
            return render_template('forgot_password.html')

        token = _make_token()
        token_hash = _hash_token(token)

        cur = get_cursor()
        cur.execute(
            'INSERT INTO password_reset_tokens (email, role, token_hash, expires_at, used_at) '
            'VALUES (%s, %s, %s, NOW() + INTERVAL 30 MINUTE, NULL)',
            (email, role, token_hash)
        )
        commit()
        cur.close()

        # Since there is no email service in this app, show the reset link.
        reset_link = url_for('auth.reset_password', token=token, _external=True)
        flash(f'Reset link (use in dev): {reset_link}', 'info')

        return render_template('forgot_password.html')

    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_hash = _hash_token(token)

    # Look up token validity
    cur = get_cursor()
    cur.execute(
        'SELECT role, email, expires_at, used_at '
        'FROM password_reset_tokens '
        'WHERE token_hash = %s',
        (token_hash,)
    )
    row = cur.fetchone()
    cur.close()

    reset_ok = False
    if row and row.get('used_at') is None:
        # MySQL returns expires_at as string/datetime depending on driver; compare safely in SQL not python.
        # Simpler: do a fresh check in SQL.
        cur = get_cursor()
        cur.execute(
            'SELECT role, email '
            'FROM password_reset_tokens '
            'WHERE token_hash = %s '
            'AND used_at IS NULL '
            'AND expires_at > NOW()',
            (token_hash,)
        )
        valid_row = cur.fetchone()
        cur.close()
        if valid_row:
            reset_ok = True

    if request.method == 'POST':
        if not reset_ok:
            flash('This reset code is invalid or has expired.', 'danger')
            return render_template('reset_password.html', reset_ok=False, token=token)

        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', reset_ok=True, token=token)

        if not is_strong_enough_password(new_password):
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('reset_password.html', reset_ok=True, token=token)

        # Fetch valid row again to get email/role
        cur = get_cursor()
        cur.execute(
            'SELECT role, email '
            'FROM password_reset_tokens '
            'WHERE token_hash = %s '
            'AND used_at IS NULL '
            'AND expires_at > NOW()',
            (token_hash,)
        )
        valid_row = cur.fetchone()

        if not valid_row:
            cur.close()
            flash('This reset code is invalid or has expired.', 'danger')
            return render_template('reset_password.html', reset_ok=False, token=token)

        role = valid_row['role']
        email = valid_row['email']

        hashed = generate_password_hash(new_password)

        if role == 'admin':
            cur.execute('UPDATE admins SET password_hash=%s WHERE email=%s', (hashed, email))
        else:
            cur.execute(
                'UPDATE members SET password_hash=%s WHERE email=%s',
                (hashed, email)
            )

        cur.execute(
            'UPDATE password_reset_tokens SET used_at=NOW() '
            'WHERE token_hash=%s AND used_at IS NULL',
            (token_hash,)
        )

        commit()
        cur.close()

        flash('Password updated successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', reset_ok=reset_ok, token=token)


@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():

    cur = get_cursor()
    cur.execute('SELECT COUNT(*) AS cnt FROM admins')
    count = cur.fetchone()['cnt']
    cur.close()

    if count > 0:
        flash('Setup already complete.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not is_valid_email(email) or not is_strong_enough_password(password):
            flash('Enter a name, a valid email, and a password of at least 8 characters.', 'danger')
            return render_template('setup.html')

        hashed = generate_password_hash(password)
        club_name = request.form.get("club_name", "").strip() or "My Club"
        club_type = request.form.get("club_type", "sports")
        if club_type not in {"sports", "private", "campus", "fitness"}:
            club_type = "sports"
        cur = get_cursor()
        cur.execute('INSERT INTO admins (name, email, password_hash, club_name, club_type) VALUES (%s,%s,%s,%s,%s)',
                    (name, email, hashed, club_name, club_type))
        commit()
        cur.close()
        flash('Admin account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('setup.html')
