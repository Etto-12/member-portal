from app.extensions import db


class Member(db.Model):
    __tablename__ = "members"

    # ======================
    # PRIMARY KEY
    # ======================
    id = db.Column(db.BigInteger, primary_key=True)

    # ======================
    # CORE IDENTIFIERS
    # ======================
    ic = db.Column(db.Text, index=True, nullable=True)
    noid = db.Column(db.Integer, index=True, nullable=True)

    # ======================
    # PERSONAL INFO
    # ======================
    title = db.Column(db.Text)
    fullname = db.Column(db.Text)
    jantina = db.Column(db.Text)
    birthdate = db.Column(db.Date)
    warganegara = db.Column(db.Text, nullable=False, default="WARGANEGARA")
    bangsa = db.Column(db.Text)
    kelulusan_akademik = db.Column(db.Text)
    pekerjaan = db.Column(db.Text)
    alamat = db.Column(db.Text)
    emel = db.Column(db.Text)
    notelefon = db.Column(db.Text)
    registration_date = db.Column(db.Date)
    memberstatus = db.Column(db.Text)

    # ======================
    # TEXT LOCATION / STRUCTURE
    # ======================
    negeri = db.Column(db.Text)

    # UPKO / organisation side
    parlimen = db.Column(db.Text)
    bahagian = db.Column(db.Text)
    dun = db.Column(db.Text)
    cawangan = db.Column(db.Text)
    pusatmengundi = db.Column(db.Text)

    # SPR side (separate)
    parlimen_spr = db.Column(db.Text)
    daerah_spr = db.Column(db.Text)
    dun_spr = db.Column(db.Text)

    # ======================
    # FK LOCATION / STRUCTURE
    # ======================
    daerah_id = db.Column(
        db.Integer,
        db.ForeignKey("daerah.id"),
        nullable=True
    )

    dun_id = db.Column(
        db.Integer,
        db.ForeignKey("dun.id"),
        nullable=True
    )

    cawangan_id = db.Column(db.Integer, nullable=True)
    pusat_mengundi_id = db.Column(db.Integer, nullable=True)

    bahagian_id = db.Column(
        db.Integer,
        db.ForeignKey("bahagian.id"),
        nullable=True
    )

    # ======================
    # RELATIONSHIPS
    # ======================
    daerah_rel = db.relationship("Daerah", foreign_keys=[daerah_id])
    dun_rel = db.relationship("Dun", foreign_keys=[dun_id])
    bahagian_rel = db.relationship("Bahagian", foreign_keys=[bahagian_id])

    # ======================
    # HELPER PROPERTIES
    # ======================
    @property
    def daerah_name(self):
        return self.daerah_rel.name if self.daerah_rel else None

    @property
    def dun_fk_name(self):
        return self.dun_rel.name if self.dun_rel else None

    @property
    def bahagian_fk_name(self):
        return self.bahagian_rel.name if self.bahagian_rel else None

    # ======================
    # HELPERS
    # ======================
    def __repr__(self):
        return (
            f"<Member id={self.id} noid={self.noid} "
            f"ic={self.ic} fullname={self.fullname}>"
        )
