import os
import json
import re
import time
from pathlib import Path
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PathFilter:
    """
    파일 경로가 처리 대상인지 판단하는 클래스.
    정규식 대신 Python 코드를 사용하여 가독성과 유지보수성을 높임.
    """
    
    # 무시할 경로에 대한 정규식 패턴 (미리 컴파일하여 성능 향상)
    IGNORE_PATTERNS = [
        re.compile(r"/.*/(?:\.?env|ENV)/.+"),
        re.compile(r"/.*/(?:site|dist)-packages/.+"),
        re.compile(r"/.*/node_modules/.+"),
        re.compile(r"/.*/lib(?:64|s)?/.+"),
        re.compile(r"/.*/\..+"),  # 숨김 파일/디렉토리
    ]
    
    # 허용할 파일 확장자
    ALLOWED_EXTENSIONS = {".c", ".h", ".py", ".cpp", ".hpp", ".ipynb"}

    def __init__(self):
        self.watch_root = settings.WATCH_ROOT
        logger.info("PathFilter 초기화 완료", watch_root=str(self.watch_root))

    def is_directory(self, file_path: str) -> bool:
        """디렉토리인지 확인"""
        return os.path.isdir(file_path)
    
    def should_process(self, file_path: str) -> bool:
        """파일/경로가 처리 대상인지 확인"""
        # 1. 무시 패턴에 해당하는지 먼저 확인
        if self._is_ignored(file_path):
            return False
        
        # 2. 경로 구조가 유효한지 확인
        return self._is_valid_source_path(file_path)

    def is_system_mutation_event(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            relative = path.relative_to(self.watch_root)
            if len(relative.parts) < 2:
                return False
            workspace_key = relative.parts[1]
            marker = (
                self.watch_root
                / ".jcode-system-mutations"
                / relative.parts[0]
                / f"{workspace_key}.json"
            )
            if not marker.is_file():
                return False
            payload = json.loads(marker.read_text(encoding="utf-8"))
            if payload.get("state") == "in_progress":
                return True
            if not path.exists():
                updated_at_ns = int(payload.get("updatedAtNs") or marker.stat().st_mtime_ns)
                return time.time_ns() - updated_at_ns <= int(
                    settings.SYSTEM_MUTATION_GRACE_SECONDS * 1_000_000_000
                )
            return path.stat().st_mtime_ns <= marker.stat().st_mtime_ns
        except (OSError, ValueError, json.JSONDecodeError):
            return False

    def _is_ignored(self, path_str: str) -> bool:
        """무시 패턴에 해당하는지 확인"""
        for pattern in self.IGNORE_PATTERNS:
            if pattern.search(path_str):
                return True
        return False

    def _is_valid_source_path(self, path_str: str) -> bool:
        """소스 코드 경로 구조의 유효성을 검사"""
        try:
            path = Path(path_str)
            relative_path = path.relative_to(self.watch_root)
            
            parts = relative_path.parts
            
            # workspace/assignment 아래의 소스 트리는 의존성 디렉토리를 제외하되,
            # 일반적인 다중 모듈 프로젝트를 수용할 수 있는 깊이까지 추적한다.
            if not (3 <= len(parts) <= 3 + settings.SOURCE_MAX_NESTING):
                return False

            # 1. 과목-분반-학번 폴더 검사 (예: os-1-202012345)
            class_student_parts = parts[0].split('-')
            if len(class_student_parts) != 3:
                return False

            # 2. V2의 불변 과제 경로 검사
            hw_part = parts[1]
            if not re.fullmatch(r"assignment-[1-9][0-9]*", hw_part):
                return False

            # 3. 파일 확장자 검사
            if path.suffix not in self.ALLOWED_EXTENSIONS:
                return False
                
            return True
            
        except (ValueError, IndexError):
            # relative_to 실패, split 실패, 인덱스 접근 실패 등 모든 예외는 유효하지 않은 경로로 간주
            return False
