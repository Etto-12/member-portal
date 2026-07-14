from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import or_

from app.extensions import db
from app.models.user import User
from app.models.member import Member
from app.models.membership_application import MembershipApplication
from app.models.location import Parlimen, Daerah, Bahagian, Dun


applications_bp = Blueprint("applications", __name__)


# =========================
# HELPERS
# =========================
def parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def application_user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("applications.login"))

        if current_user.role not in ("cawangan", "bahagian"):
            abort(403)

        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)

        if getattr(current_user, "role", None) != "admin":
            abort(403)

        return f(*args, **kwargs)

    return wrapper


def super_admin_only():
    return (
        current_user.is_authenticated
        and getattr(current_user, "role", None) == "admin"
        and (
            getattr(current_user, "is_super_admin", False)
            or current_user.username.strip().lower() == "upko"
        )
    )


def application_ready_for_admin(form):
    required_text = [
        "nama_pencadang",
        "no_keahlian_pencadang",
        "f_setiausaha_cawangan",
        "g_setiausaha_bahagian",
    ]

    required_dates = [
        "f_tarikh_diterima",
        "f_tarikh_dikemukakan",
        "g_tarikh_diterima",
        "g_tarikh_dikemukakan",
    ]

    for field in required_text:
        if not (form.get(field) or "").strip():
            return False

    for field in required_dates:
        if not (form.get(field) or "").strip():
            return False

    if form.get("f_signed") != "on":
        return False

    if form.get("g_signed") != "on":
        return False

    return True


def get_application_query_for_current_user():
    query = MembershipApplication.query

    if current_user.role == "cawangan":
        query = query.filter(
            MembershipApplication.submitted_by_user_id == current_user.id
        )

    elif current_user.role == "bahagian":
        query = query.filter(
            or_(
                MembershipApplication.submitted_by_user_id == current_user.id,
                MembershipApplication.bahagian_id == getattr(current_user, "bahagian_id", None),
                MembershipApplication.apply_bahagian == getattr(current_user, "bahagian_name", None),
            )
        )

    return query


