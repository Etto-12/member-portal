from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, jsonify, Response
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import or_
from app.extensions import db
from app.models.member import Member
from app.models.user import User
from werkzeug.security import generate_password_hash
from app.models.location import Parlimen, Daerah, Bahagian, Dun, Cawangan, PusatMengundi
import csv
from io import StringIO

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# =========================
# ADMIN ACCESS DECORATORS
# =========================
def member_editor_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)

        if not current_user.is_admin:
            abort(403)

        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)

        if not current_user.is_admin:
            abort(403)

        return f(*args, **kwargs)

    return wrapper


def super_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)

        if not current_user.is_admin:
            abort(403)

        if not current_user.is_super_admin and current_user.username.strip().lower() != "upko":
            abort(403)

        return f(*args, **kwargs)

    return wrapper


# =========================
# LOCATION VALIDATION HELPER
# =========================
def validate_location_combo(parlimen_name: str, daerah_id: int) -> bool:
    if not parlimen_name or not daerah_id:
        return False

    parlimen_name = parlimen_name.strip().upper()

    p = Parlimen.query.filter(
        db.func.upper(Parlimen.name) == parlimen_name
    ).first()
    if not p:
        return False

    d = Daerah.query.filter_by(id=daerah_id, parlimen_id=p.id).first()
    if not d:
        return False

    return True


# =========================
# CSV HELPER
# =========================
def clean_csv_value(value):
    if value is None:
        return ""
    return str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()


