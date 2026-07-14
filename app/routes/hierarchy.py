from collections import defaultdict

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.hierarchy import HierarchyDocument


hierarchy_bp = Blueprint("hierarchy", __name__, url_prefix="/hierarchy")


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


DEFAULT_TERM = "UPKO Bagi Penggal 2026 - 2029"


POSITION_ALIASES = {
    "Ketua Penerangan": "Pegawai Penerangan",
    "Timbalan Ketua Penerangan": "Timbalan Pegawai Penerangan",
    "Naib Ketua Cawangan": "Naib Ketua (Pemuda)",
}


POSITION_PRESETS = {
    "MAJLIS_TERTINGGI": [
        {"position": "Presiden", "bil": "-"},
        {"position": "Timbalan Presiden", "bil": "-"},

        {"position": "Naib Presiden", "bil": "1"},
        {"position": "Naib Presiden", "bil": "2"},
        {"position": "Naib Presiden", "bil": "3"},
        {"position": "Naib Presiden", "bil": "4"},
        {"position": "Naib Presiden", "bil": "5"},
        {"position": "Naib Presiden", "bil": "6"},
        {"position": "Naib Presiden", "bil": "7"},
        {"position": "Naib Presiden", "bil": "8 (W)"},
        {"position": "Naib Presiden", "bil": "9 (P)"},

        {"position": "Setiausaha Agung", "bil": "-"},
        {"position": "Timbalan Setiausaha Agung", "bil": "1"},
        {"position": "Timbalan Setiausaha Agung", "bil": "2"},

        {"position": "Bendahari Agung", "bil": "-"},
        {"position": "Timbalan Bendahari Agung", "bil": "1"},
        {"position": "Timbalan Bendahari Agung", "bil": "2"},

        {"position": "Pegawai Penerangan", "bil": "-"},
        {"position": "Timbalan Pegawai Penerangan", "bil": "1"},

        {"position": "Setiausaha Penganjur", "bil": "-"},
        {"position": "Timbalan Setiausaha Penganjur", "bil": "-"},

        {"position": "Ahli Majlis", "bil": "1"},
        {"position": "Ahli Majlis", "bil": "2"},
        {"position": "Ahli Majlis", "bil": "3"},
        {"position": "Ahli Majlis", "bil": "4"},
        {"position": "Ahli Majlis", "bil": "5"},
        {"position": "Ahli Majlis", "bil": "6"},
        {"position": "Ahli Majlis", "bil": "7"},
        {"position": "Ahli Majlis", "bil": "8"},
        {"position": "Ahli Majlis", "bil": "9"},
        {"position": "Ahli Majlis", "bil": "10"},
        {"position": "Ahli Majlis", "bil": "11"},
        {"position": "Ahli Majlis", "bil": "12"},
        {"position": "Ahli Majlis", "bil": "13"},
        {"position": "Ahli Majlis", "bil": "14"},
        {"position": "Ahli Majlis", "bil": "15"},
        {"position": "Ahli Majlis", "bil": "16"},
        {"position": "Ahli Majlis", "bil": "17"},
        {"position": "Ahli Majlis", "bil": "18"},
        {"position": "Ahli Majlis", "bil": "19"},
        {"position": "Ahli Majlis", "bil": "20"},
        {"position": "Ahli Majlis", "bil": "21"},
        {"position": "Ahli Majlis", "bil": "22"},
        {"position": "Ahli Majlis", "bil": "23"},
        {"position": "Ahli Majlis", "bil": "24"},
        {"position": "Ahli Majlis", "bil": "25"},
    ],

    "BAHAGIAN": [
        "Pengerusi Tetap",
        "Timbalan Pengerusi Tetap",
        "Ketua Bahagian",
        "Timbalan Ketua Bahagian",
        "Naib Ketua I",
        "Naib Ketua II",
        "Naib Ketua III",
        "Naib Ketua IV",
        "Naib Ketua (Pemuda)",
        "Naib Ketua (Wanita)",
        "Setiausaha",
        "Penolong Setiausaha",
        "Bendahari",
        "Penolong Bendahari",
        "Pegawai Penerangan",
        "Penolong Pegawai Penerangan",
        "Setiausaha Penganjur",
        "Penolong Setiausaha Penganjur",
        "Ahli Jawatankuasa Biasa (Generasi Muda)",
        "Ahli Jawatankuasa Biasa (Dipilih)",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa (Dilantik)",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
        "Ahli Jawatankuasa Biasa",
    ],

    "CAWANGAN": [
        "Pengerusi Tetap",
        "Timbalan Pengerusi Tetap",
        "Ketua Cawangan",
        "Timbalan Ketua Cawangan",
        "Naib Ketua (Pemuda)",
        "Naib Ketua (Wanita)",
        "Setiausaha",
        "Penolong Setiausaha",
        "Bendahari",
        "Penolong Bendahari",
        "Pegawai Penerangan",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
        "Ahli Jawatankuasa",
    ],
}


