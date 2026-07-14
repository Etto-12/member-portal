from flask import Blueprint, render_template
from flask_login import login_required
from app.models.member import Member
from app.extensions import db
from app.models.location import Bahagian, Dun

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
@login_required
def index():
    total_members = db.session.query(Member).count()
    active_members = db.session.query(Member).filter(Member.memberstatus == "Aktif").count()
    total_bahagian = db.session.query(Bahagian.id).count()
    total_dun = db.session.query(Dun.id).count()

    return render_template(
        "public/dashboard.html",
        total_members=total_members,
        active_members=active_members,
        total_bahagian=total_bahagian,
        total_dun=total_dun
    )
