from dataclasses import dataclass
from typing import Optional


@dataclass
class StudentInfo:
    """학생 정보"""

    student_id: str
    class_div: str  # 예: "os-1"
    assignment_id: Optional[int] = None

    def __post_init__(self):
        if not self.student_id or not self.class_div:
            raise ValueError("student_id와 class_div는 필수입니다")
        if self.assignment_id is not None and self.assignment_id <= 0:
            raise ValueError("과제 ID는 양수여야 합니다")
