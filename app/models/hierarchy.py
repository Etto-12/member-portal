from app.extensions import db


class HierarchyDocument(db.Model):
    __tablename__ = "hierarchy_documents"

    id = db.Column(db.Integer, primary_key=True)

    # Every saved election/form gets its own key.
    # Rows with the same document_key belong to one hierarchy document.
    document_key = db.Column(db.String(64), nullable=False, index=True)

    doc_type = db.Column(db.String(30), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    term = db.Column(db.Text)

    bahagian = db.Column(db.String(120))
    cawangan = db.Column(db.String(120))
    meeting_date = db.Column(db.Date)

    position = db.Column(db.String(200), nullable=False)
    bil = db.Column(db.String(30))
    candidate_name = db.Column(db.String(200), nullable=False)
    sort_order = db.Column(db.Integer, default=0)


class HierarchyFormPosition(db.Model):
    __tablename__ = "hierarchy_form_positions"

    id = db.Column(db.Integer, primary_key=True)
    doc_type = db.Column(db.String(30), nullable=False, index=True)
    position = db.Column(db.String(200), nullable=False)
    bil = db.Column(db.String(30))
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
