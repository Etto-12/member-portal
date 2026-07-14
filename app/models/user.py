from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Roles:
    # admin    = full admin access
    # user     = normal member portal user
    # bahagian = can submit membership applications for Bahagian
    # cawangan = can submit membership applications for Cawangan
    role = db.Column(db.String(20), default="user", nullable=False)

    # For Bahagian / Cawangan membership application accounts
    bahagian_id = db.Column(db.Integer, db.ForeignKey("bahagian.id"), nullable=True)
    bahagian_name = db.Column(db.String(150), nullable=True)
    cawangan_name = db.Column(db.String(150), nullable=True)

    bahagian_ref = db.relationship(
        "Bahagian",
        foreign_keys=[bahagian_id],
        lazy="joined"
    )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_super_admin(self):
        return self.username.strip().lower() == "upko"

    @property
    def is_application_user(self):
        return self.role in ("bahagian", "cawangan")

    @property
    def display_role(self):
        if self.role == "admin":
            return "ADMIN"
        if self.role == "bahagian":
            return "BAHAGIAN"
        if self.role == "cawangan":
            return "CAWANGAN"
        return "USER"
