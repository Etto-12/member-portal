from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash

from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            # ✅ Send everyone to dashboard
            return redirect(url_for("admin.dashboard"))

        error = "Invalid username or password"

    return render_template("auth/login.html", error=error)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
