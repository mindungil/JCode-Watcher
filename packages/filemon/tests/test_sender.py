from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from app.models.source_file_info import SourceFileInfo
from app.sender import SnapshotSender


@pytest.fixture
def event():
    return SourceFileInfo(
        class_div="os-1",
        hw_name="assignment-42",
        assignment_id=42,
        student_id="202012345",
        filename="src/main.c",
        target_file_path=Path("/watcher/codes/os-1-202012345/assignment-42/src/main.c"),
        timestamp="20260818_120000",
        event_id=UUID("00000000-0000-0000-0000-000000000042"),
        occurred_at=datetime(2026, 8, 18, 12, tzinfo=timezone.utc),
    )


def response_context(status=200, body="ok"):
    response = MagicMock(status=status)
    response.text = AsyncMock(return_value=body)
    post_context = MagicMock()
    post_context.__aenter__ = AsyncMock(return_value=response)
    post_context.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock()
    session.post.return_value = post_context
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)
    return session_context, session


@pytest.mark.asyncio
async def test_snapshot_uses_stable_event_contract(event):
    resolver = AsyncMock()
    resolver.resolve.return_value = 7
    sender = SnapshotSender(course_resolver=resolver)
    context, session = response_context()

    with patch("app.sender.aiohttp.ClientSession", return_value=context):
        assert await sender.register_snapshot(event, 128) is True

    url = session.post.call_args.args[0]
    payload = session.post.call_args.kwargs["json"]
    assert url.endswith("/api/v2/events/snapshot")
    assert payload == {
        "event_id": "00000000-0000-0000-0000-000000000042",
        "course_id": 7,
        "assignment_id": 42,
        "student_key": "202012345",
        "class_div": "os-1",
        "hw_name": "assignment-42",
        "relative_path": "src/main.c",
        "file_size": 128,
        "occurred_at": "2026-08-18T12:00:00+00:00",
    }


@pytest.mark.asyncio
async def test_snapshot_retry_keeps_event_id(event):
    resolver = AsyncMock()
    resolver.resolve.return_value = 7
    sender = SnapshotSender(course_resolver=resolver)
    first_context, first_session = response_context(status=503)
    second_context, second_session = response_context(status=200)

    with patch(
        "app.sender.aiohttp.ClientSession", side_effect=[first_context, second_context]
    ):
        assert await sender.register_snapshot(event, 128) is False
        assert await sender.register_snapshot(event, 128) is True

    first = first_session.post.call_args.kwargs["json"]["event_id"]
    second = second_session.post.call_args.kwargs["json"]["event_id"]
    assert first == second


@pytest.mark.asyncio
async def test_snapshot_fails_when_course_cannot_be_resolved(event):
    resolver = AsyncMock()
    resolver.resolve.side_effect = ValueError("course metadata missing")
    sender = SnapshotSender(course_resolver=resolver)
    assert await sender.register_snapshot(event, 128) is False
