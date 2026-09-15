import sqlite3
import json
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("SchemaSentinel.Database")

class WarehouseDatabase:
    def __init__(self, db_path: str = "warehouse.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 1. Main Conformed Warehouse Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tech_projects (
                    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    source_url TEXT UNIQUE NOT NULL,
                    relevance_score INTEGER NOT NULL,
                    batch_id TEXT,
                    ingestion_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # 2. Enterprise Dead Letter Queue (DLQ) Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tech_projects_dlq (
                    dlq_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_payload TEXT,
                    failure_reason TEXT,
                    batch_id TEXT,
                    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def get_table_schema(self, table_name: str = "tech_projects") -> str:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema_lines = [f"Table: {table_name}"]
            for col in columns:
                schema_lines.append(f"- {col[1]} ({col[2]}): NOT NULL={bool(col[3])}")
            return "\n".join(schema_lines)

    def insert_batch(self, records: List[Dict[str, Any]], batch_id: str = "unknown", status: str = "clean") -> Tuple[int, int]:
        inserted, skipped = 0, 0
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for r in records:
                if not r.get("title") or not r.get("author") or not r.get("source_url") or r.get("relevance_score") is None:
                    raise ValueError(f"Schema violation: missing mandatory columns in record {r}")

                try:
                    cursor.execute("""
                        INSERT INTO tech_projects (title, author, source_url, relevance_score, batch_id, ingestion_status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(r["title"]).strip(),
                        str(r["author"]).strip(),
                        str(r["source_url"]).strip(),
                        int(r["relevance_score"]),
                        batch_id,
                        status
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    skipped += 1
            conn.commit()
        return inserted, skipped

    def insert_dlq(self, raw_record: Dict[str, Any], failure_reason: str, batch_id: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tech_projects_dlq (raw_payload, failure_reason, batch_id)
                VALUES (?, ?, ?)
            """, (json.dumps(raw_record), str(failure_reason), str(batch_id)))
            conn.commit()

    def get_all_rows(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tech_projects ORDER BY project_id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_dlq_rows(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tech_projects_dlq ORDER BY dlq_id DESC")
            return [dict(row) for row in cursor.fetchall()]