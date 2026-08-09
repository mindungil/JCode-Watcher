from sqlmodel import Field, SQLModel
from sqlalchemy import Index
from typing import Optional
from datetime import datetime

class BuildLog(SQLModel, table=True):
    __table_args__ = (
        Index("ix_build_log_lookup", "class_div", "hw_name", "student_id", "timestamp", "id"),
        Index("ix_build_log_cursor", "class_div", "hw_name", "student_id", "id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    class_div: str
    hw_name: str
    student_id: int
    cwd: str
    binary_path: str
    cmdline: str
    exit_code: int
    target_path: str
    timestamp: datetime