# =========================
# APPLICATION PORTAL LOGIN
# =========================
@applications_bp.route("/apply/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return redirect(url_for("applications.login"))

        if user.role not in ("cawangan", "bahagian"):
            flash(
                "This login page is only for Cawangan/Bahagian application submission accounts.",
                "danger",
            )
            return redirect(url_for("applications.login"))

        login_user(user)
        return redirect(url_for("applications.dashboard"))

    return render_template("applications/login.html")


@applications_bp.route("/apply/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("applications.login"))


@applications_bp.route("/apply/dashboard")
@application_user_required
def dashboard():
    total = get_application_query_for_current_user().count()
    pending = get_application_query_for_current_user().filter_by(status="pending").count()
    approved = get_application_query_for_current_user().filter_by(status="approved").count()
    rejected = get_application_query_for_current_user().filter_by(status="rejected").count()

    return render_template(
        "applications/dashboard.html",
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected,
    )


# =========================
# CAWANGAN / BAHAGIAN SUBMISSION
# =========================
@applications_bp.route("/apply/new", methods=["GET", "POST"])
@application_user_required
def new_application():
    parlimens = Parlimen.query.order_by(Parlimen.name).all()
    bahagians = Bahagian.query.order_by(Bahagian.name).all()

    if request.method == "POST":
        if not application_ready_for_admin(request.form):
            flash(
                "Please complete sections E, F and G before submitting for Admin review.",
                "danger",
            )
            return render_template(
                "applications/application_form.html",
                parlimens=parlimens,
                bahagians=bahagians,
            )

        app = MembershipApplication(
            submitted_by_user_id=current_user.id,
            submitted_by_role=current_user.role,
            submitted_by_username=current_user.username,
            status="pending",

            # A. Application area
            apply_cawangan=(
                request.form.get("apply_cawangan")
                or getattr(current_user, "cawangan_name", "")
                or ""
            ).strip(),
            apply_bahagian=(
                request.form.get("apply_bahagian")
                or getattr(current_user, "bahagian_name", "")
                or ""
            ).strip(),
            apply_negeri=(request.form.get("apply_negeri") or "").strip(),

            # B. Applicant details
            fullname=(request.form.get("fullname") or "").strip(),
            ic=(request.form.get("ic") or "").strip(),
            old_ic=(request.form.get("old_ic") or "").strip(),
            birthdate=parse_date(request.form.get("birthdate")),
            jantina=request.form.get("jantina"),
            warganegara=(request.form.get("warganegara") or "WARGANEGARA").strip(),
            bangsa=(request.form.get("bangsa") or "").strip(),
            kelulusan_akademik=(request.form.get("kelulusan_akademik") or "").strip(),
            pekerjaan=(request.form.get("pekerjaan") or "").strip(),
            alamat_surat=(request.form.get("alamat_surat") or "").strip(),
            alamat_rumah=(request.form.get("alamat_rumah") or "").strip(),
            emel=(request.form.get("emel") or "").strip(),
            notelefon_rumah=(request.form.get("notelefon_rumah") or "").strip(),
            notelefon_pejabat=(request.form.get("notelefon_pejabat") or "").strip(),
            notelefon_hp=(request.form.get("notelefon_hp") or "").strip(),
            pengakuan_accepted=request.form.get("pengakuan_accepted") == "on",

            # D. SPR details
            parlimen_spr=(request.form.get("parlimen_spr") or "").strip(),
            negeri_spr=(request.form.get("negeri_spr") or "").strip(),
            daerah_mengundi=(request.form.get("daerah_mengundi") or "").strip(),
            pusat_mengundi=(request.form.get("pusat_mengundi") or "").strip(),

            # Internal mapping to main member portal
            parlimen=(request.form.get("parlimen") or "").strip().upper(),
            daerah_id=request.form.get("daerah_id", type=int),
            dun_id=request.form.get("dun_id", type=int),
            bahagian_id=request.form.get("bahagian_id", type=int)
            or getattr(current_user, "bahagian_id", None),

            # E. Sokongan
            nama_pencadang=(request.form.get("nama_pencadang") or "").strip(),
            no_keahlian_pencadang=(request.form.get("no_keahlian_pencadang") or "").strip(),
            tarikh_sokongan=parse_date(request.form.get("tarikh_sokongan")),

            # F. Cawangan
            f_tarikh_diterima=parse_date(request.form.get("f_tarikh_diterima")),
            f_tarikh_dikemukakan=parse_date(request.form.get("f_tarikh_dikemukakan")),
            f_nota=(request.form.get("f_nota") or "").strip(),
            f_setiausaha_cawangan=(request.form.get("f_setiausaha_cawangan") or "").strip(),
            f_signed=request.form.get("f_signed") == "on",

            # G. Bahagian
            g_tarikh_diterima=parse_date(request.form.get("g_tarikh_diterima")),
            g_tarikh_dikemukakan=parse_date(request.form.get("g_tarikh_dikemukakan")),
            g_nota=(request.form.get("g_nota") or "").strip(),
            g_setiausaha_bahagian=(request.form.get("g_setiausaha_bahagian") or "").strip(),
            g_signed=request.form.get("g_signed") == "on",
        )

        if not app.fullname or not app.ic or not app.pengakuan_accepted:
            flash("Applicant name, IC number and declaration checkbox are required.", "danger")
            return render_template(
                "applications/application_form.html",
                parlimens=parlimens,
                bahagians=bahagians,
            )

        db.session.add(app)
        db.session.commit()

        flash("Membership application submitted for Admin review.", "success")
        return redirect(url_for("applications.my_submissions"))

    return render_template(
        "applications/application_form.html",
        parlimens=parlimens,
        bahagians=bahagians,
    )


@applications_bp.route("/apply/my-submissions")
@application_user_required
def my_submissions():
    applications = (
        get_application_query_for_current_user()
        .order_by(MembershipApplication.created_at.desc())
        .all()
    )

    return render_template(
        "applications/my_submissions.html",
        applications=applications,
    )


# =========================
# ADMIN: APPLICATION ACCOUNT MANAGEMENT
# =========================
@applications_bp.route("/admin/application-accounts", methods=["GET", "POST"])
@login_required
@admin_required
def application_accounts():
    bahagians = Bahagian.query.order_by(Bahagian.name).all()

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        role = request.form.get("role")
        bahagian_id = request.form.get("bahagian_id", type=int)
        cawangan_name = (request.form.get("cawangan_name") or "").strip()

        if role not in ("cawangan", "bahagian"):
            flash("Role must be cawangan or bahagian.", "danger")
            return redirect(url_for("applications.application_accounts"))

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("applications.application_accounts"))

        if role == "cawangan" and not cawangan_name:
            flash("Cawangan name is required for Cawangan account.", "danger")
            return redirect(url_for("applications.application_accounts"))

        if User.query.filter(db.func.lower(User.username) == username.lower()).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("applications.application_accounts"))

        selected_bahagian = Bahagian.query.get(bahagian_id) if bahagian_id else None

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            bahagian_id=selected_bahagian.id if selected_bahagian else None,
            bahagian_name=selected_bahagian.name if selected_bahagian else None,
            cawangan_name=cawangan_name if role == "cawangan" else None,
        )

        db.session.add(user)
        db.session.commit()

        flash("Application login account created.", "success")
        return redirect(url_for("applications.application_accounts"))

    users = (
        User.query
        .filter(User.role.in_(["cawangan", "bahagian"]))
        .order_by(User.role, User.username)
        .all()
    )

    return render_template(
        "admin/application_accounts.html",
        users=users,
        bahagians=bahagians,
        can_manage_accounts=super_admin_only(),
    )


