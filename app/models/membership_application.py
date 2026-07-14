from datetime import datetime
from app.extensions import db


class MembershipApplication(db.Model):
    __bind_key__ = "applications"
    __tablename__ = "membership_applications"

    id = db.Column(db.Integer, primary_key=True)

    # ======================
    # WHO SUBMITTED THE FORM
    # Stored as plain values because this table is in separate DB
    # ======================
    submitted_by_user_id = db.Column(db.Integer, nullable=False, index=True)
    submitted_by_role = db.Column(db.String(20), nullable=False)  # cawangan | bahagian
    submitted_by_username = db.Column(db.String(80))

    # ======================
    # WORKFLOW STATUS
    # ======================
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    # pending | reviewed | approved | rejected

    admin_remarks = db.Column(db.Text)
    reviewed_by_admin_id = db.Column(db.Integer, nullable=True)
    reviewed_at = db.Column(db.DateTime)

    # Admin enters this only after checking the physical signed form
    approved_noid = db.Column(db.Integer, unique=True, nullable=True)

    # ======================
    # A. SAYA MEMOHON MENJADI AHLI PARTI DI
    # ======================
    apply_cawangan = db.Column(db.Text)
    apply_bahagian = db.Column(db.Text)
    apply_negeri = db.Column(db.Text)

    # ======================
    # B. BUTIR-BUTIR PEMOHON
    # ======================
    fullname = db.Column(db.Text, nullable=False)
    ic = db.Column(db.Text, nullable=False, index=True)
    old_ic = db.Column(db.Text)

    birthdate = db.Column(db.Date)
    jantina = db.Column(db.Text)
    warganegara = db.Column(db.Text, default="WARGANEGARA")
    bangsa = db.Column(db.Text)
    kelulusan_akademik = db.Column(db.Text)
    pekerjaan = db.Column(db.Text)

    alamat_surat = db.Column(db.Text)
    alamat_rumah = db.Column(db.Text)

    emel = db.Column(db.Text)
    notelefon_rumah = db.Column(db.Text)
    notelefon_pejabat = db.Column(db.Text)
    notelefon_hp = db.Column(db.Text)

    # ======================
    # C. PENGAKUAN PEMOHON
    # ======================
    pengakuan_accepted = db.Column(db.Boolean, default=False)

    # ======================
    # D. PUSAT PENGUNDIAN / SPR
    # ======================
    parlimen_spr = db.Column(db.Text)
    negeri_spr = db.Column(db.Text)
    daerah_mengundi = db.Column(db.Text)
    pusat_mengundi = db.Column(db.Text)

    # ======================
    # OPTIONAL MAIN MEMBER PORTAL MAPPING
    # No ForeignKey here because this DB is separate
    # ======================
    parlimen = db.Column(db.Text)
    daerah_id = db.Column(db.Integer, nullable=True)
    dun_id = db.Column(db.Integer, nullable=True)
    bahagian_id = db.Column(db.Integer, nullable=True)

    # ======================
    # E. SOKONGAN
    # ======================
    nama_pencadang = db.Column(db.Text)
    no_keahlian_pencadang = db.Column(db.Text)
    tarikh_sokongan = db.Column(db.Date)

    # ======================
    # F. UNTUK KEGUNAAN JAWATANKUASA CAWANGAN
    # ======================
    f_tarikh_diterima = db.Column(db.Date)
    f_tarikh_dikemukakan = db.Column(db.Date)
    f_nota = db.Column(db.Text)
    f_setiausaha_cawangan = db.Column(db.Text)
    f_signed = db.Column(db.Boolean, default=False)

    # ======================
    # G. UNTUK KEGUNAAN JAWATANKUASA BAHAGIAN
    # ======================
    g_tarikh_diterima = db.Column(db.Date)
    g_tarikh_dikemukakan = db.Column(db.Date)
    g_nota = db.Column(db.Text)
    g_setiausaha_bahagian = db.Column(db.Text)
    g_signed = db.Column(db.Boolean, default=False)

    # ======================
    # H. UNTUK KEGUNAAN IBU PEJABAT UPKO
    # Admin only
    # ======================
    h_tarikh_diterima = db.Column(db.Date)
    h_tarikh_diluluskan = db.Column(db.Date)
    h_tarikh_yuran = db.Column(db.Date)
    h_no_resit_yuran = db.Column(db.Text)
    h_no_keahlian = db.Column(db.Text)
    h_setiausaha_eksekutif = db.Column(db.Text)

    # ======================
    # TIMESTAMPS
    # ======================
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
