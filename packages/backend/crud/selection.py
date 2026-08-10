from typing import List
from sqlmodel import Session, select
from models.snapshot import Snapshot

def get_student_hw_files(db: Session, class_div: str, student_id: int, hw_name: str) -> List[str]:
    statement = (
        select(Snapshot.filename).distinct()
        .where(Snapshot.class_div == class_div)
        .where(Snapshot.student_id == student_id)
        .where(Snapshot.hw_name == hw_name)
        .order_by(Snapshot.filename)
        .limit(1000)
    )
    return db.exec(statement).all()

def get_student_hw_timestamps(db: Session, class_div: str, student_id: int, hw_name: str, filename: str) -> List[str]:
    statement = (
        select(Snapshot.timestamp)
        .where(Snapshot.class_div == class_div)
        .where(Snapshot.student_id == student_id)
        .where(Snapshot.hw_name == hw_name)
        .where(Snapshot.filename == filename)
    )
    
    results = db.exec(statement.order_by(Snapshot.timestamp.desc()).limit(1000)).all()
    return results
