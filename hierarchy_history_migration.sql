BEGIN;

ALTER TABLE hierarchy_documents
    ADD COLUMN IF NOT EXISTS document_key VARCHAR(64),
    ADD COLUMN IF NOT EXISTS bil VARCHAR(30);

-- Group legacy rows into separate saved documents using their existing metadata.
UPDATE hierarchy_documents
SET document_key = md5(concat_ws('|',
    COALESCE(doc_type,''),
    COALESCE(title,''),
    COALESCE(term,''),
    COALESCE(bahagian,''),
    COALESCE(cawangan,''),
    COALESCE(meeting_date::text,'')
))
WHERE document_key IS NULL OR document_key = '';

ALTER TABLE hierarchy_documents
    ALTER COLUMN document_key SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_hierarchy_documents_document_key
    ON hierarchy_documents(document_key);
CREATE INDEX IF NOT EXISTS ix_hierarchy_documents_doc_type
    ON hierarchy_documents(doc_type);

CREATE TABLE IF NOT EXISTS hierarchy_form_positions (
    id SERIAL PRIMARY KEY,
    doc_type VARCHAR(30) NOT NULL,
    position VARCHAR(200) NOT NULL,
    bil VARCHAR(30),
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_hierarchy_form_positions_doc_type
    ON hierarchy_form_positions(doc_type);

-- Seed current hard-coded layouts once.
INSERT INTO hierarchy_form_positions (doc_type, position, bil, sort_order, is_active)
SELECT * FROM (VALUES
    ('MAJLIS_TERTINGGI','Presiden','-',1,TRUE),
    ('MAJLIS_TERTINGGI','Timbalan Presiden','-',2,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','1',3,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','2',4,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','3',5,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','4',6,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','5',7,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','6',8,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','7',9,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','8 (W)',10,TRUE),
    ('MAJLIS_TERTINGGI','Naib Presiden','9 (P)',11,TRUE),
    ('MAJLIS_TERTINGGI','Setiausaha Agung','-',12,TRUE),
    ('MAJLIS_TERTINGGI','Timbalan Setiausaha Agung','1',13,TRUE),
    ('MAJLIS_TERTINGGI','Timbalan Setiausaha Agung','2',14,TRUE),
    ('MAJLIS_TERTINGGI','Bendahari Agung','-',15,TRUE),
    ('MAJLIS_TERTINGGI','Timbalan Bendahari Agung','1',16,TRUE),
    ('MAJLIS_TERTINGGI','Timbalan Bendahari Agung','2',17,TRUE),
    ('MAJLIS_TERTINGGI','Pegawai Penerangan','-',18,TRUE),
    ('MAJLIS_TERTINGGI','Timbalan Pegawai Penerangan','1',19,TRUE),
    ('MAJLIS_TERTINGGI','Setiausaha Penganjur','-',20,TRUE),
    ('MAJLIS_TERTINGGI','Timbalan Setiausaha Penganjur','-',21,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','1',22,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','2',23,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','3',24,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','4',25,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','5',26,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','6',27,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','7',28,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','8',29,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','9',30,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','10',31,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','11',32,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','12',33,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','13',34,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','14',35,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','15',36,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','16',37,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','17',38,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','18',39,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','19',40,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','20',41,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','21',42,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','22',43,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','23',44,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','24',45,TRUE),
    ('MAJLIS_TERTINGGI','Ahli Majlis','25',46,TRUE),
    ('BAHAGIAN','Pengerusi Tetap','1',1,TRUE),
    ('BAHAGIAN','Timbalan Pengerusi Tetap','2',2,TRUE),
    ('BAHAGIAN','Ketua Bahagian','3',3,TRUE),
    ('BAHAGIAN','Timbalan Ketua Bahagian','4',4,TRUE),
    ('BAHAGIAN','Naib Ketua I','5',5,TRUE),
    ('BAHAGIAN','Naib Ketua II','6',6,TRUE),
    ('BAHAGIAN','Naib Ketua III','7',7,TRUE),
    ('BAHAGIAN','Naib Ketua IV','8',8,TRUE),
    ('BAHAGIAN','Naib Ketua (Pemuda)','9',9,TRUE),
    ('BAHAGIAN','Naib Ketua (Wanita)','10',10,TRUE),
    ('BAHAGIAN','Setiausaha','11',11,TRUE),
    ('BAHAGIAN','Penolong Setiausaha','12',12,TRUE),
    ('BAHAGIAN','Bendahari','13',13,TRUE),
    ('BAHAGIAN','Penolong Bendahari','14',14,TRUE),
    ('BAHAGIAN','Pegawai Penerangan','15',15,TRUE),
    ('BAHAGIAN','Penolong Pegawai Penerangan','16',16,TRUE),
    ('BAHAGIAN','Setiausaha Penganjur','17',17,TRUE),
    ('BAHAGIAN','Penolong Setiausaha Penganjur','18',18,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa (Generasi Muda)','19',19,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa (Dipilih)','20',20,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','21',21,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','22',22,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','23',23,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','24',24,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','25',25,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','26',26,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','27',27,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','28',28,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','29',29,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa (Dilantik)','30',30,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','31',31,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','32',32,TRUE),
    ('BAHAGIAN','Ahli Jawatankuasa Biasa','33',33,TRUE),
    ('CAWANGAN','Pengerusi Tetap','1',1,TRUE),
    ('CAWANGAN','Timbalan Pengerusi Tetap','2',2,TRUE),
    ('CAWANGAN','Ketua Cawangan','3',3,TRUE),
    ('CAWANGAN','Timbalan Ketua Cawangan','4',4,TRUE),
    ('CAWANGAN','Naib Ketua (Pemuda)','5',5,TRUE),
    ('CAWANGAN','Naib Ketua (Wanita)','6',6,TRUE),
    ('CAWANGAN','Setiausaha','7',7,TRUE),
    ('CAWANGAN','Penolong Setiausaha','8',8,TRUE),
    ('CAWANGAN','Bendahari','9',9,TRUE),
    ('CAWANGAN','Penolong Bendahari','10',10,TRUE),
    ('CAWANGAN','Pegawai Penerangan','11',11,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','12',12,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','13',13,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','14',14,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','15',15,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','16',16,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','17',17,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','18',18,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','19',19,TRUE),
    ('CAWANGAN','Ahli Jawatankuasa','20',20,TRUE)
) AS seed(doc_type, position, bil, sort_order, is_active)
WHERE NOT EXISTS (
    SELECT 1 FROM hierarchy_form_positions existing
    WHERE existing.doc_type = seed.doc_type
);

-- Backfill Bil on legacy saved rows using the current layout and their existing sort order.
UPDATE hierarchy_documents hd
SET bil = fp.bil
FROM hierarchy_form_positions fp
WHERE hd.bil IS NULL
  AND fp.doc_type = hd.doc_type
  AND fp.sort_order = hd.sort_order;

COMMIT;
