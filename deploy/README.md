# Watcher PostgreSQL 배포

Watcher의 신규 이벤트는 빈 PostgreSQL 데이터베이스에 저장합니다. 기존 SQLite는 과거 기록 보관본이며 새 API에 연결하거나 PostgreSQL로 복사하지 않습니다.

## 배포 순서

1. `watcher-postgres-app` Secret의 `uri`에 `postgresql+psycopg://` 연결 문자열을 설정합니다.
2. 확인된 commit 이미지 digest를 `deploy/set-image-digests.py`로 dev overlay에 기록합니다.
3. `deploy/deploy.sh dev`를 실행합니다. 이 스크립트는 Backend를 내리고 `alembic upgrade head` Job을 완료한 뒤 Backend와 수집기를 올립니다.
4. Snapshot, Build, Run 등록·조회와 `/ready`, Pod 재시작 후 데이터 유지를 확인합니다.
5. 같은 digest를 production overlay에 기록하고 `deploy/deploy.sh production`을 실행합니다.

Backend와 migration Job에는 SQLite PVC를 마운트하지 않습니다. PostgreSQL 연결 실패 시 `/ready`만 실패하며 `/health`는 프로세스 상태를 계속 반환합니다.

최초 production 전환에서는 기존 수집기를 먼저 중단하고 SQLite 백업을 완료한 뒤 배포합니다. 새 Backend가 준비되기 전에 구형 수집기를 다시 시작하지 않습니다.

Filemon과 Procmon은 강의 Namespace의 `jcode.io/course-id` annotation을 읽어 `course_id`를 결정합니다. 이 권한은 `watcher-course-metadata-reader` ClusterRole의 Namespace `get`으로 제한됩니다.

## SQLite 보관 경계

- 기존 PVC와 PV는 삭제하지 않습니다.
- SQLite를 신규 Watcher의 읽기 또는 쓰기 대상으로 설정하지 않습니다.
- 과거 기록이 필요할 때만 관리자용 일회성 조회 Pod로 보관본을 엽니다.
- PostgreSQL 전환 이후 신규 기록의 유일한 원본은 PostgreSQL입니다.
