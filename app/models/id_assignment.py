from datetime import datetime
from app.extensions import db


class IdAssignment(db.Model):
    __bind_key__ = "id_assignment"
    __tablename__ = "id_assignments"

    id = db.Column(db.Integer, primary_key=True)

    noid = db.Column(db.Integer, unique=True, nullable=False, index=True)

    is_assigned = db.Column(db.Boolean, nullable=False, default=False, index=True)

    assigned_by_user_id = db.Column(db.Integer, nullable=True)
    assigned_by_username = db.Column(db.String(120), nullable=True)
    assigned_color = db.Column(db.String(80), nullable=True)

    assigned_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
