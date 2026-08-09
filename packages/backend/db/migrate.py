import fcntl
from pathlib import Path

from sqlalchemy import text
from sqlmodel import SQLModel

from db.connection import engine
from models.buildLog import BuildLog  # noqa: F401
from models.runLog import RunLog  # noqa: F401
from models.snapshot import Snapshot  # noqa: F401


MIGRATIONS = (
    "CREATE INDEX IF NOT EXISTS ix_snapshot_lookup ON snapshot (class_div, hw_name, student_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS ix_snapshot_file_lookup ON snapshot (class_div, hw_name, student_id, filename, timestamp)",
    "CREATE INDEX IF NOT EXISTS ix_build_log_lookup ON buildlog (class_div, hw_name, student_id, timestamp, id)",
    "CREATE INDEX IF NOT EXISTS ix_build_log_cursor ON buildlog (class_div, hw_name, student_id, id)",
    "CREATE INDEX IF NOT EXISTS ix_run_log_lookup ON runlog (class_div, hw_name, student_id, timestamp, id)",
    "CREATE INDEX IF NOT EXISTS ix_run_log_cursor ON runlog (class_div, hw_name, student_id, id)",
)


def migrate() -> None:
    database_path = engine.url.database
    if not database_path:
        raise RuntimeError("DB_URL must point to a persistent SQLite database")
    lock_path = Path(database_path).with_suffix(".migration.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        SQLModel.metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(text("PRAGMA busy_timeout=60000"))
            for statement in MIGRATIONS:
                connection.execute(text(statement))
        lock_path.with_name(".watcher-schema-v1").write_text("ready\n", encoding="utf-8")


if __name__ == "__main__":
    migrate()
