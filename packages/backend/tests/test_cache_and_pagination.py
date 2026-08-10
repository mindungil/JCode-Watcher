from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from crud.student import get_build_log
from models.buildLog import BuildLog
from models.runLog import RunLog
from models.snapshot import Snapshot
from utils.cache import BoundedTTLCache, cache, invalidate_log_cache, log_cache_key


def test_cache_is_bounded_and_prefix_invalidation_is_targeted():
    bounded = BoundedTTLCache(max_entries=2)
    bounded.set("a", 1)
    bounded.set("b", 2)
    bounded.set("c", 3)

    assert bounded.get("a") is None
    assert len(bounded) == 2

    key = log_cache_key("build", "os-1", "hw1", 1, None, None, 100, None)
    cache.set(key, ["stale"])
    invalidate_log_cache("build", "os-1", "hw1", 1)
    assert cache.get(key) is None


def test_build_log_query_is_bounded_and_cursor_is_stable():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    now = datetime.now()
    with Session(engine) as session:
        for idx in range(5):
            session.add(
                BuildLog(
                    class_div="os-1",
                    hw_name="hw1",
                    student_id=1,
                    cwd="/workspace",
                    binary_path="a.out",
                    cmdline="gcc main.c",
                    exit_code=0,
                    target_path="main.c",
                    timestamp=now + timedelta(seconds=idx),
                )
            )
        session.commit()

        first = get_build_log(session, "os-1", "hw1", 1, limit=2)
        assert len(first) == 3
        assert [row.id for row in first[:2]] == [5, 4]

        second = get_build_log(session, "os-1", "hw1", 1, limit=2, cursor=first[1].id)
        assert [row.id for row in second[:2]] == [3, 2]


def test_composite_indexes_are_declared_for_all_event_tables():
    index_names = {
        index.name
        for model in (Snapshot, BuildLog, RunLog)
        for index in model.__table__.indexes
    }
    assert {
        "ix_snapshot_lookup",
        "ix_snapshot_file_lookup",
        "ix_build_log_lookup",
        "ix_build_log_cursor",
        "ix_run_log_lookup",
        "ix_run_log_cursor",
    } <= index_names
