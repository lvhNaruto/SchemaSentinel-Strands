import sqlite3
from typing import Any, Dict, List, Tuple

class WarehouseDatabase:
    """Manages SQLite storage with unique constraints and ingestion tracking."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup_tables()

    def _setup_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tech_projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                source_url TEXT NOT NULL UNIQUE,
                relevance_score INTEGER NOT NULL,
                batch_id TEXT DEFAULT 'batch_clean',
                ingestion_status TEXT DEFAULT 'clean'
            )
            """
        )
        self.conn.commit()

    def get_table_schema(self, table_name: str = "tech_projects") -> str:
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = self.cursor.fetchall()
        return "\n".join([f"- {col[1]} ({col[2]}): NOT NULL={bool(col[3])}" for col in columns])

    def insert_record(self, record: Dict[str, Any], batch_id: str = "clean", status: str = "clean") -> bool:
        """Inserts record only if source_url does not already exist."""
        title = str(record["title"])
        author = str(record["author"])
        source_url = str(record["source_url"])
        score = int(record["relevance_score"])
        b_id = str(record.get("batch_id", batch_id))
        i_status = str(record.get("ingestion_status", status))

        # Check if URL already exists
        self.cursor.execute("SELECT 1 FROM tech_projects WHERE source_url = ?", (source_url,))
        if self.cursor.fetchone():
            return False  # Duplicate skipped

        query = """
            INSERT INTO tech_projects (title, author, source_url, relevance_score, batch_id, ingestion_status)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, (title, author, source_url, score, b_id, i_status))
        return True

    def insert_batch(self, batch: List[Dict[str, Any]], batch_id: str = "clean", status: str = "clean") -> Tuple[int, int]:
        """Inserts unique records, returning (inserted_count, skipped_duplicates)."""
        inserted = 0
        skipped = 0
        try:
            for record in batch:
                if self.insert_record(record, batch_id=batch_id, status=status):
                    inserted += 1
                else:
                    skipped += 1
            self.conn.commit()
            return inserted, skipped
        except Exception:
            self.conn.rollback()
            raise

    def get_all_rows(self) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT project_id, title, author, source_url, relevance_score, batch_id, ingestion_status FROM tech_projects ORDER BY project_id DESC")
        rows = self.cursor.fetchall()
        return [
            {
                "project_id": r[0],
                "title": r[1],
                "author": r[2],
                "source_url": r[3],
                "relevance_score": r[4],
                "batch_id": r[5],
                "ingestion_status": r[6]
            }
            for r in rows
        ]

    def count_records(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM tech_projects")
        return self.cursor.fetchone()[0]