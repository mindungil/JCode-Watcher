from datetime import datetime

from models.buildLog import BuildLog
from models.runLog import RunLog
from models.snapshot import Snapshot
from sqlalchemy import func
from sqlmodel import Session, select


def get_snapshot_stats(
    db: Session, class_div: str, hw_name: str, student_id: int, filename: str
):
    return db.exec(
        select(func.count(Snapshot.id), func.avg(Snapshot.file_size)).where(
            Snapshot.class_div == class_div,
            Snapshot.hw_name == hw_name,
            Snapshot.student_key == str(student_id),
            Snapshot.relative_path == filename,
        )
    ).one()


def get_assignment_snapshot_stats(
    db: Session, class_div: str, student_id: int, hw_name: str
):
    filters = (
        Snapshot.class_div == class_div,
        Snapshot.student_key == str(student_id),
        Snapshot.hw_name == hw_name,
    )
    count, average, first, last = db.exec(
        select(
            func.count(Snapshot.id),
            func.avg(Snapshot.file_size),
            func.min(Snapshot.occurred_at),
            func.max(Snapshot.occurred_at),
        ).where(*filters)
    ).one()
    latest = db.exec(
        select(Snapshot.occurred_at)
        .where(*filters)
        .order_by(Snapshot.occurred_at.desc(), Snapshot.id.desc())
        .limit(2)
    ).all()
    return count, average, first, last, latest


def get_student_trends(
    db: Session, class_div: str, student_id: int, hw_name: str, interval: int
):
    bucket_seconds = interval * 60
    bucket = func.to_timestamp(
        func.floor(func.extract("epoch", Snapshot.occurred_at) / bucket_seconds)
        * bucket_seconds
    )
    latest_per_file = (
        select(
            bucket.label("bucket"),
            Snapshot.relative_path.label("relative_path"),
            Snapshot.file_size.label("file_size"),
        )
        .distinct(bucket, Snapshot.relative_path)
        .where(
            Snapshot.class_div == class_div,
            Snapshot.student_key == str(student_id),
            Snapshot.hw_name == hw_name,
        )
        .order_by(
            bucket,
            Snapshot.relative_path,
            Snapshot.occurred_at.desc(),
            Snapshot.id.desc(),
        )
        .subquery()
    )
    totals = (
        select(
            latest_per_file.c.bucket,
            func.sum(latest_per_file.c.file_size).label("total_size"),
        )
        .group_by(latest_per_file.c.bucket)
        .subquery()
    )
    previous = func.lag(totals.c.total_size, 1, 0).over(order_by=totals.c.bucket)
    return db.exec(
        select(
            totals.c.bucket,
            totals.c.total_size,
            (totals.c.total_size - previous).label("size_change"),
        ).order_by(totals.c.bucket)
    ).all()


def get_build_log(
    db: Session,
    class_div: str,
    hw_name: str,
    student_id: int,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int = 200,
    cursor: int | None = None,
):
    statement = select(BuildLog).where(
        BuildLog.class_div == class_div,
        BuildLog.hw_name == hw_name,
        BuildLog.student_key == str(student_id),
    )
    if from_time is not None:
        statement = statement.where(BuildLog.occurred_at >= from_time)
    if to_time is not None:
        statement = statement.where(BuildLog.occurred_at <= to_time)
    if cursor is not None:
        statement = statement.where(BuildLog.id < cursor)
    return db.exec(statement.order_by(BuildLog.id.desc()).limit(limit + 1)).all()


def get_run_log(
    db: Session,
    class_div: str,
    hw_name: str,
    student_id: int,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int = 200,
    cursor: int | None = None,
):
    statement = select(RunLog).where(
        RunLog.class_div == class_div,
        RunLog.hw_name == hw_name,
        RunLog.student_key == str(student_id),
    )
    if from_time is not None:
        statement = statement.where(RunLog.occurred_at >= from_time)
    if to_time is not None:
        statement = statement.where(RunLog.occurred_at <= to_time)
    if cursor is not None:
        statement = statement.where(RunLog.id < cursor)
    return db.exec(statement.order_by(RunLog.id.desc()).limit(limit + 1)).all()
