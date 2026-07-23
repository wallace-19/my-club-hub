from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps

pages_bp = Blueprint('pages', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@pages_bp.route('/clubs/sports')
@login_required
def sports_clubs():
    return render_template('pages/sports_clubs.html')

@pages_bp.route('/clubs/private')
@login_required
def private_members():
    return render_template('pages/private_members.html')

@pages_bp.route('/clubs/campus')
@login_required
def campus_clubs():
    return render_template('pages/campus_clubs.html')

@pages_bp.route('/clubs/fitness')
@login_required
def fitness_studios():
    return render_template('pages/fitness_studios.html')

@pages_bp.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')

@pages_bp.route('/terms')
def terms():
    return render_template('pages/terms.html')