# =========================
# DASHBOARD
# =========================
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    selected_bahagian_id = request.args.get("bahagian_id", type=int)
    selected_dun_id = request.args.get("dun_id", type=int)
    selected_cawangan = (request.args.get("cawangan") or "").strip()
    view_mode = (request.args.get("view") or "bahagian").strip().lower()

    if view_mode not in ("bahagian", "dun", "cawangan"):
        view_mode = "bahagian"

    base_query = Member.query

    if selected_bahagian_id:
        base_query = base_query.filter(Member.bahagian_id == selected_bahagian_id)

    if selected_dun_id:
        base_query = base_query.filter(Member.dun_id == selected_dun_id)

    if selected_cawangan:
        base_query = base_query.filter(Member.cawangan.ilike(selected_cawangan))

    total_members = base_query.count()
    active_members = base_query.filter(Member.memberstatus == "Aktif").count()
    non_active_members = total_members - active_members

    selected_bahagian = Bahagian.query.get(selected_bahagian_id) if selected_bahagian_id else None
    selected_dun = Dun.query.get(selected_dun_id) if selected_dun_id else None

    # ===== Bahagian breakdown =====
    bahagian_query = (
        db.session.query(
            Bahagian.id.label("id"),
            Bahagian.name.label("name"),
            db.func.count(Member.id).label("total"),
            db.func.sum(
                db.case((Member.memberstatus == "Aktif", 1), else_=0)
            ).label("active")
        )
        .join(Member, Member.bahagian_id == Bahagian.id)
    )

    if selected_dun_id:
        bahagian_query = bahagian_query.filter(Member.dun_id == selected_dun_id)

    if selected_cawangan:
        bahagian_query = bahagian_query.filter(Member.cawangan.ilike(selected_cawangan))

    bahagian_breakdown = (
        bahagian_query
        .group_by(Bahagian.id, Bahagian.name)
        .order_by(db.func.count(Member.id).desc(), Bahagian.name.asc())
        .all()
    )

    bahagian_rows = []
    for row in bahagian_breakdown:
        total = row.total or 0
        active = row.active or 0
        bahagian_rows.append({
            "id": row.id,
            "name": row.name,
            "total": total,
            "active": active,
            "inactive": total - active,
            "link": url_for(
                "admin.dashboard",
                bahagian_id=row.id,
                view="dun"
            )
        })

    # ===== DUN breakdown =====
    dun_query = (
        db.session.query(
            Dun.id.label("id"),
            Dun.name.label("name"),
            db.func.count(Member.id).label("total"),
            db.func.sum(
                db.case((Member.memberstatus == "Aktif", 1), else_=0)
            ).label("active")
        )
        .join(Member, Member.dun_id == Dun.id)
    )

    if selected_bahagian_id:
        dun_query = dun_query.filter(Member.bahagian_id == selected_bahagian_id)

    if selected_cawangan:
        dun_query = dun_query.filter(Member.cawangan.ilike(selected_cawangan))

    dun_breakdown = (
        dun_query
        .group_by(Dun.id, Dun.name)
        .order_by(db.func.count(Member.id).desc(), Dun.name.asc())
        .all()
    )

    dun_rows = []
    for row in dun_breakdown:
        total = row.total or 0
        active = row.active or 0
        dun_rows.append({
            "id": row.id,
            "name": row.name,
            "total": total,
            "active": active,
            "inactive": total - active,
            "link": url_for(
                "admin.dashboard",
                bahagian_id=selected_bahagian_id,
                dun_id=row.id,
                view="cawangan"
            )
        })

    # ===== Cawangan breakdown =====
    cawangan_query = (
        db.session.query(
            Member.cawangan.label("name"),
            db.func.count(Member.id).label("total"),
            db.func.sum(
                db.case((Member.memberstatus == "Aktif", 1), else_=0)
            ).label("active")
        )
        .filter(Member.cawangan.isnot(None))
        .filter(Member.cawangan != "")
    )

    if selected_bahagian_id:
        cawangan_query = cawangan_query.filter(Member.bahagian_id == selected_bahagian_id)

    if selected_dun_id:
        cawangan_query = cawangan_query.filter(Member.dun_id == selected_dun_id)

    if selected_cawangan:
        cawangan_query = cawangan_query.filter(Member.cawangan.ilike(selected_cawangan))

    cawangan_breakdown = (
        cawangan_query
        .group_by(Member.cawangan)
        .order_by(db.func.count(Member.id).desc(), Member.cawangan.asc())
        .all()
    )

    cawangan_rows = []
    for row in cawangan_breakdown:
        total = row.total or 0
        active = row.active or 0
        cawangan_rows.append({
            "name": row.name,
            "total": total,
            "active": active,
            "inactive": total - active,
            "link": url_for(
                "admin.members",
                bahagian_id=selected_bahagian_id,
                dun_id=selected_dun_id,
                cawangan=row.name
            )
        })

    total_cawangan = len(cawangan_rows)

    return render_template(
        "admin/dashboard.html",
        total_members=total_members,
        active_members=active_members,
        non_active_members=non_active_members,
        total_bahagian=Bahagian.query.count(),
        total_dun=Dun.query.count(),
        total_cawangan=total_cawangan,
        bahagians=Bahagian.query.order_by(Bahagian.name).all(),
        duns=Dun.query.order_by(Dun.name).all(),
        selected_bahagian_id=selected_bahagian_id,
        selected_dun_id=selected_dun_id,
        selected_cawangan=selected_cawangan,
        selected_bahagian=selected_bahagian,
        selected_dun=selected_dun,
        view_mode=view_mode,
        bahagian_rows=bahagian_rows,
        dun_rows=dun_rows,
        cawangan_rows=cawangan_rows,
    )


