from datetime import datetime, timedelta

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from crud.dashboard import get_dashboard_summaries
from models.buildLog import BuildLog
from models.runLog import RunLog
from models.snapshot import Snapshot


def test_dashboard_aggregates_all_students_in_one_query_group():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    now = datetime(2026, 8, 9, 10, 0, 0)
    with Session(engine) as session:
        session.add_all(
            [
                BuildLog(class_div="os-1", hw_name="hw1", student_id=1, cwd="/", binary_path="a", cmdline="cc", exit_code=1, target_path="a", timestamp=now),
                BuildLog(class_div="os-1", hw_name="hw1", student_id=1, cwd="/", binary_path="a", cmdline="cc", exit_code=0, target_path="a", timestamp=now + timedelta(minutes=1)),
                RunLog(class_div="os-1", hw_name="hw1", student_id=1, cmdline="./a", exit_code=0, cwd="/", target_path="a", process_type="run", timestamp=now + timedelta(minutes=2)),
                Snapshot(class_div="os-1", hw_name="hw1", student_id=1, filename="main.c", timestamp="20260809_100000", file_size=100),
                Snapshot(class_div="os-1", hw_name="hw1", student_id=1, filename="main.c", timestamp="20260809_100100", file_size=140),
            ]
        )
        session.commit()

        result = get_dashboard_summaries(session, "os-1", "hw1", [1, 2])

    assert result[1]["build_count"] == 2
    assert result[1]["build_fail_count"] == 1
    assert result[1]["run_count"] == 1
    assert result[1]["total_size_change"] == 140
    assert result[1]["max_single_change"] == 100
    assert result[2]["build_count"] == 0
