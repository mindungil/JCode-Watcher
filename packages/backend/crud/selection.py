from typing import List

from models.snapshot import Snapshot
from sqlmodel import Session, select


def get_student_hw_files(
    db: Session, class_div: str, student_id: int, hw_name: str
) -> List[str]:
    statement = (
        select(Snapshot.relative_path)
        .distinct()
        .where(Snapshot.class_div == class_div)
        .where(Snapshot.student_key == str(student_id))
        .where(Snapshot.hw_name == hw_name)
        .order_by(Snapshot.relative_path)
        .limit(1000)
    )
    return db.exec(statement).all()


def get_student_hw_timestamps(
    db: Session, class_div: str, student_id: int, hw_name: str, filename: str
) -> List[str]:
    statement = (
        select(Snapshot.occurred_at)
        .where(Snapshot.class_div == class_div)
        .where(Snapshot.student_key == str(student_id))
        .where(Snapshot.hw_name == hw_name)
        .where(Snapshot.relative_path == filename)
    )

    results = db.exec(statement.order_by(Snapshot.occurred_at.desc()).limit(1000)).all()
    return [value.isoformat() for value in results]