DOC_LABELS = {
    "MAJLIS_TERTINGGI": "Majlis Tertinggi Parti",
    "BAHAGIAN": "Bahagian",
    "CAWANGAN": "Cawangan",
}


def normalize_position_name(position):
    position = (position or "").strip()
    return POSITION_ALIASES.get(position, position)


def normalize_positions(doc_type):
    raw_positions = POSITION_PRESETS[doc_type]

    positions = []
    for index, item in enumerate(raw_positions, start=1):
        if isinstance(item, dict):
            positions.append({
                "position": item["position"],
                "bil": item["bil"],
                "candidate_name": "",
            })
        else:
            positions.append({
                "position": item,
                "bil": str(index),
                "candidate_name": "",
            })

    return positions


def get_document_query(doc_type, bahagian=None, cawangan=None):
    query = HierarchyDocument.query.filter_by(doc_type=doc_type)

    if doc_type == "BAHAGIAN":
        query = query.filter_by(bahagian=bahagian)

    elif doc_type == "CAWANGAN":
        query = query.filter_by(bahagian=bahagian, cawangan=cawangan)

    return query


def build_prefilled_positions(doc_type, existing_rows):
    positions = normalize_positions(doc_type)
    buckets = defaultdict(list)

    for row in existing_rows:
        normalized_position = normalize_position_name(row.position)
        buckets[normalized_position].append(row)

    for key in buckets:
        buckets[key].sort(key=lambda r: ((r.sort_order or 9999), r.id))

    for item in positions:
        position = item["position"]

        if buckets[position]:
            existing = buckets[position].pop(0)
            item["candidate_name"] = existing.candidate_name or ""

    return positions


@hierarchy_bp.route("/")
@login_required
def view_hierarchy():
    majlis = HierarchyDocument.query.filter_by(
        doc_type="MAJLIS_TERTINGGI"
    ).order_by(HierarchyDocument.sort_order, HierarchyDocument.id).all()

    bahagian_names = db.session.query(HierarchyDocument.bahagian)\
        .filter(HierarchyDocument.doc_type == "BAHAGIAN")\
        .filter(HierarchyDocument.bahagian.isnot(None))\
        .filter(HierarchyDocument.bahagian != "")\
        .distinct()\
        .order_by(HierarchyDocument.bahagian)\
        .all()

    cawangan_names = db.session.query(
        HierarchyDocument.cawangan,
        HierarchyDocument.bahagian
    )\
        .filter(HierarchyDocument.doc_type == "CAWANGAN")\
        .filter(HierarchyDocument.cawangan.isnot(None))\
        .filter(HierarchyDocument.cawangan != "")\
        .distinct()\
        .order_by(HierarchyDocument.bahagian, HierarchyDocument.cawangan)\
        .all()

    return render_template(
        "hierarchy/view_hierarchy.html",
        majlis=majlis,
        bahagian_names=bahagian_names,
        cawangan_names=cawangan_names
    )


@hierarchy_bp.route("/document")
@login_required
def document_view():
    doc_type = request.args.get("type")
    bahagian = request.args.get("bahagian")
    cawangan = request.args.get("cawangan")

    if not doc_type:
        flash("Please select a hierarchy document first.", "warning")
        return redirect(url_for("hierarchy.view_hierarchy"))

    doc_type = doc_type.upper()

    query = HierarchyDocument.query.filter_by(doc_type=doc_type)

    if bahagian:
        query = query.filter_by(bahagian=bahagian)

    if cawangan:
        query = query.filter_by(cawangan=cawangan)

    rows = query.order_by(
        HierarchyDocument.sort_order,
        HierarchyDocument.id
    ).all()

    grouped_rows = []
    seen = {}

    for row in rows:
        key = (row.position or "").strip()

        if key not in seen:
            group = {
                "position": key,
                "items": [],
                "sort_order": row.sort_order or 0
            }
            seen[key] = group
            grouped_rows.append(group)

        seen[key]["items"].append(row)

    term = rows[0].term if rows and rows[0].term else DEFAULT_TERM

    return render_template(
        "hierarchy/document_view.html",
        rows=rows,
        grouped_rows=grouped_rows,
        doc_type=doc_type,
        bahagian=bahagian,
        cawangan=cawangan,
        term=term,
    )


