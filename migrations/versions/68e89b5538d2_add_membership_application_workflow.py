"""add membership application workflow

Revision ID: 68e89b5538d2
Revises: 001_add_hierarchy_documents
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "68e89b5538d2"
down_revision = "001_add_hierarchy_documents"
branch_labels = None
depends_on = None


def upgrade():
    # =========================
    # USERS TABLE - ADD APPLICATION ACCOUNT FIELDS
    # =========================
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bahagian_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("bahagian_name", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("cawangan_name", sa.String(length=150), nullable=True))

    op.create_foreign_key(
        "fk_users_bahagian_id_bahagian",
        "users",
        "bahagian",
        ["bahagian_id"],
        ["id"]
    )

    # =========================
    # MEMBERSHIP APPLICATIONS TABLE
    # =========================
    op.create_table(
        "membership_applications",

        sa.Column("id", sa.Integer(), nullable=False),

        # submitted by
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=False),
        sa.Column("submitted_by_role", sa.String(length=20), nullable=False),

        # status
        sa.Column("status", sa.String(length=30), nullable=True),
        sa.Column("admin_remarks", sa.Text(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),

        # approved member id
        sa.Column("approved_noid", sa.Integer(), nullable=True),

        # A. application area
        sa.Column("apply_cawangan", sa.Text(), nullable=True),
        sa.Column("apply_bahagian", sa.Text(), nullable=True),
        sa.Column("apply_negeri", sa.Text(), nullable=True),

        # B. applicant details
        sa.Column("fullname", sa.Text(), nullable=False),
        sa.Column("ic", sa.Text(), nullable=False),
        sa.Column("old_ic", sa.Text(), nullable=True),
        sa.Column("birthdate", sa.Date(), nullable=True),
        sa.Column("jantina", sa.Text(), nullable=True),
        sa.Column("warganegara", sa.Text(), nullable=True),
        sa.Column("bangsa", sa.Text(), nullable=True),
        sa.Column("kelulusan_akademik", sa.Text(), nullable=True),
        sa.Column("pekerjaan", sa.Text(), nullable=True),
        sa.Column("alamat_surat", sa.Text(), nullable=True),
        sa.Column("alamat_rumah", sa.Text(), nullable=True),
        sa.Column("emel", sa.Text(), nullable=True),
        sa.Column("notelefon_rumah", sa.Text(), nullable=True),
        sa.Column("notelefon_pejabat", sa.Text(), nullable=True),
        sa.Column("notelefon_hp", sa.Text(), nullable=True),

        # C. declaration
        sa.Column("pengakuan", sa.Boolean(), nullable=True),

        # D. voting centre
        sa.Column("parlimen_spr", sa.Text(), nullable=True),
        sa.Column("negeri_spr", sa.Text(), nullable=True),
        sa.Column("daerah_mengundi", sa.Text(), nullable=True),
        sa.Column("pusat_mengundi", sa.Text(), nullable=True),

        # Optional FK mapping to your existing structure
        sa.Column("bahagian_id", sa.Integer(), nullable=True),
        sa.Column("dun_id", sa.Integer(), nullable=True),
        sa.Column("daerah_id", sa.Integer(), nullable=True),

        # E. sokongan
        sa.Column("nama_pencadang", sa.Text(), nullable=True),
        sa.Column("no_keahlian_pencadang", sa.Text(), nullable=True),
        sa.Column("tarikh_sokongan", sa.Date(), nullable=True),

        # F. jawatankuasa cawangan
        sa.Column("f_tarikh_diterima", sa.Date(), nullable=True),
        sa.Column("f_tarikh_dikemukakan", sa.Date(), nullable=True),
        sa.Column("f_nota", sa.Text(), nullable=True),
        sa.Column("f_setiausaha_cawangan", sa.Text(), nullable=True),
        sa.Column("f_signed", sa.Boolean(), nullable=True),

        # G. jawatankuasa bahagian
        sa.Column("g_tarikh_diterima", sa.Date(), nullable=True),
        sa.Column("g_tarikh_dikemukakan", sa.Date(), nullable=True),
        sa.Column("g_nota", sa.Text(), nullable=True),
        sa.Column("g_setiausaha_bahagian", sa.Text(), nullable=True),
        sa.Column("g_signed", sa.Boolean(), nullable=True),

        # H. ibu pejabat / admin
        sa.Column("h_tarikh_diterima", sa.Date(), nullable=True),
        sa.Column("h_tarikh_diluluskan", sa.Date(), nullable=True),
        sa.Column("h_tarikh_yuran", sa.Date(), nullable=True),
        sa.Column("h_no_resit_yuran", sa.Text(), nullable=True),
        sa.Column("h_no_keahlian", sa.Text(), nullable=True),
        sa.Column("h_setiausaha_eksekutif", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=True),

        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["bahagian_id"], ["bahagian.id"]),
        sa.ForeignKeyConstraint(["dun_id"], ["dun.id"]),
        sa.ForeignKeyConstraint(["daerah_id"], ["daerah.id"]),

        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approved_noid")
    )

    op.create_index(
        "ix_membership_applications_ic",
        "membership_applications",
        ["ic"],
        unique=False
    )

    op.create_index(
        "ix_membership_applications_status",
        "membership_applications",
        ["status"],
        unique=False
    )

    op.create_index(
        "ix_membership_applications_submitted_by_user_id",
        "membership_applications",
        ["submitted_by_user_id"],
        unique=False
    )


def downgrade():
    op.drop_index(
        "ix_membership_applications_submitted_by_user_id",
        table_name="membership_applications"
    )
    op.drop_index(
        "ix_membership_applications_status",
        table_name="membership_applications"
    )
    op.drop_index(
        "ix_membership_applications_ic",
        table_name="membership_applications"
    )

    op.drop_table("membership_applications")

    op.drop_constraint(
        "fk_users_bahagian_id_bahagian",
        "users",
        type_="foreignkey"
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("cawangan_name")
        batch_op.drop_column("bahagian_name")
        batch_op.drop_column("bahagian_id")
