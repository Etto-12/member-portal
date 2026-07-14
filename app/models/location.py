from app.extensions import db


class Parlimen(db.Model):
    __tablename__ = "parlimen"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)


# ✅ NEW — POLITICAL DAERAH
class Daerah(db.Model):
    __tablename__ = "daerah"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    parlimen_id = db.Column(db.Integer, db.ForeignKey("parlimen.id"), nullable=False)
    parlimen = db.relationship("Parlimen", backref="daerahs")

    __table_args__ = (
        db.UniqueConstraint("parlimen_id", "name", name="uq_daerah_parlimen"),
    )


# ✅ INDEPENDENT ORGANISATION UNIT
class Bahagian(db.Model):
    __tablename__ = "bahagian"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)


from app.extensions import db

class Dun(db.Model):
    __tablename__ = "dun"

    id = db.Column(db.Integer, primary_key=True)
    daerah_id = db.Column(
        db.Integer,
        db.ForeignKey("daerah.id"),
        nullable=False
    )
    name = db.Column(db.Text, nullable=False)

    daerah = db.relationship("Daerah", backref="duns")

    __table_args__ = (
        db.UniqueConstraint("daerah_id", "name", name="dun_unique"),
    )


class Cawangan(db.Model):
    __tablename__ = "cawangan"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)


class PusatMengundi(db.Model):
    __tablename__ = "pusat_mengundi"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