# =========================
# SUPER ADMIN: EDIT APPLICATION ACCOUNT
# =========================
@applications_bp.route("/admin/application-accounts/<int:user_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_application_account(user_id):
    if not super_admin_only():
        abort(403)

    user = User.query.get_or_404(user_id)

    if user.role not in ("cawangan", "bahagian"):
        flash("Only Bahagian/Cawangan application accounts can be edited here.", "danger")
        return redirect(url_for("applications.application_accounts"))

    username = (request.form.get("username") or "").strip()
    new_password = request.form.get("password") or ""
    role = (request.form.get("role") or "").strip().lower()
    bahagian_id = request.form.get("bahagian_id", type=int)
    cawangan_name = (request.form.get("cawangan_name") or "").strip()

    if role not in ("cawangan", "bahagian"):
        flash("Role must be cawangan or bahagian.", "danger")
        return redirect(url_for("applications.application_accounts"))

    if not username:
        flash("Username is required.", "danger")
        return redirect(url_for("applications.application_accounts"))

    duplicate = (
        User.query
        .filter(db.func.lower(User.username) == username.lower(), User.id != user.id)
        .first()
    )

    if duplicate:
        flash("Username already exists.", "danger")
        return redirect(url_for("applications.application_accounts"))

    if role == "cawangan" and not cawangan_name:
        flash("Cawangan name is required for Cawangan account.", "danger")
        return redirect(url_for("applications.application_accounts"))

    selected_bahagian = Bahagian.query.get(bahagian_id) if bahagian_id else None

    user.username = username
    user.role = role
    user.bahagian_id = selected_bahagian.id if selected_bahagian else None
    user.bahagian_name = selected_bahagian.name if selected_bahagian else None
    user.cawangan_name = cawangan_name if role == "cawangan" else None

    if new_password.strip():
        user.password_hash = generate_password_hash(new_password)

    db.session.commit()

    flash("Application account updated successfully.", "success")
    return redirect(url_for("applications.application_accounts"))


# =========================
# SUPER ADMIN: DELETE APPLICATION ACCOUNT
# =========================
@applications_bp.route("/admin/application-accounts/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_application_account(user_id):
    if not super_admin_only():
        abort(403)

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("applications.application_accounts"))

    if user.role not in ("cawangan", "bahagian"):
        flash("Only Bahagian/Cawangan application accounts can be deleted here.", "danger")
        return redirect(url_for("applications.application_accounts"))

    db.session.delete(user)
    db.session.commit()

    flash("Application account deleted successfully.", "success")
    return redirect(url_for("applications.application_accounts"))


# =========================
# ADMIN: REVIEW APPLICATIONS
# =========================
@applications_bp.route("/admin/applications")
@login_required
@admin_required
def admin_applications():
    status = request.args.get("status", "pending")
    q = (request.args.get("q") or "").strip()

    query = MembershipApplication.query

    if status:
        query = query.filter(MembershipApplication.status == status)

    if q:
        query = query.filter(
            or_(
                MembershipApplication.fullname.ilike(f"%{q}%"),
                MembershipApplication.ic.ilike(f"%{q}%"),
                MembershipApplication.apply_bahagian.ilike(f"%{q}%"),
                MembershipApplication.apply_cawangan.ilike(f"%{q}%"),
            )
        )

    applications = query.order_by(MembershipApplication.created_at.desc()).all()

    return render_template(
        "admin/applications_list.html",
        applications=applications,
        status=status,
        q=q,
    )


@applications_bp.route("/admin/applications/<int:application_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_review_application(application_id):
    app = MembershipApplication.query.get_or_404(application_id)

    if request.method == "POST":
        app.h_tarikh_diterima = parse_date(request.form.get("h_tarikh_diterima"))
        app.h_tarikh_diluluskan = parse_date(request.form.get("h_tarikh_diluluskan"))
        app.h_tarikh_yuran = parse_date(request.form.get("h_tarikh_yuran"))
        app.h_no_resit_yuran = (request.form.get("h_no_resit_yuran") or "").strip()
        app.h_no_keahlian = (request.form.get("h_no_keahlian") or "").strip()
        app.h_setiausaha_eksekutif = (
            request.form.get("h_setiausaha_eksekutif") or ""
        ).strip()
        app.admin_remarks = (request.form.get("admin_remarks") or "").strip()

        if app.status == "pending":
            app.status = "reviewed"

        app.reviewed_by_admin_id = current_user.id
        app.reviewed_at = datetime.utcnow()

        db.session.commit()

        flash("Application review details saved.", "success")
        return redirect(
            url_for("applications.admin_review_application", application_id=app.id)
        )

    return render_template("admin/application_review.html", app=app)


@applications_bp.route("/admin/applications/<int:application_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_application(application_id):
    app = MembershipApplication.query.get_or_404(application_id)

    if app.status == "approved":
        flash("This application has already been approved.", "warning")
        return redirect(
            url_for("applications.admin_review_application", application_id=app.id)
        )

    approved_noid = request.form.get("approved_noid", type=int)

    if not approved_noid:
        flash("Admin must enter No ID / No Keahlian before approval.", "danger")
        return redirect(
            url_for("applications.admin_review_application", application_id=app.id)
        )

    if approved_noid > 2147483647:
        flash("No ID is too large. Please enter a number below 2147483647.", "danger")
        return redirect(
            url_for("applications.admin_review_application", application_id=app.id)
        )

    if Member.query.filter_by(noid=approved_noid).first():
        flash("This No ID already exists in the members table.", "danger")
        return redirect(
            url_for("applications.admin_review_application", application_id=app.id)
        )

    if Member.query.filter_by(ic=app.ic).first():
        flash("A member with this IC already exists.", "danger")
        return redirect(
            url_for("applications.admin_review_application", application_id=app.id)
        )

    bahagian_obj = Bahagian.query.get(app.bahagian_id) if app.bahagian_id else None

    bahagian_name = bahagian_obj.name if bahagian_obj else app.apply_bahagian
    parlimen_name = app.parlimen or app.parlimen_spr

    member = Member(
        ic=app.ic,
        noid=approved_noid,

        title=None,
        fullname=app.fullname,
        jantina=app.jantina,
        birthdate=app.birthdate,
        warganegara=app.warganegara or "WARGANEGARA",
        bangsa=app.bangsa,
        kelulusan_akademik=app.kelulusan_akademik,
        pekerjaan=app.pekerjaan,

        alamat=app.alamat_rumah or app.alamat_surat,
        emel=app.emel,
        notelefon=app.notelefon_hp or app.notelefon_rumah,

        registration_date=app.h_tarikh_diluluskan or datetime.utcnow().date(),
        memberstatus="Aktif",

        parlimen=parlimen_name,
        daerah_id=app.daerah_id,
        dun_id=app.dun_id,
        bahagian_id=app.bahagian_id,

        # This writes into members.bahagian through Member.bahagian_text
        bahagian_text=bahagian_name,

        cawangan=app.apply_cawangan,
        pusatmengundi=app.pusat_mengundi,
    )

    app.status = "approved"
    app.approved_noid = approved_noid
    app.h_no_keahlian = app.h_no_keahlian or str(approved_noid)
    app.reviewed_by_admin_id = current_user.id
    app.reviewed_at = datetime.utcnow()

    db.session.add(member)
    db.session.commit()

    flash("Application approved and member created successfully.", "success")
    return redirect(url_for("applications.admin_applications", status="approved"))


@applications_bp.route("/admin/applications/<int:application_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_application(application_id):
    app = MembershipApplication.query.get_or_404(application_id)

    app.status = "rejected"
    app.admin_remarks = (request.form.get("admin_remarks") or app.admin_remarks or "").strip()
    app.reviewed_by_admin_id = current_user.id
    app.reviewed_at = datetime.utcnow()

    db.session.commit()

    flash("Application rejected.", "warning")
    return redirect(url_for("applications.admin_applications", status="rejected"))