@hierarchy_bp.route("/admin")
@login_required
def admin_list():
    admin_required()

    rows = HierarchyDocument.query.order_by(
        HierarchyDocument.doc_type,
        HierarchyDocument.bahagian,
        HierarchyDocument.cawangan,
        HierarchyDocument.sort_order,
        HierarchyDocument.id
    ).all()

    return render_template("hierarchy/admin_list.html", rows=rows)


@hierarchy_bp.route("/admin/add")
@login_required
def admin_add_choice():
    admin_required()
    return render_template("hierarchy/admin_form.html", choose_mode=True)


@hierarchy_bp.route("/admin/add/<doc_type>", methods=["GET", "POST"])
@login_required
def admin_add(doc_type):
    admin_required()

    doc_type = doc_type.upper()

    if doc_type not in POSITION_PRESETS:
        abort(404)

    positions = normalize_positions(doc_type)
    doc_label = DOC_LABELS[doc_type]

    if request.method == "POST":
        title = request.form.get("title")
        term = (request.form.get("term") or DEFAULT_TERM).strip()
        bahagian = request.form.get("bahagian")
        cawangan = request.form.get("cawangan")
        meeting_date = request.form.get("meeting_date") or None

        submitted_positions = request.form.getlist("position[]")
        submitted_names = request.form.getlist("candidate_name[]")

        added_count = 0

        for index, position in enumerate(submitted_positions):
            candidate_name = submitted_names[index].strip() if index < len(submitted_names) else ""

            if not candidate_name:
                continue

            row = HierarchyDocument(
                doc_type=doc_type,
                title=title,
                term=term,
                bahagian=bahagian,
                cawangan=cawangan,
                meeting_date=meeting_date,
                position=position,
                candidate_name=candidate_name,
                sort_order=index + 1
            )

            db.session.add(row)
            added_count += 1

        if added_count == 0:
            flash("No names were entered. Please enter at least one name.", "warning")
            return render_template(
                "hierarchy/admin_form.html",
                choose_mode=False,
                edit_document_mode=False,
                doc_type=doc_type,
                doc_label=doc_label,
                positions=positions,
                title=title,
                term=term,
                bahagian=bahagian,
                cawangan=cawangan,
                meeting_date=meeting_date,
            )

        db.session.commit()
        flash(f"{doc_label} data saved successfully.", "success")
        return redirect(url_for("hierarchy.admin_list"))

    return render_template(
        "hierarchy/admin_form.html",
        choose_mode=False,
        edit_document_mode=False,
        doc_type=doc_type,
        doc_label=doc_label,
        positions=positions,
        title="",
        term=DEFAULT_TERM,
        bahagian="",
        cawangan="",
        meeting_date="",
    )


