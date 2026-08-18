#!/usr/bin/env python3
import argparse
from pathlib import Path

import yaml


def documents(path: Path) -> list[dict]:
    return [
        item for item in yaml.safe_load_all(path.read_text(encoding="utf-8")) if item
    ]


def find(items: list[dict], kind: str, name: str) -> dict:
    return next(
        item
        for item in items
        if item["kind"] == kind and item["metadata"]["name"] == name
    )


def env(container: dict) -> dict[str, dict]:
    return {item["name"]: item for item in container.get("env", [])}


def validate_release(path: Path, environment: str) -> None:
    items = documents(path)
    namespace = "dev" if environment == "dev" else "watcher"
    backend = find(items, "Deployment", "watcher-backend")["spec"]["template"]["spec"]
    backend_deployment = find(items, "Deployment", "watcher-backend")
    assert backend_deployment["spec"]["replicas"] == (
        1 if environment == "dev" else 2
    )
    backend_container = backend["containers"][0]
    db = env(backend_container)["DB_URL"]["valueFrom"]["secretKeyRef"]
    assert db == {"name": "watcher-postgres-app", "key": "uri"}
    assert backend_container["readinessProbe"]["httpGet"]["path"] == "/ready"
    assert backend_container["livenessProbe"]["httpGet"]["path"] == "/health"
    assert all(
        mount.get("mountPath") != "/app/data"
        for mount in backend_container.get("volumeMounts", [])
    )

    binding_name = f"watcher-course-metadata-reader-{environment}"
    binding = find(items, "ClusterRoleBinding", binding_name)
    assert binding["subjects"] == [
        {
            "kind": "ServiceAccount",
            "name": "watcher-course-reader",
            "namespace": namespace,
        }
    ]
    for name in ("watcher-filemon", "watcher-procmon"):
        pod = find(items, "DaemonSet", name)["spec"]["template"]["spec"]
        assert pod["serviceAccountName"] == "watcher-course-reader"
        collector_env = env(pod["containers"][0])
        assert collector_env["JCODE_ENVIRONMENT"]["value"] == (
            "dev" if environment == "dev" else "prod"
        )
        assert collector_env["SPOOL_PATH"]["value"].endswith(
            "$(MY_NODE_NAME)-event-spool.db"
        )

    for item in items:
        pod_spec = item.get("spec", {}).get("template", {}).get("spec", {})
        for container in pod_spec.get("containers", []):
            assert not container.get("image", "").startswith("harbor.jbnu.ac.kr/")


def validate_migration(path: Path) -> None:
    job = find(documents(path), "Job", "watcher-backend-migration")["spec"]["template"][
        "spec"
    ]
    container = job["containers"][0]
    assert container["command"] == ["alembic", "-c", "alembic.ini", "upgrade", "head"]
    assert env(container)["DB_URL"]["valueFrom"]["secretKeyRef"] == {
        "name": "watcher-postgres-app",
        "key": "uri",
    }
    assert not container.get("volumeMounts")
    assert not job.get("volumes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("environment", choices=("dev", "production"))
    parser.add_argument("release", type=Path)
    parser.add_argument("migration", type=Path)
    args = parser.parse_args()
    validate_release(args.release, args.environment)
    validate_migration(args.migration)


if __name__ == "__main__":
    main()
