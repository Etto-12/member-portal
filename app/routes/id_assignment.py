from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.id_assignment import IdAssignment
from app.models.member import Member
from app.models.user import User


id_assignment_bp = Blueprint(
    "id_assignment",
    __name__,
    url_prefix="/admin/id-assignment"
)


START_NOID = 162687
INITIAL_BATCH_SIZE = 5000
GENERATE_BATCH_SIZE = 500

MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def format_myt(value):
    if not value:
        return ""

    # assigned_at values are stored as naive UTC datetimes
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(MALAYSIA_TZ).strftime("%Y-%m-%d %H:%M:%S")


def format_myt_date(value):
    if not value:
        return ""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(MALAYSIA_TZ).strftime("%d %b %Y")


def normalize_text(value):
    return (value or "").strip().lower()


def safe_bool_attr(user, attr_name):
    value = getattr(user, attr_name, False)

    if callable(value):
        try:
            return bool(value())
        except TypeError:
            return False

    return bool(value)


def is_super_admin_user(user):
    role = normalize_text(getattr(user, "role", ""))
    username = normalize_text(getattr(user, "username", ""))
    display_role = normalize_text(getattr(user, "display_role", ""))

    return (
        safe_bool_attr(user, "is_super_admin")
        or username == "upko"
        or username in ("superadmin", "super_admin", "su")
        or role in ("super_admin", "superadmin", "su")
        or display_role in ("super_admin", "superadmin", "super admin", "su")
    )


def is_admin_user(user):
    role = normalize_text(getattr(user, "role", ""))

    return (
        safe_bool_attr(user, "is_admin")
        or role == "admin"
    )


def user_has_id_assignment_access(user):
    return is_super_admin_user(user) or is_admin_user(user)


def id_assignment_required():
    if not current_user.is_authenticated:
        abort(403)

    if not user_has_id_assignment_access(current_user):
        abort(403)


def get_color_for_user(user_id, username):
    username = username or "admin"
    user_id = user_id or 0

    key = f"{user_id}-{username}".encode("utf-8")
    digest = hashlib.md5(key).hexdigest()
    hue = int(digest[:8], 16) % 360

    return f"hsl({hue}, 78%, 42%)"


def get_current_user_color():
    username = getattr(current_user, "username", "admin") or "admin"
    user_id = getattr(current_user, "id", 0) or 0

    return get_color_for_user(user_id, username)


def get_access_users():
    users = User.query.order_by(User.username.asc()).all()
    access_users = []

    for user in users:
        if not user_has_id_assignment_access(user):
            continue

        username = getattr(user, "username", "")
        user_id = getattr(user, "id", 0)
        role = normalize_text(getattr(user, "role", ""))

        if is_super_admin_user(user):
            access_type = "Super Admin"
        else:
            access_type = "Admin"

        access_users.append({
            "id": user_id,
            "username": username,
            "role": role or "-",
            "access_type": access_type,
            "color": get_color_for_user(user_id, username),
        })

    return access_users


def seed_ids(start_noid, end_noid):
    existing = {
        row.noid
        for row in IdAssignment.query
        .filter(IdAssignment.noid >= start_noid)
        .filter(IdAssignment.noid <= end_noid)
        .all()
    }

    new_rows = []

    for noid in range(start_noid, end_noid + 1):
        if noid not in existing:
            new_rows.append(IdAssignment(noid=noid))

    if new_rows:
        db.session.bulk_save_objects(new_rows)
        db.session.commit()

    return len(new_rows)


def ensure_initial_ids():
    count = IdAssignment.query.count()

    if count == 0:
        seed_ids(START_NOID, START_NOID + INITIAL_BATCH_SIZE - 1)


@id_assignment_bp.route("/", methods=["GET"])
@login_required
def index():
    id_assignment_required()
    ensure_initial_ids()

    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "available").strip()
    search = request.args.get("q", "").strip()

    query = IdAssignment.query

    if status == "assigned":
        query = query.filter(IdAssignment.is_assigned.is_(True))
    elif status == "available":
        query = query.filter(IdAssignment.is_assigned.is_(False))

    if search:
        # Numeric prefix search:
        # "1640" can match 164040, 164041, etc.
        # Non-numeric input intentionally returns no rows.
        if search.isdigit():
            query = query.filter(
                db.cast(IdAssignment.noid, db.String).like(f"{search}%")
            )
        else:
            query = query.filter(db.false())

    pagination = query.order_by(IdAssignment.noid.asc()).paginate(
        page=page,
        per_page=200,
        error_out=False
    )

    rows = pagination.items

    total_ids = IdAssignment.query.count()
    assigned_count = IdAssignment.query.filter_by(is_assigned=True).count()
    available_count = total_ids - assigned_count

    highest_id = db.session.query(db.func.max(IdAssignment.noid)).scalar() or START_NOID - 1

    access_users = get_access_users()
    current_admin_color = get_current_user_color()

    return render_template(
        "admin/id_assignment.html",
        rows=rows,
        pagination=pagination,
        status=status,
        search=search,
        total_ids=total_ids,
        assigned_count=assigned_count,
        available_count=available_count,
        highest_id=highest_id,
        access_users=access_users,
        current_admin_color=current_admin_color,
        format_myt=format_myt,
        format_myt_date=format_myt_date,
    )