@hierarchy_bp.route("/admin/edit-document/<doc_type>", methods=["GET", "POST"])
@login_required
def admin_edit_document(doc_type):
    admin_required()

    doc_type = doc_type.upper()

    if doc_type not in POSITION_PRESETS:
        abort(404)

    doc_label = DOC_LABELS[doc_type]

    bahagian = request.args.get("bahagian") or ""
    cawangan = request.args.get("cawangan") or ""

    query = get_document_query(doc_type, bahagian=bahagian, cawangan=cawangan)

    existing_rows = query.order_by(
        HierarchyDocument.sort_order,
        HierarchyDocument.id
    ).all()

    if not existing_rows:
        flash("No existing hierarchy document found. You can create a new one here.", "warning")
        return redirect(url_for("hierarchy.admin_add", doc_type=doc_type))

    first_row = existing_rows[0]

    if request.method == "POST":
        title = request.form.get("title")
        term = (request.form.get("term") or DEFAULT_TERM).strip()
        new_bahagian = request.form.get("bahagian")
        new_cawangan = request.form.get("cawangan")
        meeting_date = request.form.get("meeting_date") or None

        submitted_positions = request.form.getlist("position[]")
        submitted_names = request.form.getlist("candidate_name[]")

        # Delete the old full document/group first
        for row in existing_rows:
            db.session.delete(row)

        added_count = 0

        # Re-create only rows that still have names.
        # Empty name means delete/unneeded position.
        for index, position in enumerate(submitted_positions):
            candidate_name = submitted_names[index].strip() if index < len(submitted_names) else ""

            if not candidate_name:
                continue

            row = HierarchyDocument(
                doc_type=doc_type,
                title=title,
                term=term,
                bahagian=new_bahagian,
                cawangan=new_cawangan if doc_type == "CAWANGAN" else None,
                meeting_date=meeting_date,
                position=position,
                candidate_name=candidate_name,
                sort_order=index + 1
            )

            db.session.add(row)
            added_count += 1

        db.session.commit()

        if added_count == 0:
            flash("All names were empty, so this hierarchy document was cleared.", "warning")
        else:
            flash(f"{doc_label} document updated successfully.", "success")

        return redirect(url_for("hierarchy.admin_list"))

    positions = build_prefilled_positions(doc_type, existing_rows)

    return render_template(
        "hierarchy/admin_form.html",
        choose_mode=False,
        edit_document_mode=True,
        doc_type=doc_type,
        doc_label=doc_label,
        positions=positions,
        title=first_row.title or "",
        term=first_row.term or DEFAULT_TERM,
        bahagian=first_row.bahagian or "",
        cawangan=first_row.cawangan or "",
        meeting_date=first_row.meeting_date or "",
    )


@hierarchy_bp.route("/admin/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit(id):
    admin_required()

    row = HierarchyDocument.query.get_or_404(id)

    if row.doc_type == "MAJLIS_TERTINGGI":
        return redirect(url_for(
            "hierarchy.admin_edit_document",
            doc_type=row.doc_type
        ))

    if row.doc_type == "BAHAGIAN":
        return redirect(url_for(
            "hierarchy.admin_edit_document",
            doc_type=row.doc_type,
            bahagian=row.bahagian
        ))

    if row.doc_type == "CAWANGAN":
        return redirect(url_for(
            "hierarchy.admin_edit_document",
            doc_type=row.doc_type,
            bahagian=row.bahagian,
            cawangan=row.cawangan
        ))

    abort(404)


@hierarchy_bp.route("/admin/delete-document/<doc_type>", methods=["POST"])
@login_required
def admin_delete_document(doc_type):
    admin_required()

    doc_type = (doc_type or "").upper()

    if doc_type not in POSITION_PRESETS:
        abort(404)

    bahagian = (request.form.get("bahagian") or "").strip()
    cawangan = (request.form.get("cawangan") or "").strip()

    query = HierarchyDocument.query.filter_by(doc_type=doc_type)

    if doc_type == "BAHAGIAN":
        if not bahagian:
            flash("Bahagian name is required to delete this form.", "danger")
            return redirect(url_for("hierarchy.admin_list"))

        query = query.filter_by(bahagian=bahagian)
        label = f"Bahagian form: {bahagian}"

    elif doc_type == "CAWANGAN":
        if not bahagian or not cawangan:
            flash("Bahagian and Cawangan name are required to delete this form.", "danger")
            return redirect(url_for("hierarchy.admin_list"))

        query = query.filter_by(bahagian=bahagian, cawangan=cawangan)
        label = f"Cawangan form: {cawangan} ({bahagian})"

    else:
        label = "Majlis Tertinggi form"

    rows = query.all()
    count = len(rows)

    for row in rows:
        db.session.delete(row)

    db.session.commit()

    flash(f"{label} deleted successfully. {count} records removed.", "warning")
    return redirect(url_for("hierarchy.admin_list"))


@hierarchy_bp.route("/admin/delete/<int:id>", methods=["POST"])
@login_required
def admin_delete(id):
    admin_required()

    row = HierarchyDocument.query.get_or_404(id)

    db.session.delete(row)
    db.session.commit()

    flash("Hierarchy data removed.", "warning")
    return redirect(url_for("hierarchy.admin_list"))