# =========================
# VIEW MEMBERS
# =========================
@admin_bp.route("/members")
@login_required
def members():
    page = request.args.get("page", 1, type=int)

    search = request.args.get("q", "").strip()
    parlimen = request.args.get("parlimen", "").strip()
    daerah_id = request.args.get("daerah_id", type=int)
    dun_id = request.args.get("dun_id", type=int)
    bahagian_id = request.args.get("bahagian_id", type=int)
    cawangan = request.args.get("cawangan", "").strip()

    query = Member.query

    if search:
        filters = [
            Member.ic.ilike(f"%{search}%"),
            Member.fullname.ilike(f"%{search}%")
        ]

        if search.isdigit():
            try:
                noid_value = int(search)
                if -2147483648 <= noid_value <= 2147483647:
                    filters.append(Member.noid == noid_value)
            except ValueError:
                pass

        query = query.filter(or_(*filters))

    if parlimen:
        query = query.filter(Member.parlimen == parlimen)

    if daerah_id:
        query = query.filter(Member.daerah_id == daerah_id)

    if dun_id:
        query = query.filter(Member.dun_id == dun_id)

    if bahagian_id:
        query = query.filter(Member.bahagian_id == bahagian_id)

    if cawangan:
        query = query.filter(Member.cawangan.ilike(f"%{cawangan}%"))

    pagination = query.order_by(Member.noid.asc()).paginate(
        page=page,
        per_page=25,
        error_out=False
    )

    return render_template(
        "admin/members.html",
        members=pagination.items,
        pagination=pagination,
        parlimens=Parlimen.query.order_by(Parlimen.name).all(),
        daerahs=Daerah.query.order_by(Daerah.name).all(),
        duns=Dun.query.order_by(Dun.name).all(),
        bahagians=Bahagian.query.order_by(Bahagian.name).all(),
        search=search,
        selected_parlimen=parlimen,
        selected_daerah_id=daerah_id,
        selected_dun_id=dun_id,
        selected_bahagian_id=bahagian_id,
        selected_cawangan=cawangan,
    )


# =========================
# ADD MEMBER
# =========================
@admin_bp.route("/members/add", methods=["GET", "POST"])
@login_required
def add_member():
    parlimens = Parlimen.query.order_by(Parlimen.name).all()
    bahagians = Bahagian.query.order_by(Bahagian.name).all()
    all_duns = Dun.query.order_by(Dun.name).all()

    if request.method == "POST":
        bahagian_id = request.form.get("bahagian_id", type=int)
        dun_id = request.form.get("dun_id", type=int)

        negeri = (request.form.get("negeri") or "").strip() or None
        cawangan = (request.form.get("cawangan") or "").strip() or None
        pusatmengundi = (request.form.get("pusatmengundi") or "").strip() or None

        parlimen_spr = (request.form.get("parlimen_spr") or "").strip().upper() or None
        daerah_spr = (request.form.get("daerah_spr") or "").strip().upper() or None
        dun_spr = (request.form.get("dun_spr") or "").strip().upper() or None

        noid = request.form.get("noid", type=int)
        ic = (request.form.get("ic") or "").strip() or None

        if noid is not None and Member.query.filter_by(noid=noid).first():
            flash("NoID already exists.", "danger")
            return redirect(request.url)

        if ic and Member.query.filter_by(ic=ic).first():
            flash("IC already exists.", "danger")
            return redirect(request.url)

        selected_bahagian = Bahagian.query.get(bahagian_id) if bahagian_id else None
        selected_dun = Dun.query.get(dun_id) if dun_id else None

        member = Member(
            ic=ic,
            noid=noid,
            title=(request.form.get("title") or "").strip() or None,
            fullname=(request.form.get("fullname") or "").strip() or None,
            jantina=(request.form.get("jantina") or "").strip() or None,
            negeri=negeri,

            parlimen=None,
            daerah_id=None,
            bahagian_id=bahagian_id,
            dun_id=dun_id,
            bahagian=(selected_bahagian.name if selected_bahagian else None),
            dun=(selected_dun.name if selected_dun else None),
            cawangan=cawangan,
            pusatmengundi=pusatmengundi,

            birthdate=request.form.get("birthdate") or None,
            warganegara=(request.form.get("warganegara") or "").strip() or "WARGANEGARA",
            bangsa=(request.form.get("bangsa") or "").strip() or None,
            kelulusan_akademik=(request.form.get("kelulusan_akademik") or "").strip() or None,
            pekerjaan=(request.form.get("pekerjaan") or "").strip() or None,
            alamat=(request.form.get("alamat") or "").strip() or None,
            emel=(request.form.get("emel") or "").strip() or None,
            notelefon=(request.form.get("notelefon") or "").strip() or None,
            registration_date=request.form.get("registration_date") or None,
            memberstatus=(request.form.get("memberstatus") or "").strip() or None,

            parlimen_spr=parlimen_spr,
            daerah_spr=daerah_spr,
            dun_spr=dun_spr,
        )

        db.session.add(member)
        db.session.commit()
        flash("Member added.", "success")
        return redirect(url_for("admin.members"))

    return render_template(
        "admin/add_member.html",
        parlimens=parlimens,
        bahagians=bahagians,
        duns=all_duns
    )


