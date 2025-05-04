from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from shared.models import db, Character
from player_app.app import mail
import secrets

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("character.character_view", char_id=current_user.id))
    return render_template("index.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        char = Character.query.filter_by(email=request.form["email"]).first()
        if char and char.check_password(request.form["password"]):
            login_user(char)
            return redirect(url_for("character.character_view", char_id=char.id))
        flash("Invalid credentials.")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/reset", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        char = Character.query.filter_by(email=request.form["email"]).first()
        if char:
            new_pw = secrets.token_urlsafe(8)
            char.set_password(new_pw)
            db.session.commit()
            msg = Message("Your New Password", recipients=[char.email])
            msg.body = f"Your new password is: {new_pw}"
            mail.send(msg)
            flash("New password sent to your email.")
        else:
            flash("Email not found.")
    return render_template("reset.html")
