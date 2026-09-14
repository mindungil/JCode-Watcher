"""공통 정규표현식 패턴 정의"""
import re

# 기본 구성 요소 패턴
SUBJECT_CODE_PATTERN = r"[a-zA-Z0-9]+"  # 과목코드: 영숫자
CLASS_NUM_PATTERN = r"\d+"              # 분반: 숫자
STUDENT_ID_PATTERN = r"\d+"             # 학번: 숫자

# Watcher 저장 키는 표시 이름이 아니라 불변 assignment ID를 사용한다.
ASSIGNMENT_DIR_PATTERN = r"assignment-[1-9][0-9]*"

# 조합된 패턴들
CLASS_DIV_PATTERN = f"({SUBJECT_CODE_PATTERN})-({CLASS_NUM_PATTERN})"  # 과목-분반

# 컴파일된 정규표현식 객체들
HOSTNAME_REGEX = re.compile(
    f"^jcode-{CLASS_DIV_PATTERN}-({STUDENT_ID_PATTERN})(?:-([a-z0-9-]+))?$"
)

WORKSPACE_PATH_REGEX = re.compile(
    f"^(?:/workspace/{CLASS_DIV_PATTERN}-{STUDENT_ID_PATTERN}/({ASSIGNMENT_DIR_PATTERN})|"
    f"/home/coder/project/(?:assignments/)?({ASSIGNMENT_DIR_PATTERN}))(?:/|$)"
)