# =========================
# EDIT MEMBER
# =========================
@admin_bp.route("/members/edit/<int:member_id>", methods=["GET", "POST"])
@login_required
@member_editor_required
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)

    parlimens = Parlimen.query.order_by(Parlimen.name).all()
    bahagians = Bahagian.query.order_by(Bahagian.name).all()
    all_duns = Dun.query.order_by(Dun.name).all()

    if request.method == "POST":
        bahagian_id = request.form.get("bahagian_id", type=int)
        dun_id = request.form.get("dun_id", type=int)

        parlimen_spr = (request.form.get("parlimen_spr") or "").strip().upper() or None
        daerah_spr = (request.form.get("daerah_spr") or "").strip().upper() or None
        dun_spr = (request.form.get("dun_spr") or "").strip().upper() or None

        selected_bahagian = Bahagian.query.get(bahagian_id) if bahagian_id else None
        selected_dun = Dun.query.get(dun_id) if dun_id else None

        new_ic = (request.form.get("ic") or "").strip() or None
        if new_ic and new_ic != member.ic:
            existing = Member.query.filter(Member.ic == new_ic, Member.id != member.id).first()
            if existing:
                flash("IC already exists.", "danger")
                return redirect(request.url)
            member.ic = new_ic

        member.noid = request.form.get("noid", type=int)
        member.title = (request.form.get("title") or "").strip() or None
        member.fullname = (request.form.get("fullname") or "").strip() or None
        member.jantina = (request.form.get("jantina") or "").strip() or None
        member.negeri = (request.form.get("negeri") or "").strip() or None

        member.parlimen = None
        member.daerah_id = None
        member.dun_id = dun_id
        member.bahagian_id = bahagian_id
        member.bahagian = selected_bahagian.name if selected_bahagian else None
        member.dun = selected_dun.name if selected_dun else None
        member.cawangan = (request.form.get("cawangan") or "").strip() or None
        member.pusatmengundi = (request.form.get("pusatmengundi") or "").strip() or None

        member.birthdate = request.form.get("birthdate") or None
        member.warganegara = (request.form.get("warganegara") or "").strip() or None
        member.bangsa = (request.form.get("bangsa") or "").strip() or None
        member.kelulusan_akademik = (request.form.get("kelulusan_akademik") or "").strip() or None
        member.pekerjaan = (request.form.get("pekerjaan") or "").strip() or None
        member.alamat = (request.form.get("alamat") or "").strip() or None
        member.emel = (request.form.get("emel") or "").strip() or None
        member.notelefon = (request.form.get("notelefon") or "").strip() or None
        member.registration_date = request.form.get("registration_date") or None
        member.memberstatus = (request.form.get("memberstatus") or "").strip() or None

        member.parlimen_spr = parlimen_spr
        member.daerah_spr = daerah_spr
        member.dun_spr = dun_spr

        db.session.commit()
        flash("Member updated.", "success")
        return redirect(url_for("admin.members"))

    return render_template(
        "admin/member_form.html",
        member=member,
        parlimens=parlimens,
        bahagians=bahagians,
        duns=all_duns,
    )


# =========================
# DELETE MEMBER
# =========================
@admin_bp.route("/members/delete/<int:member_id>", methods=["POST"])
@login_required
@member_editor_required
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash("Member deleted", "warning")
    return redirect(url_for("admin.members"))


