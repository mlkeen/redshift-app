from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import SignatureExpired
from flask_mail import Message
from .models import User
from . import db, mail, serializer
from .models import GameState

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    state = GameState.query.get(1)
    now = datetime.now()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.")
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        token = serializer.dumps(email, salt='email-confirm')
        verify_link = url_for('auth.verify_email', token=token, _external=True)

        msg = Message(
            subject="Confirm your Redshift account",
            sender="redshift_game@fastmail.com",  # TEMP hardcoded fallback
            recipients=[email]
        )
        msg.body = f"Hello {username},\n\nClick to verify your email:\n{verify_link}"
        mail.send(msg)

        flash("Registration successful. Please check your email to verify your account.")
        return redirect(url_for('auth.login'))

    return render_template('register.html', state=state, now=now)
    
@auth_bp.route('/verify/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash("Verification link expired.")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()
        flash("Email verified! You may now log in.")
    else:
        flash("Account not found.")

    return redirect(url_for('auth.login'))




@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    state = GameState.query.get(1)
    now = datetime.now()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid username or password")

    return render_template('login.html', state=state, now=now)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


