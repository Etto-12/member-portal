from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..models.admin_user import AdminUser

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = AdminUser.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard"))

        flash("Invalid login", "danger")
    return render_template("admin_login.html")

@auth_bp.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("auth.admin_login"))
