from collections import defaultdict
from datetime import datetime
import re
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.hierarchy import HierarchyDocument, HierarchyFormPosition


hierarchy_bp = Blueprint("hierarchy", __name__, url_prefix="/hierarchy")


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


DEFAULT_TERM = "UPKO Bagi Penggal 2026 – 2029"


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


def format_term_for_display(value):
    raw = (value or DEFAULT_TERM or "").strip()
    raw = re.sub(
        r"^\s*UPKO\s+Bagi\s+Penggal\s+",
        "Penggal ",
        raw,
        flags=re.IGNORECASE,
    )
    raw = re.sub(
        r"(?<!\d)(\d{2})\s*[-–]\s*(\d{2})(?!\d)",
        lambda m: f"20{m.group(1)}–20{m.group(2)}",
        raw,
    )
    raw = re.sub(
        r"(?<!\d)(\d{4})\s*[-–]\s*(\d{4})(?!\d)",
        r"\1–\2",
        raw,
    )
    return re.sub(r"\s+", " ", raw).strip()


def fallback_layout(doc_type):
    raw_positions = POSITION_PRESETS[doc_type]
    rows = []
    for index, item in enumerate(raw_positions, start=1):
        if isinstance(item, dict):
            rows.append({
                "position": item["position"],
                "bil": item.get("bil") or "",
                "sort_order": index,
                "candidate_name": "",
            })
        else:
            rows.append({
                "position": item,
                "bil": str(index),
                "sort_order": index,
                "candidate_name": "",
            })
    return rows


def get_layout_positions(doc_type):
    rows = (
        HierarchyFormPosition.query
        .filter_by(doc_type=doc_type, is_active=True)
        .order_by(HierarchyFormPosition.sort_order, HierarchyFormPosition.id)
        .all()
    )

    if not rows:
        return fallback_layout(doc_type)

    return [
        {
            "position": row.position,
            "bil": row.bil or "",
            "sort_order": row.sort_order or 0,
            "candidate_name": "",
        }
        for row in rows
    ]


def get_document_rows(document_key):
    return (
        HierarchyDocument.query
        .filter_by(document_key=document_key)
        .order_by(HierarchyDocument.sort_order, HierarchyDocument.id)
        .all()
    )


def build_edit_positions(existing_rows):
    return [
        {
            "position": row.position,
            "bil": row.bil or "",
            "sort_order": row.sort_order or index,
            "candidate_name": row.candidate_name or "",
        }
        for index, row in enumerate(existing_rows, start=1)
    ]


def build_document_summary(rows):
    if not rows:
        return None

    first = rows[0]
    grouped = []
    seen = {}

    for row in rows:
        position = normalize_position_name(row.position)
        if position not in seen:
            group = {"position": position, "items": []}
            seen[position] = group
            grouped.append(group)
        seen[position]["items"].append(row)

    preview = []
    preview_limit = 4 if first.doc_type == "MAJLIS_TERTINGGI" else 3
    for group in grouped[:preview_limit]:
        preview.append({
            "position": group["position"],
            "name": group["items"][0].candidate_name,
            "more_count": max(len(group["items"]) - 1, 0),
        })

    search_parts = [
        first.title or "", first.term or "", first.bahagian or "", first.cawangan or ""
    ]
    for row in rows:
        search_parts.extend([row.position or "", row.candidate_name or "", row.bil or ""])

    return {
        "document_key": first.document_key,
        "doc_type": first.doc_type,
        "title": first.title,
        "term": format_term_for_display(first.term),
        "raw_term": first.term or "",
        "meeting_date": first.meeting_date,
        "bahagian": first.bahagian,
        "cawangan": first.cawangan,
        "preview": preview,
        "rows": rows,
        "count": len(rows),
        "href": url_for("hierarchy.document_view", document_key=first.document_key),
        "search_text": " ".join(search_parts).lower(),
    }


