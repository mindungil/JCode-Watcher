from crud.dashboard import get_dashboard_summaries_by_assignment
from db.connection import get_session
from fastapi import APIRouter, Depends, Query
from models.buildLog import BuildLog
from models.runLog import RunLog
from models.snapshot import Snapshot
from schemas.v2 import (
    DashboardV2Request,
    DashboardV2Response,
    DashboardV2Student,
    EventPage,
    EventPageItem,
    SnapshotPage,
    SnapshotPageItem,
)
from sqlmodel import Session, select

router = APIRouter(prefix="/api/v2", tags=["V2 queries"])


@router.post(
    "/assignments/{assignment_id}/dashboard", response_model=DashboardV2Response
)
def dashboard(
    assignment_id: int, request: DashboardV2Request, db: Session = Depends(get_session)
):
    rows = get_dashboard_summaries_by_assignment(
        db, assignment_id, request.student_keys
    )
    return DashboardV2Response(
        students=[
            DashboardV2Student(**rows[key])
            for key in dict.fromkeys(request.student_keys)
        ]
    )


def _event_page(
    db: Session,
    model,
    assignment_id: int,
    student_key: str,
    limit: int,
    cursor: int | None,
):
    statement = select(model).where(
        model.assignment_id == assignment_id, model.student_key == student_key
    )
    if cursor is not None:
        statement = statement.where(model.id < cursor)
    rows = db.exec(statement.order_by(model.id.desc()).limit(limit + 1)).all()
    page = rows[:limit]
    return EventPage(
        items=[EventPageItem.model_validate(row, from_attributes=True) for row in page],
        next_cursor=page[-1].id if len(rows) > limit and page else None,
    )


@router.get(
    "/assignments/{assignment_id}/students/{student_key}/snapshots",
    response_model=SnapshotPage,
)
def snapshots(
    assignment_id: int,
    student_key: str,
    limit: int = Query(default=200, ge=1, le=1000),
    cursor: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_session),
):
    statement = select(Snapshot).where(
        Snapshot.assignment_id == assignment_id, Snapshot.student_key == student_key
    )
    if cursor is not None:
        statement = statement.where(Snapshot.id < cursor)
    rows = db.exec(statement.order_by(Snapshot.id.desc()).limit(limit + 1)).all()
    page = rows[:limit]
    return SnapshotPage(
        items=[
            SnapshotPageItem.model_validate(row, from_attributes=True) for row in page
        ],
        next_cursor=page[-1].id if len(rows) > limit and page else None,
    )


@router.get(
    "/assignments/{assignment_id}/students/{student_key}/build",
    response_model=EventPage,
)
def build_events(
    assignment_id: int,
    student_key: str,
    limit: int = Query(default=200, ge=1, le=1000),
    cursor: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_session),
):
    return _event_page(db, BuildLog, assignment_id, student_key, limit, cursor)


@router.get(
    "/assignments/{assignment_id}/students/{student_key}/run", response_model=EventPage
)
def run_events(
    assignment_id: int,
    student_key: str,
    limit: int = Query(default=200, ge=1, le=1000),
    cursor: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_session),
):
    return _event_page(db, RunLog, assignment_id, student_key, limit, cursor)
