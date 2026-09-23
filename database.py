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

    def _column_exists(self, table: str, column: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table});")
            return any(row[1] == column for row in cursor.fetchall())

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
                    extra_metadata TEXT,
                    batch_id TEXT,
                    ingestion_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # 2. Enterprise Dead Letter Queue (DLQ) Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tech_projects_dlq (
                    dlq_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_payload TEXT NOT NULL,
                    failure_reason TEXT NOT NULL,
                    detected_keys TEXT,
                    batch_id TEXT,
                    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # 3. Learned Transformation Template Cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS template_cache (
                    signature TEXT PRIMARY KEY,
                    patch_code TEXT NOT NULL,
                    sample_record TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    occurrences INTEGER DEFAULT 1
                );
            """)
            conn.commit()

        # 4. Backfill new columns if the DB was created before this migration.
        for table, column, ddl in [
            ("tech_projects", "extra_metadata", "ALTER TABLE tech_projects ADD COLUMN extra_metadata TEXT"),
            ("tech_projects_dlq", "detected_keys", "ALTER TABLE tech_projects_dlq ADD COLUMN detected_keys TEXT"),
        ]:
            if not self._column_exists(table, column):
                try:
                    with self._get_conn() as conn:
                        conn.execute(ddl)
                        conn.commit()
                except sqlite3.OperationalError as e:
                    logger.warning("Migration warning for %s.%s: %s", table, column, e)

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
        core = {"title", "author", "source_url", "relevance_score"}
        meta = {"project_id", "batch_id", "ingestion_status", "created_at", "extra_metadata"}

        with self._get_conn() as conn:
            cursor = conn.cursor()
            for r in records:
                if not r.get("title") or not r.get("author") or not r.get("source_url") or r.get("relevance_score") is None:
                    raise ValueError(f"Schema violation: missing mandatory columns in record {r}")

                # Preserve unmapped fields in the side-car extra_metadata JSON column.
                explicit_extra = r.get("extra_metadata")
                unmapped = {k: v for k, v in r.items() if k not in core and k not in meta}
                if explicit_extra is not None:
                    try:
                        parsed = json.loads(explicit_extra) if isinstance(explicit_extra, str) else explicit_extra
                        if isinstance(parsed, dict):
                            parsed.update(unmapped)
                            extra_str = json.dumps(parsed)
                        else:
                            extra_str = json.dumps(unmapped)
                    except Exception:
                        extra_str = json.dumps(unmapped)
                elif unmapped:
                    extra_str = json.dumps(unmapped)
                else:
                    extra_str = None

                try:
                    cursor.execute("""
                        INSERT INTO tech_projects (title, author, source_url, relevance_score, extra_metadata, batch_id, ingestion_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(r["title"]).strip(),
                        str(r["author"]).strip(),
                        str(r["source_url"]).strip(),
                        int(r["relevance_score"]),
                        extra_str,
                        batch_id,
                        status
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    skipped += 1
            conn.commit()
        return inserted, skipped

    def insert_dlq(self, raw_record: Dict[str, Any], failure_reason: str, batch_id: str, detected_keys: str = ""):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tech_projects_dlq (raw_payload, failure_reason, detected_keys, batch_id)
                VALUES (?, ?, ?, ?)
            """, (json.dumps(raw_record), str(failure_reason), str(detected_keys), str(batch_id)))
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

    def get_template(self, signature: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT signature, patch_code, sample_record, first_seen, last_seen, occurrences
                FROM template_cache WHERE signature = ?
            """, (signature,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                try:
                    d["sample_record"] = json.loads(d["sample_record"]) if d["sample_record"] else {}
                except Exception:
                    d["sample_record"] = {}
                return d
            return None

    def save_template(self, signature: str, patch_code: str, sample_record: Dict[str, Any]) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO template_cache (signature, patch_code, sample_record)
                    VALUES (?, ?, ?)
                    ON CONFLICT(signature) DO UPDATE SET
                        patch_code = excluded.patch_code,
                        sample_record = excluded.sample_record,
                        last_seen = CURRENT_TIMESTAMP,
                        occurrences = occurrences + 1
                """, (signature, patch_code, json.dumps(sample_record)))
                conn.commit()
                return True
            except sqlite3.Error as e:
                logger.warning("Failed to save template %s: %s", signature, e)
                return False

    def increment_template_usage(self, signature: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE template_cache
                SET occurrences = occurrences + 1, last_seen = CURRENT_TIMESTAMP
                WHERE signature = ?
            """, (signature,))
            conn.commit()

    def get_all_templates(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT signature, patch_code, sample_record, first_seen, last_seen, occurrences
                FROM template_cache
                ORDER BY last_seen DESC
            """)
            rows = []
            for row in cursor.fetchall():
                d = dict(row)
                try:
                    d["sample_record"] = json.loads(d["sample_record"]) if d["sample_record"] else {}
                except Exception:
                    d["sample_record"] = {}
                rows.append(d)
            return rows

    def clear_all(self) -> None:
        """Truncate warehouse + DLQ tables (used by the dashboard reset action).
        Additive helper only — existing insert/read semantics are untouched."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tech_projects")
            cursor.execute("DELETE FROM tech_projects_dlq")
            conn.commit()