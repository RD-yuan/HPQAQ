from __future__ import annotations
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence

class MiniSQL:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def exec(self, sql: str, params: Sequence[Any] = ()) -> int:
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.rowcount

    def exec_many(self, sql: str, seq_of_params: Iterable[Sequence[Any]]) -> int:
        with self.connect() as conn:
            cur = conn.executemany(sql, seq_of_params)
            conn.commit()
            return cur.rowcount

    def query_all(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None
