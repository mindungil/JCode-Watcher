from datetime import datetime

from sqlalchemy import case, func
from sqlmodel import Session, select

from models.buildLog import BuildLog
from models.runLog import RunLog
from models.snapshot import Snapshot


def _parse_snapshot_time(value: str | None) -> datetime | None:
    return datetime.strptime(value, "%Y%m%d_%H%M%S") if value else None


def get_dashboard_summaries(
    db: Session,
    class_div: str,
    hw_name: str,
    student_ids: list[int],
) -> dict[int, dict]:
    unique_ids = list(dict.fromkeys(student_ids))
    summaries = {
        student_id: {
            "student_id": student_id,
            "build_count": 0,
            "build_fail_count": 0,
            "run_count": 0,
            "total_size_change": 0,
            "max_single_change": 0,
            "first_activity": None,
            "last_activity": None,
        }
        for student_id in unique_ids
    }

    build_rows = db.exec(
        select(
            BuildLog.student_id,
            func.count(BuildLog.id),
            func.sum(case((BuildLog.exit_code != 0, 1), else_=0)),
            func.min(BuildLog.timestamp),
            func.max(BuildLog.timestamp),
        )
        .where(
            BuildLog.class_div == class_div,
            BuildLog.hw_name == hw_name,
            BuildLog.student_id.in_(unique_ids),
        )
        .group_by(BuildLog.student_id)
    ).all()
    for student_id, count, failed, first, last in build_rows:
        row = summaries[student_id]
        row["build_count"] = count or 0
        row["build_fail_count"] = failed or 0
        row["first_activity"] = first
        row["last_activity"] = last

    run_rows = db.exec(
        select(
            RunLog.student_id,
            func.count(RunLog.id),
            func.min(RunLog.timestamp),
            func.max(RunLog.timestamp),
        )
        .where(
            RunLog.class_div == class_div,
            RunLog.hw_name == hw_name,
            RunLog.student_id.in_(unique_ids),
        )
        .group_by(RunLog.student_id)
    ).all()
    for student_id, count, first, last in run_rows:
        row = summaries[student_id]
        row["run_count"] = count or 0
        activity = [value for value in (row["first_activity"], first) if value is not None]
        row["first_activity"] = min(activity) if activity else None
        activity = [value for value in (row["last_activity"], last) if value is not None]
        row["last_activity"] = max(activity) if activity else None

    previous_size = func.lag(Snapshot.file_size, 1, 0).over(
        partition_by=(Snapshot.student_id, Snapshot.filename),
        order_by=Snapshot.timestamp,
    )
    deltas = (
        select(
            Snapshot.student_id.label("student_id"),
            Snapshot.timestamp.label("timestamp"),
            func.abs(Snapshot.file_size - previous_size).label("size_change"),
        )
        .where(
            Snapshot.class_div == class_div,
            Snapshot.hw_name == hw_name,
            Snapshot.student_id.in_(unique_ids),
        )
        .subquery()
    )
    snapshot_rows = db.exec(
        select(
            deltas.c.student_id,
            func.sum(deltas.c.size_change),
            func.max(deltas.c.size_change),
            func.min(deltas.c.timestamp),
            func.max(deltas.c.timestamp),
        ).group_by(deltas.c.student_id)
    ).all()
    for student_id, total_change, max_change, first, last in snapshot_rows:
        row = summaries[student_id]
        row["total_size_change"] = total_change or 0
        row["max_single_change"] = max_change or 0
        first_snapshot = _parse_snapshot_time(first)
        last_snapshot = _parse_snapshot_time(last)
        activity = [value for value in (row["first_activity"], first_snapshot) if value is not None]
        row["first_activity"] = min(activity) if activity else None
        activity = [value for value in (row["last_activity"], last_snapshot) if value is not None]
        row["last_activity"] = max(activity) if activity else None

    return summaries