def all_documents():
    rows = (
        HierarchyDocument.query
        .order_by(
            HierarchyDocument.doc_type,
            HierarchyDocument.term,
            HierarchyDocument.bahagian,
            HierarchyDocument.cawangan,
            HierarchyDocument.sort_order,
            HierarchyDocument.id,
        )
        .all()
    )

    grouped = defaultdict(list)
    for row in rows:
        grouped[row.document_key].append(row)

    docs = [build_document_summary(group_rows) for group_rows in grouped.values()]
    docs = [doc for doc in docs if doc]

    def doc_sort(doc):
        meeting = doc["meeting_date"] or datetime.min.date()
        return (meeting, doc["raw_term"], doc["title"])

    docs.sort(key=doc_sort, reverse=True)
    return docs


def validate_header_fields(doc_type):
    title = (request.form.get("title") or "").strip()
    term = (request.form.get("term") or DEFAULT_TERM).strip()
    bahagian = (request.form.get("bahagian") or "").strip().upper()
    cawangan = (request.form.get("cawangan") or "").strip().upper()
    meeting_date = request.form.get("meeting_date") or None

    if not title:
        return None, "Title is required."
    if not term:
        return None, "Penggal / Subtitle is required."
    if doc_type in ("BAHAGIAN", "CAWANGAN") and not bahagian:
        return None, "Bahagian is required."
    if doc_type == "CAWANGAN" and not cawangan:
        return None, "Cawangan is required."

    return {
        "title": title,
        "term": term,
        "bahagian": bahagian or None,
        "cawangan": cawangan if doc_type == "CAWANGAN" else None,
        "meeting_date": meeting_date,
    }, None


def posted_position_rows():
    positions = request.form.getlist("position[]")
    bils = request.form.getlist("bil[]")
    names = request.form.getlist("candidate_name[]")

    rows = []
    for index, position in enumerate(positions, start=1):
        position = (position or "").strip()
        bil = (bils[index - 1] if index - 1 < len(bils) else "").strip()
        name = (names[index - 1] if index - 1 < len(names) else "").strip()

        if not position or not name:
            continue

        rows.append({
            "position": position,
            "bil": bil,
            "candidate_name": name,
            "sort_order": index,
        })

    return rows


@hierarchy_bp.route("/")
@login_required
def view_hierarchy():
    docs = all_documents()
    central_documents = [d for d in docs if d["doc_type"] == "MAJLIS_TERTINGGI"]
    bahagian_documents = [d for d in docs if d["doc_type"] == "BAHAGIAN"]
    cawangan_documents = [d for d in docs if d["doc_type"] == "CAWANGAN"]

    return render_template(
        "hierarchy/view_hierarchy.html",
        central_documents=central_documents,
        bahagian_documents=bahagian_documents,
        cawangan_documents=cawangan_documents,
        central_count=len(central_documents),
        bahagian_count=len(bahagian_documents),
        cawangan_count=len(cawangan_documents),
    )


@hierarchy_bp.route("/document/<document_key>")
@login_required
def document_view(document_key):
    rows = get_document_rows(document_key)
    if not rows:
        abort(404)

    first = rows[0]
    grouped_rows = []
    seen = {}

    for row in rows:
        key = normalize_position_name(row.position)
        if key not in seen:
            group = {"position": key, "items": [], "sort_order": row.sort_order or 0}
            seen[key] = group
            grouped_rows.append(group)
        seen[key]["items"].append(row)

    return render_template(
        "hierarchy/document_view.html",
        rows=rows,
        grouped_rows=grouped_rows,
        doc_type=first.doc_type,
        bahagian=first.bahagian,
        cawangan=first.cawangan,
        document_title=first.title,
        term=format_term_for_display(first.term),
        meeting_date=first.meeting_date,
    )