# =========================
# USER MANAGEMENT
# =========================
@admin_bp.route("/users")
@login_required
@admin_required
def list_users():
    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin/user.html", users=users)


@admin_bp.route("/users/add", methods=["POST"])
@login_required
@admin_required
def add_user():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    role = (request.form.get("role") or "user").strip().lower()

    if role not in ("admin", "user"):
        role = "user"

    if not username or not password:
        flash("Username and password are required.", "danger")
        return redirect(url_for("admin.list_users"))

    existing = User.query.filter(
        db.func.lower(User.username) == username.lower()
    ).first()

    if existing:
        flash("Username already exists.", "danger")
        return redirect(url_for("admin.list_users"))

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role
    )

    db.session.add(user)
    db.session.commit()

    flash(f"User '{username}' added successfully.", "success")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@super_admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = (request.form.get("role") or "").strip().lower()

    if new_role not in ("admin", "user"):
        flash("Invalid role selected.", "danger")
        return redirect(url_for("admin.list_users"))

    if user.username.strip().lower() == "upko":
        flash("You cannot change the UPKO admin role.", "warning")
        return redirect(url_for("admin.list_users"))

    user.role = new_role
    db.session.commit()

    flash(f"Role for '{user.username}' updated.", "success")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@super_admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.list_users"))

    if user.username.strip().lower() == "upko":
        flash("The UPKO account cannot be deleted.", "warning")
        return redirect(url_for("admin.list_users"))

    db.session.delete(user)
    db.session.commit()

    flash(f"User '{user.username}' deleted.", "success")
    return redirect(url_for("admin.list_users"))


# =========================
# API: DAERAHS BY PARLIMEN
# =========================
@admin_bp.route("/api/daerahs")
@login_required
def api_daerahs():
    parlimen_id = request.args.get("parlimen_id", type=int)
    if not parlimen_id:
        return jsonify([])

    daerahs = Daerah.query.filter_by(
        parlimen_id=parlimen_id
    ).order_by(Daerah.name).all()

    return jsonify([{"id": d.id, "name": d.name} for d in daerahs])


# =========================
# API: DUNS BY DAERAH
# =========================
@admin_bp.route("/api/duns")
@login_required
def api_duns():
    daerah_id = request.args.get("daerah_id", type=int)
    if not daerah_id:
        return jsonify([])

    duns = (
        Dun.query
        .filter(Dun.daerah_id == daerah_id)
        .order_by(Dun.name)
        .all()
    )

    return jsonify([{"id": d.id, "name": d.name} for d in duns])


