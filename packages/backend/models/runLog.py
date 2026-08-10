from sqlmodel import Field, SQLModel
from sqlalchemy import Index
from typing import Optional
from datetime import datetime

class RunLog(SQLModel, table=True):
    __table_args__ = (
        Index("ix_run_log_lookup", "class_div", "hw_name", "student_id", "timestamp", "id"),
        Index("ix_run_log_cursor", "class_div", "hw_name", "student_id", "id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    class_div: str
    hw_name: str
    student_id: int
    cmdline: str
    exit_code: int
    cwd: str
    target_path: str
    process_type: str
    timestamp: datetime
