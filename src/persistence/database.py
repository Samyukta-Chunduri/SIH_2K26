"""Q-SHIELD — SQLite Database Management & Schema Initialization (Milestone M19-A).

Provides thread-safe connection factories, schema migrations, and index management
for the Q-SHIELD local SQLite persistence layer.
"""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import threading
from typing import Final

DEFAULT_DB_PATH: Final[str] = "qshield_events.db"

SCHEMA_SQL: Final[str] = """
-- 1. Security Events Table (M12 Decisions)
CREATE TABLE IF NOT EXISTS security_events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK(verdict IN ('ACCEPT', 'SUSPICIOUS', 'ATTACK')),
    primary_reason TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    session_id TEXT,
    scenario_id TEXT,
    configuration_hash TEXT,
    policy_id TEXT,
    exceeded_count INTEGER NOT NULL DEFAULT 0,
    is_explicit_violation INTEGER NOT NULL DEFAULT 0,
    is_evidence_complete INTEGER NOT NULL DEFAULT 1,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_session ON security_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_verdict ON security_events(verdict);
CREATE INDEX IF NOT EXISTS idx_events_config ON security_events(configuration_hash);

-- 2. Evidence Records Table (M13, M14, M15, M16)
CREATE TABLE IF NOT EXISTS evidence_records (
    record_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('IMPERSONATION', 'AUTHORIZATION', 'QUANTUM_CHANNEL', 'FUSION')),
    status TEXT NOT NULL,
    primary_reason TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    violations_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY(event_id) REFERENCES security_events(event_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_evidence_event_id ON evidence_records(event_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence_records(source);

-- 3. Evaluation Runs Table (M17)
CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    session_id TEXT,
    total_scenarios INTEGER NOT NULL,
    passed_scenarios INTEGER NOT NULL,
    failed_scenarios INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    confusion_matrix_json TEXT NOT NULL DEFAULT '{}',
    category_summaries_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_eval_runs_timestamp ON evaluation_runs(timestamp);

-- 4. Evaluation Scenario Results Table (M17)
CREATE TABLE IF NOT EXISTS evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    category TEXT NOT NULL,
    expected_verdict TEXT NOT NULL,
    observed_verdict TEXT NOT NULL,
    passed INTEGER NOT NULL,
    mismatch_reason TEXT,
    violations_json TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_eval_results_run_id ON evaluation_results(run_id);

-- 5. Benchmark Runs Table (M18)
CREATE TABLE IF NOT EXISTS benchmark_runs (
    run_id TEXT PRIMARY KEY,
    suite_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    total_benchmarks INTEGER NOT NULL,
    successful_benchmarks INTEGER NOT NULL,
    failed_benchmarks INTEGER NOT NULL,
    total_elapsed_seconds REAL NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_bench_runs_timestamp ON benchmark_runs(timestamp);

-- 6. Benchmark Results Table (M18)
CREATE TABLE IF NOT EXISTS benchmark_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    benchmark_id TEXT NOT NULL,
    category TEXT NOT NULL,
    workload_size INTEGER NOT NULL,
    iterations INTEGER NOT NULL,
    total_elapsed_seconds REAL NOT NULL,
    cpu_time_seconds REAL,
    mean_latency_seconds REAL,
    min_latency_seconds REAL,
    max_latency_seconds REAL,
    median_latency_seconds REAL,
    p95_latency_seconds REAL,
    throughput_ops_per_sec REAL,
    observed_verdicts_json TEXT NOT NULL DEFAULT '{}',
    errors_json TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(run_id) REFERENCES benchmark_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bench_results_run_id ON benchmark_results(run_id);
"""


from contextlib import contextmanager
from typing import Generator

class DatabaseManager:
    """Manages SQLite database connections and schema lifecycles."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """Initialize database manager with target SQLite database path.

        Args:
            db_path: Path to SQLite database file or ':memory:' for transient test databases.
        """
        self.db_path = db_path
        self._ensure_parent_directory()
        self._lock = threading.RLock()
        self._mem_conn: sqlite3.Connection | None = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", timeout=10.0, check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON;")
        self.init_schema()

    def _ensure_parent_directory(self) -> None:
        """Ensure parent directory exists for file-backed databases."""
        if self.db_path != ":memory:":
            path = Path(self.db_path)
            path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a transactional connection context that commits and closes cleanly."""
        if self._mem_conn is not None:
            with self._lock:
                try:
                    yield self._mem_conn
                    self._mem_conn.commit()
                except Exception:
                    self._mem_conn.rollback()
                    raise
        else:
            conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """Return a configured connection instance."""
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_schema(self) -> None:
        """Execute DDL to initialize all required relational tables and indexes."""
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)

    def close(self) -> None:
        """Close any persistent connections."""
        with self._lock:
            if self._mem_conn is not None:
                self._mem_conn.close()
                self._mem_conn = None

    def __del__(self) -> None:
        """Ensure connection is closed on garbage collection."""
        self.close()
