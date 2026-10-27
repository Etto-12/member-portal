from app.extensions import db


class HierarchyDocument(db.Model):
    __tablename__ = "hierarchy_documents"

    id = db.Column(db.Integer, primary_key=True)

    doc_type = db.Column(
        db.String(30),
        nullable=False
    )  # MAJLIS_TERTINGGI / WANITA / GENERASI_MUDA / PEMUDA / BAHAGIAN / CAWANGAN

    title = db.Column(db.String(200), nullable=False)

    # Editable subtitle / penggal text
    term = db.Column(db.Text)

    bahagian = db.Column(db.String(120))
    cawangan = db.Column(db.String(120))
    meeting_date = db.Column(db.Date)

    position = db.Column(db.String(200), nullable=False)
    candidate_name = db.Column(db.String(200), nullable=False)

    sort_order = db.Column(db.Integer, default=0)
