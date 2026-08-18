import main
import pytest
from db.connection import build_engine
from fastapi.testclient import TestClient


def test_liveness_does_not_depend_on_database(monkeypatch):
    monkeypatch.setattr(
        main, "check_database", lambda: (_ for _ in ()).throw(RuntimeError("down"))
    )
    client = TestClient(main.app)
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 503


def test_database_driver_is_restricted_to_psycopg_or_test_sqlite():
    sqlite_engine = build_engine("sqlite://")
    assert sqlite_engine.dialect.name == "sqlite"
    sqlite_engine.dispose()
    with pytest.raises(RuntimeError, match=r"postgresql\+psycopg"):
        build_engine("mysql+pymysql://watcher:watcher@localhost/watcher")
