from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.user import User
from app.utils.permissions import admin_required
from werkzeug.security import generate_password_hash

admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/admin/users")

@admin_users_bp.route("/")
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template("admin/users.html", users=users)

@admin_users_bp.route("/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_user():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            email=request.form["email"],
            password_hash=generate_password_hash(request.form["password"]),
            role=request.form["role"]
        )
        db.session.add(user)
        db.session.commit()
        flash("User created", "success")
        return redirect(url_for("admin_users.list_users"))

    return render_template("admin/user_form.html")

@admin_users_bp.route("/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted", "warning")
    return redirect(url_for("admin_users.list_users"))

@admin_users_bp.route("/update/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)

    user.username = request.form.get("username")
    user.role = request.form.get("role")

    db.session.commit()
    flash("User updated", "success")
    return redirect(url_for("admin_users.list_users"))
