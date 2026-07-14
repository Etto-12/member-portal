import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from app import create_app
from app.extensions import db
from app.models.member import Member

CSV_FILE = "Members.csv"
CHUNK_SIZE = 500


def safe_date(val):
    try:
        if pd.isna(val):
            return None
        dt = pd.to_datetime(val, errors="coerce", dayfirst=True)
        if pd.isna(dt):
            return None
        return dt.date()
    except Exception:
        return None


app = create_app()

with app.app_context():
    print("📄 Reading CSV...")
    df = pd.read_csv(CSV_FILE, encoding="latin-1", low_memory=False)
    print(f"📄 Loaded {len(df)} rows")

    df = df.where(pd.notnull(df), None)

    # Normalize IC
    df["IC"] = (
        df["IC"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )
    df.loc[df["IC"].isin(["None", "nan", "NaN", ""]), "IC"] = None

    # Date fields
    for col in ["BirthDate", "registration_date"]:
        if col in df.columns:
            df[col] = df[col].apply(safe_date)

    # Status cleanup
    if "MemberStatus" in df.columns:
        df["MemberStatus"] = df["MemberStatus"].fillna("Aktif")

    total_inserted = 0
    total_skipped = 0

    for start in range(0, len(df), CHUNK_SIZE):
        chunk = df.iloc[start:start + CHUNK_SIZE]
        rows = chunk.to_dict(orient="records")

        # Skip rows without IC
        rows = [r for r in rows if r.get("IC")]

        if not rows:
            continue

        stmt = insert(Member).values(rows).on_conflict_do_nothing(
            index_elements=["IC"]
        )

        try:
            result = db.session.execute(stmt)
            db.session.commit()

            inserted = result.rowcount or 0
            total_inserted += inserted
            total_skipped += len(rows) - inserted

            print(
                f"✅ {start + len(chunk):>7}/{len(df)} "
                f"Inserted: {total_inserted}  Skipped: {total_skipped}"
            )

        except Exception as e:
            db.session.rollback()
            print(f"❌ Chunk failed at rows {start}-{start + CHUNK_SIZE}")
            print(str(e))
            total_skipped += len(rows)

    print("\n🎉 IMPORT COMPLETE")
    print(f"✅ Inserted: {total_inserted}")
    print(f"⚠️ Skipped:  {total_skipped}")
