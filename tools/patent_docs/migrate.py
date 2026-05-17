"""
migrate.py — add patent_documents and patent_figures tables to patents.duckdb.
"""

from __future__ import annotations

import duckdb

DDL = """
CREATE TABLE IF NOT EXISTS patent_documents (
    patent_no       VARCHAR PRIMARY KEY,
    pdf_path        VARCHAR,
    pdf_fetched_at  TIMESTAMP,
    page_count      INTEGER,
    figure_count    INTEGER
);

CREATE TABLE IF NOT EXISTS patent_figures (
    patent_no          VARCHAR NOT NULL,
    figure_no          INTEGER NOT NULL,
    figure_path        VARCHAR,
    is_representative  BOOLEAN,
    PRIMARY KEY (patent_no, figure_no)
);
"""


def migrate(db_path: str) -> None:
    conn = duckdb.connect(db_path)
    conn.execute(DDL)
    conn.commit()
    conn.close()
    print(f"Migrated: {db_path}")
