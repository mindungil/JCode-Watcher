from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from app.models.event import Event
from app.models.process_type import ProcessType
from app.sender import EventSender


def make_event(process_type=ProcessType.GCC):
    return Event(
        process_type=process_type,
        homework_dir="assignment-42",
        assignment_id=42,
        student_id="202012345",
        class_div="os-1",
        timestamp=datetime(2026, 8, 18, 12, tzinfo=timezone.utc),
        event_id=UUID("00000000-0000-0000-0000-000000000042"),
        source_file="/workspace/os-1-202012345/assignment-42/main.c",
        exit_code=0,
        args=["gcc", "main.c"],
        cwd="/workspace/os-1-202012345/assignment-42",
        binary_path="/usr/bin/gcc",
    )


@pytest.fixture
def sender():
    resolver = AsyncMock()
    resolver.resolve.return_value = 7
    return EventSender("http://watcher", course_resolver=resolver)


@pytest.mark.asyncio
async def test_build_event_uses_stable_contract(sender):
    event = make_event()
    with patch.object(
        sender, "_send_request", new=AsyncMock(return_value=True)
    ) as request:
        assert await sender.send_event(event) is True

    endpoint, payload = request.call_args.args
    assert endpoint == "/api/v2/events/build"
    assert payload["event_id"] == str(event.event_id)
    assert payload["course_id"] == 7
    assert payload["assignment_id"] == 42
    assert payload["student_key"] == "202012345"
    assert payload["occurred_at"] == "2026-08-18T12:00:00+00:00"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("process_type", "expected"),
    [(ProcessType.USER_BINARY, "binary"), (ProcessType.PYTHON, "python")],
)
async def test_run_event_uses_stable_contract(sender, process_type, expected):
    event = make_event(process_type)
    with patch.object(
        sender, "_send_request", new=AsyncMock(return_value=True)
    ) as request:
        assert await sender.send_event(event) is True

    endpoint, payload = request.call_args.args
    assert endpoint == "/api/v2/events/run"
    assert payload["process_type"] == expected


@pytest.mark.asyncio
async def test_retry_reuses_collector_event_id(sender):
    event = make_event()
    with patch.object(
        sender, "_send_request", new=AsyncMock(side_effect=[False, True])
    ) as request:
        assert await sender.send_event(event) is False
        assert await sender.send_event(event) is True

    assert (
        request.call_args_list[0].args[1]["event_id"]
        == request.call_args_list[1].args[1]["event_id"]
    )


@pytest.mark.asyncio
async def test_unknown_event_is_not_sent(sender):
    assert await sender.send_event(make_event(ProcessType.UNKNOWN)) is False
