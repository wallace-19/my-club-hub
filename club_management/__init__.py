import os
import hmac
import secrets

from flask import Flask, abort, request, session, render_template, redirect, url_for
from dotenv import load_dotenv

from .extensions import mysql
from .filters import format_date, format_time


def create_app():
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

    app = Flask(__name__, template_folder='templates', static_folder='static')
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key or secret_key in {'change-me-to-a-secure-random-string', 'club-mgmt-secret-2024-change-in-prod'}:
        raise RuntimeError('SECRET_KEY must be set to a strong unique value in .env')
    app.secret_key = secret_key

    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'club_management')
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    mysql.init_app(app)

    from .auth import auth_bp
    from .member import member_bp
    from .admin import admin_bp
    from .pages import pages_bp  

    app.register_blueprint(auth_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pages_bp) 

    app.add_template_filter(format_date, 'format_date')
    app.add_template_filter(format_time, 'format_time')

    @app.before_request
    def validate_csrf_token():
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return

        session_token = session.get('_csrf_token')
        request_token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        if not session_token or not request_token or not hmac.compare_digest(session_token, request_token):
            abort(400, description='Invalid CSRF token.')

    @app.context_processor
    def inject_csrf_token():
        def csrf_token():
            token = session.get('_csrf_token')
            if not token:
                token = secrets.token_urlsafe(32)
                session['_csrf_token'] = token
            return token

        return {'csrf_token': csrf_token}

    @app.route('/')
    def landing():
        if 'user_id' in session:
            if session.get('role') == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('member.member_dashboard'))
        return render_template('landing.html')



    return app