@id_assignment_bp.route("/generate", methods=["POST"])
@login_required
def generate_more():
    id_assignment_required()

    highest_id = db.session.query(db.func.max(IdAssignment.noid)).scalar()

    if not highest_id or highest_id < START_NOID:
        start_noid = START_NOID
    else:
        start_noid = highest_id + 1

    end_noid = start_noid + GENERATE_BATCH_SIZE - 1

    added_count = seed_ids(start_noid, end_noid)

    if added_count:
        flash(
            f"Generated {added_count} new IDs from {start_noid} to {end_noid}.",
            "success"
        )
    else:
        flash(
            "No new IDs were generated because that range already exists.",
            "warning"
        )

    return redirect(url_for("id_assignment.index"))


@id_assignment_bp.route("/assign", methods=["POST"])
@login_required
def assign_id():
    id_assignment_required()

    data = request.get_json(silent=True) or {}
    noid = data.get("noid")

    try:
        noid = int(noid)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "message": "Invalid ID."
        }), 400

    if noid < START_NOID:
        return jsonify({
            "ok": False,
            "message": f"ID must be {START_NOID} or above."
        }), 400

    username = getattr(current_user, "username", "Admin")
    user_id = getattr(current_user, "id", None)
    color = get_current_user_color()
    now = datetime.utcnow()

    updated = IdAssignment.query.filter(
        IdAssignment.noid == noid,
        IdAssignment.is_assigned.is_(False)
    ).update({
        "is_assigned": True,
        "assigned_by_user_id": user_id,
        "assigned_by_username": username,
        "assigned_color": color,
        "assigned_at": now,
    }, synchronize_session=False)

    db.session.commit()

    if updated == 0:
        row = IdAssignment.query.filter_by(noid=noid).first()

        if not row:
            return jsonify({
                "ok": False,
                "message": "This ID does not exist yet. Generate more IDs first."
            }), 404

        return jsonify({
            "ok": False,
            "message": f"ID {noid} has already been assigned by {row.assigned_by_username or 'another admin'}.",
            "assigned_by_username": row.assigned_by_username,
            "assigned_color": row.assigned_color,
        }), 409

    return jsonify({
        "ok": True,
        "noid": noid,
        "assigned_by_username": username,
        "assigned_color": color,
        "assigned_at": format_myt(now),
    })


@id_assignment_bp.route("/release", methods=["POST"])
@login_required
def release_id():
    id_assignment_required()

    data = request.get_json(silent=True) or {}
    noid = data.get("noid")

    try:
        noid = int(noid)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "message": "Invalid ID."
        }), 400

    # Safety rule:
    # Never release an ID that has already been attached to a real member.
    member = (
        Member.query
        .filter(Member.noid == noid)
        .order_by(Member.id.asc())
        .first()
    )

    if member:
        member_name = (member.fullname or "").strip() or "an existing member"
        return jsonify({
            "ok": False,
            "message": (
                f"ID {noid} cannot be released because it is already used by "
                f"{member_name}."
            ),
            "member_id": member.id,
            "member_name": member_name,
        }), 409

    updated = IdAssignment.query.filter(
        IdAssignment.noid == noid,
        IdAssignment.is_assigned.is_(True)
    ).update({
        "is_assigned": False,
        "assigned_by_user_id": None,
        "assigned_by_username": None,
        "assigned_color": None,
        "assigned_at": None,
    }, synchronize_session=False)

    db.session.commit()

    if updated == 0:
        return jsonify({
            "ok": False,
            "message": "This ID was not assigned."
        }), 400

    return jsonify({
        "ok": True,
        "noid": noid,
    })


@id_assignment_bp.route("/status", methods=["GET"])
@login_required
def status():
    id_assignment_required()

    ids_raw = request.args.get("ids", "")
    noids = []

    for value in ids_raw.split(","):
        value = value.strip()

        if not value:
            continue

        try:
            noids.append(int(value))
        except ValueError:
            continue

    if not noids:
        return jsonify({
            "ok": True,
            "rows": []
        })

    rows = IdAssignment.query.filter(IdAssignment.noid.in_(noids)).all()

    return jsonify({
        "ok": True,
        "rows": [
            {
                "noid": row.noid,
                "is_assigned": row.is_assigned,
                "assigned_by_username": row.assigned_by_username,
                "assigned_color": row.assigned_color,
                "assigned_at": format_myt(row.assigned_at),
            }
            for row in rows
        ]
    })