# =========================
# MEMBER REPORT
# =========================
@admin_bp.route("/member-report")
@login_required
def member_report():
    page = request.args.get("page", 1, type=int)
    per_page = 100

    search = request.args.get("q", "").strip()
    parlimen = request.args.get("parlimen", "").strip()
    dun_id = request.args.get("dun_id", type=int)
    bahagian_id = request.args.get("bahagian_id", type=int)
    cawangan = request.args.get("cawangan", "").strip()

    query = Member.query

    # ======================================================
    # LIMIT ACCESS FOR BAHAGIAN / CAWANGAN APPLICATION USERS
    # They can access the report, but only for their Bahagian.
    # ======================================================
    is_application_user = current_user.role in ("bahagian", "cawangan")

    user_bahagian_id = getattr(current_user, "bahagian_id", None)
    user_bahagian_name = getattr(current_user, "bahagian_name", None)

    if is_application_user:
        # Force remove Parlimen filter for application users
        parlimen = ""

        if user_bahagian_id:
            query = query.filter(Member.bahagian_id == user_bahagian_id)
            bahagian_id = user_bahagian_id

        elif user_bahagian_name:
            query = query.filter(Member.bahagian.ilike(user_bahagian_name))

        else:
            # No Bahagian assigned = show nothing
            query = query.filter(False)

    # ======================================================
    # SEARCH FILTER
    # ======================================================
    if search:
        filters = [
            Member.fullname.ilike(f"%{search}%"),
            Member.ic.ilike(f"%{search}%")
        ]

        if search.isdigit():
            try:
                noid_value = int(search)
                if -2147483648 <= noid_value <= 2147483647:
                    filters.append(Member.noid == noid_value)
            except ValueError:
                pass

        query = query.filter(or_(*filters))

    # ======================================================
    # NORMAL FILTERS
    # Admin can use all filters.
    # Bahagian/Cawangan users cannot use Parlimen or override Bahagian.
    # ======================================================
    if parlimen and not is_application_user:
        query = query.filter(Member.parlimen == parlimen)

    if dun_id:
        query = query.filter(Member.dun_id == dun_id)

    if bahagian_id and not is_application_user:
        query = query.filter(Member.bahagian_id == bahagian_id)

    if cawangan:
        query = query.filter(Member.cawangan.ilike(f"%{cawangan}%"))

    pagination = query.order_by(Member.noid.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    members = pagination.items

    # ======================================================
    # DROPDOWN DATA
    # Admin = all Bahagian/DUN/Parlimen.
    # Application users = only their Bahagian-related DUN/Cawangan.
    # Parlimen dropdown should be hidden in template using is_application_user.
    # ======================================================
    if is_application_user:
        parlimens = []

        if user_bahagian_id:
            bahagians = Bahagian.query.filter_by(id=user_bahagian_id).all()

            duns = (
                db.session.query(Dun)
                .join(Member, Member.dun_id == Dun.id)
                .filter(Member.bahagian_id == user_bahagian_id)
                .distinct()
                .order_by(Dun.name.asc())
                .all()
            )

            cawangans_query = (
                db.session.query(Member.cawangan)
                .filter(
                    Member.bahagian_id == user_bahagian_id,
                    Member.cawangan.isnot(None),
                    Member.cawangan != ""
                )
            )

        elif user_bahagian_name:
            bahagians = (
                Bahagian.query
                .filter(Bahagian.name.ilike(user_bahagian_name))
                .all()
            )

            duns = (
                db.session.query(Dun)
                .join(Member, Member.dun_id == Dun.id)
                .filter(Member.bahagian.ilike(user_bahagian_name))
                .distinct()
                .order_by(Dun.name.asc())
                .all()
            )

            cawangans_query = (
                db.session.query(Member.cawangan)
                .filter(
                    Member.bahagian.ilike(user_bahagian_name),
                    Member.cawangan.isnot(None),
                    Member.cawangan != ""
                )
            )

        else:
            bahagians = []
            duns = []
            cawangans_query = db.session.query(Member.cawangan).filter(False)

    else:
        parlimens = Parlimen.query.order_by(Parlimen.name).all()
        bahagians = Bahagian.query.order_by(Bahagian.name).all()
        duns = Dun.query.order_by(Dun.name).all()

        cawangans_query = (
            db.session.query(Member.cawangan)
            .filter(
                Member.cawangan.isnot(None),
                Member.cawangan != ""
            )
        )

        if bahagian_id:
            cawangans_query = cawangans_query.filter(Member.bahagian_id == bahagian_id)

    cawangans = [
        c[0]
        for c in cawangans_query.distinct().order_by(Member.cawangan.asc()).all()
    ]

    return render_template(
        "admin/member_report.html",
        members=members,
        pagination=pagination,
        total=pagination.total,

        parlimens=parlimens,
        duns=duns,
        bahagians=bahagians,
        cawangans=cawangans,

        search=search,
        selected_parlimen=parlimen,
        selected_dun_id=dun_id,
        selected_bahagian_id=bahagian_id,
        selected_cawangan=cawangan,

        is_application_user=is_application_user,
    )


# =========================
# API: DUNS BY BAHAGIAN
# =========================
@admin_bp.route("/api/duns-by-bahagian")
@login_required
def api_duns_by_bahagian():
    bahagian_id = request.args.get("bahagian_id", type=int)
    if not bahagian_id:
        return jsonify([])

    rows = (
        db.session.query(Dun.id, Dun.name)
        .join(Member, Member.dun_id == Dun.id)
        .filter(Member.bahagian_id == bahagian_id)
        .distinct()
        .order_by(Dun.name.asc())
        .all()
    )

    return jsonify([{"id": r.id, "name": r.name} for r in rows])


# =========================
# EXPORT MEMBERS CSV
# =========================
@admin_bp.route("/members/export")
@login_required
@super_admin_required
def export_members_csv():
    search = request.args.get("q", "").strip()
    dun_id = request.args.get("dun_id", type=int)
    bahagian_id = request.args.get("bahagian_id", type=int)
    cawangan = request.args.get("cawangan", "").strip()

    query = Member.query

    if search:
        filters = [
            Member.ic.ilike(f"%{search}%"),
            Member.fullname.ilike(f"%{search}%")
        ]

        if search.isdigit():
            try:
                noid_value = int(search)
                if -2147483648 <= noid_value <= 2147483647:
                    filters.append(Member.noid == noid_value)
            except ValueError:
                pass

        query = query.filter(or_(*filters))

    if dun_id:
        query = query.filter(Member.dun_id == dun_id)

    if bahagian_id:
        query = query.filter(Member.bahagian_id == bahagian_id)

    if cawangan:
        query = query.filter(Member.cawangan.ilike(f"%{cawangan}%"))

    members = query.order_by(Member.noid.asc()).all()

    selected_bahagian = Bahagian.query.get(bahagian_id) if bahagian_id else None
    selected_dun = Dun.query.get(dun_id) if dun_id else None

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "IC",
        "Title",
        "Full Name",
        "Gender",
        "Negeri",
        "Bahagian",
        "DUN",
        "Cawangan",
        "Pusat Mengundi",
        "Birthdate",
        "Warganegara",
        "Bangsa",
        "Kelulusan Akademik",
        "Pekerjaan",
        "Alamat",
        "Email",
        "No Telefon",
        "Registration Date",
        "Member Status",
        "Parlimen SPR",
        "Daerah SPR",
        "DUN SPR",
    ])

    for m in members:
        writer.writerow([
            f'="{m.noid:05d}"' if m.noid is not None else "",
            f'="{m.ic}"' if m.ic else "",
            clean_csv_value(m.title),
            clean_csv_value(m.fullname),
            clean_csv_value(m.jantina),
            clean_csv_value(m.negeri),
            clean_csv_value(m.bahagian),
            clean_csv_value(m.dun),
            clean_csv_value(m.cawangan),
            clean_csv_value(m.pusatmengundi),
            m.birthdate.strftime("%Y-%m-%d") if m.birthdate else "",
            clean_csv_value(m.warganegara),
            clean_csv_value(m.bangsa),
            clean_csv_value(m.kelulusan_akademik),
            clean_csv_value(m.pekerjaan),
            clean_csv_value(m.alamat),
            clean_csv_value(m.emel),
            clean_csv_value(m.notelefon),
            m.registration_date.strftime("%Y-%m-%d") if m.registration_date else "",
            clean_csv_value(m.memberstatus),
            clean_csv_value(m.parlimen_spr),
            clean_csv_value(m.daerah_spr),
            clean_csv_value(m.dun_spr),
        ])

    csv_data = output.getvalue()
    output.close()

    filename_parts = ["members_export"]

    if selected_bahagian:
        safe_bahagian = selected_bahagian.name.replace(" ", "_").replace("/", "_")
        filename_parts.append(f"bahagian_{safe_bahagian}")

    if selected_dun:
        safe_dun = selected_dun.name.replace(" ", "_").replace("/", "_")
        filename_parts.append(f"dun_{safe_dun}")

    if cawangan:
        safe_cawangan = cawangan.replace(" ", "_").replace("/", "_")
        filename_parts.append(f"cawangan_{safe_cawangan}")

    filename = "_".join(filename_parts) + ".csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