@hierarchy_bp.route("/admin")
@login_required
def admin_list():
    admin_required()
    docs = all_documents()

    documents_by_type = {
        "MAJLIS_TERTINGGI": [d for d in docs if d["doc_type"] == "MAJLIS_TERTINGGI"],
        "BAHAGIAN": [d for d in docs if d["doc_type"] == "BAHAGIAN"],
        "CAWANGAN": [d for d in docs if d["doc_type"] == "CAWANGAN"],
    }

    return render_template(
        "hierarchy/admin_list.html",
        documents_by_type=documents_by_type,
        doc_labels=DOC_LABELS,
    )


@hierarchy_bp.route("/admin/add")
@login_required
def admin_add_choice():
    admin_required()
    return render_template("hierarchy/admin_form.html", choose_mode=True)


@hierarchy_bp.route("/admin/add/<doc_type>", methods=["GET", "POST"])
@login_required
def admin_add(doc_type):
    admin_required()
    doc_type = (doc_type or "").upper()
    if doc_type not in POSITION_PRESETS:
        abort(404)

    positions = get_layout_positions(doc_type)
    doc_label = DOC_LABELS[doc_type]

    if request.method == "POST":
        header, error = validate_header_fields(doc_type)
        if error:
            flash(error, "danger")
            return render_template(
                "hierarchy/admin_form.html",
                choose_mode=False,
                edit_document_mode=False,
                doc_type=doc_type,
                doc_label=doc_label,
                positions=positions,
                title=request.form.get("title", ""),
                term=request.form.get("term", DEFAULT_TERM),
                bahagian=request.form.get("bahagian", ""),
                cawangan=request.form.get("cawangan", ""),
                meeting_date=request.form.get("meeting_date", ""),
            )

        submitted = posted_position_rows()
        if not submitted:
            flash("Enter at least one name before saving the hierarchy document.", "warning")
            return render_template(
                "hierarchy/admin_form.html",
                choose_mode=False,
                edit_document_mode=False,
                doc_type=doc_type,
                doc_label=doc_label,
                positions=positions,
                title=header["title"],
                term=header["term"],
                bahagian=header["bahagian"] or "",
                cawangan=header["cawangan"] or "",
                meeting_date=header["meeting_date"] or "",
            )

        document_key = uuid.uuid4().hex
        for item in submitted:
            db.session.add(HierarchyDocument(
                document_key=document_key,
                doc_type=doc_type,
                title=header["title"],
                term=header["term"],
                bahagian=header["bahagian"],
                cawangan=header["cawangan"],
                meeting_date=header["meeting_date"],
                position=item["position"],
                bil=item["bil"],
                candidate_name=item["candidate_name"],
                sort_order=item["sort_order"],
            ))

        db.session.commit()
        flash(f"{doc_label} saved as a NEW hierarchy document. Older election records were kept.", "success")
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


@hierarchy_bp.route("/admin/edit-document/<document_key>", methods=["GET", "POST"])
@login_required
def admin_edit_document(document_key):
    admin_required()
    existing_rows = get_document_rows(document_key)
    if not existing_rows:
        abort(404)

    first = existing_rows[0]
    doc_type = first.doc_type
    doc_label = DOC_LABELS.get(doc_type, doc_type)

    if request.method == "POST":
        header, error = validate_header_fields(doc_type)
        if error:
            flash(error, "danger")
            return render_template(
                "hierarchy/admin_form.html",
                choose_mode=False,
                edit_document_mode=True,
                document_key=document_key,
                doc_type=doc_type,
                doc_label=doc_label,
                positions=build_edit_positions(existing_rows),
                title=request.form.get("title", first.title),
                term=request.form.get("term", first.term or DEFAULT_TERM),
                bahagian=request.form.get("bahagian", first.bahagian or ""),
                cawangan=request.form.get("cawangan", first.cawangan or ""),
                meeting_date=request.form.get("meeting_date", first.meeting_date or ""),
            )

        submitted = posted_position_rows()
        if not submitted:
            flash("A saved document must contain at least one named position.", "danger")
            return redirect(request.url)

        for row in existing_rows:
            db.session.delete(row)

        for item in submitted:
            db.session.add(HierarchyDocument(
                document_key=document_key,
                doc_type=doc_type,
                title=header["title"],
                term=header["term"],
                bahagian=header["bahagian"],
                cawangan=header["cawangan"],
                meeting_date=header["meeting_date"],
                position=item["position"],
                bil=item["bil"],
                candidate_name=item["candidate_name"],
                sort_order=item["sort_order"],
            ))

        db.session.commit()
        flash("This hierarchy document was updated. Other election documents were not changed.", "success")
        return redirect(url_for("hierarchy.admin_list"))

    return render_template(
        "hierarchy/admin_form.html",
        choose_mode=False,
        edit_document_mode=True,
        document_key=document_key,
        doc_type=doc_type,
        doc_label=doc_label,
        positions=build_edit_positions(existing_rows),
        title=first.title or "",
        term=first.term or DEFAULT_TERM,
        bahagian=first.bahagian or "",
        cawangan=first.cawangan or "",
        meeting_date=first.meeting_date or "",
    )


