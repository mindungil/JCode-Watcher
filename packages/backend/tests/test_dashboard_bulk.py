from datetime import datetime, timedelta, timezone
from uuid import uuid4

from crud.dashboard import get_dashboard_summaries
from models.buildLog import BuildLog
from models.runLog import RunLog
from models.snapshot import Snapshot
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

COMMON = dict(
    course_id=7,
    assignment_id=42,
    student_key="1",
    class_div="os-1",
    hw_name="assignment-42",
)


def test_dashboard_aggregates_all_students_in_database():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    now = datetime(2026, 8, 18, 10, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add_all(
            [
                BuildLog(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=now,
                    cwd="/",
                    binary_path="a",
                    cmdline="cc",
                    exit_code=1,
                    target_path="a",
                ),
                BuildLog(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=now + timedelta(minutes=1),
                    cwd="/",
                    binary_path="a",
                    cmdline="cc",
                    exit_code=0,
                    target_path="a",
                ),
                RunLog(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=now + timedelta(minutes=2),
                    cmdline="./a",
                    exit_code=0,
                    cwd="/",
                    target_path="a",
                    process_type="binary",
                ),
                Snapshot(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=now,
                    relative_path="main.c",
                    file_size=100,
                ),
                Snapshot(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=now + timedelta(minutes=1),
                    relative_path="main.c",
                    file_size=140,
                ),
            ]
        )
        session.commit()
        result = get_dashboard_summaries(session, "os-1", "assignment-42", [1, 2])

    assert result[1]["build_count"] == 2
    assert result[1]["build_fail_count"] == 1
    assert result[1]["run_count"] == 1
    assert result[1]["total_size_change"] == 140
    assert result[2]["build_count"] == 0


def test_dashboard_summary_excludes_activity_after_until():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    deadline = datetime(2026, 10, 2, 14, 59, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add_all(
            [
                Snapshot(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=deadline - timedelta(minutes=5),
                    relative_path="main.py",
                    file_size=100,
                ),
                RunLog(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=deadline - timedelta(minutes=1),
                    cmdline="python3 main.py",
                    exit_code=0,
                    cwd="/",
                    target_path="main.py",
                    process_type="python",
                ),
                # A student opening the closed assignment read-only after the deadline.
                RunLog(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=deadline + timedelta(days=12),
                    cmdline="python3 main.py",
                    exit_code=0,
                    cwd="/",
                    target_path="main.py",
                    process_type="python",
                ),
                BuildLog(
                    **COMMON,
                    event_id=uuid4(),
                    occurred_at=deadline + timedelta(days=12),
                    cwd="/",
                    binary_path="gcc",
                    cmdline="gcc main.c",
                    exit_code=1,
                    target_path="main.c",
                ),
            ]
        )
        session.commit()
        bounded = get_dashboard_summaries(
            session, "os-1", "assignment-42", [1], until=deadline
        )
        unbounded = get_dashboard_summaries(session, "os-1", "assignment-42", [1])

    assert bounded[1]["run_count"] == 1
    assert bounded[1]["build_count"] == 0
    assert bounded[1]["build_fail_count"] == 0
    assert bounded[1]["last_activity"].replace(tzinfo=timezone.utc) == deadline - timedelta(minutes=1)
    assert unbounded[1]["run_count"] == 2
    assert unbounded[1]["build_count"] == 1


def test_dashboard_summary_until_requires_time_zone():
    import pytest
    from pydantic import ValidationError
    from schemas.student import DashboardSummaryRequest

    request = DashboardSummaryRequest(student_ids=[1], until="2026-10-03T00:01:00+09:00")
    assert request.until.utcoffset().total_seconds() == 9 * 3600
    with pytest.raises(ValidationError):
        DashboardSummaryRequest(student_ids=[1], until="2026-10-03T00:01:00")
    assert DashboardSummaryRequest(student_ids=[1]).until is None