@hierarchy_bp.route("/admin/form-layout/<doc_type>", methods=["GET", "POST"])
@login_required
def admin_form_layout(doc_type):
    admin_required()
    doc_type = (doc_type or "").upper()
    if doc_type not in POSITION_PRESETS:
        abort(404)

    if request.method == "POST":
        positions = request.form.getlist("position[]")
        bils = request.form.getlist("bil[]")

        submitted = []
        for index, position in enumerate(positions, start=1):
            position = (position or "").strip()
            bil = (bils[index - 1] if index - 1 < len(bils) else "").strip()
            if not position:
                continue
            submitted.append((position, bil))

        if not submitted:
            flash("The form layout must contain at least one Jawatan row.", "danger")
            return redirect(request.url)

        HierarchyFormPosition.query.filter_by(doc_type=doc_type).delete(synchronize_session=False)

        for index, (position, bil) in enumerate(submitted, start=1):
            db.session.add(HierarchyFormPosition(
                doc_type=doc_type,
                position=position,
                bil=bil,
                sort_order=index,
                is_active=True,
            ))

        db.session.commit()
        flash("Jawatan/Bil form layout updated. Existing saved election documents were not changed.", "success")
        return redirect(url_for("hierarchy.admin_form_layout", doc_type=doc_type))

    rows = get_layout_positions(doc_type)
    return render_template(
        "hierarchy/form_layout.html",
        doc_type=doc_type,
        doc_label=DOC_LABELS[doc_type],
        rows=rows,
    )


@hierarchy_bp.route("/admin/edit/<int:id>")
@login_required
def admin_edit(id):
    admin_required()
    row = HierarchyDocument.query.get_or_404(id)
    return redirect(url_for("hierarchy.admin_edit_document", document_key=row.document_key))


@hierarchy_bp.route("/admin/delete-document/<document_key>", methods=["POST"])
@login_required
def admin_delete_document(document_key):
    admin_required()
    rows = get_document_rows(document_key)
    if not rows:
        abort(404)

    label = rows[0].title
    count = len(rows)
    for row in rows:
        db.session.delete(row)
    db.session.commit()

    flash(f"Deleted hierarchy document '{label}' ({count} rows). Other election documents were kept.", "warning")
    return redirect(url_for("hierarchy.admin_list"))


@hierarchy_bp.route("/admin/delete/<int:id>", methods=["POST"])
@login_required
def admin_delete(id):
    admin_required()
    row = HierarchyDocument.query.get_or_404(id)
    document_key = row.document_key
    db.session.delete(row)
    db.session.commit()

    if not HierarchyDocument.query.filter_by(document_key=document_key).first():
        flash("The row was deleted and that document is now empty.", "warning")
    else:
        flash("Hierarchy row deleted.", "warning")
    return redirect(url_for("hierarchy.admin_list"))
