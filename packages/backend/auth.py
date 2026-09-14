import secrets

from fastapi import Header, HTTPException

from schemas.config import settings


def require_collector_token(
    x_watcher_collector_token: str | None = Header(default=None),
) -> None:
    if (
        x_watcher_collector_token is None
        or not secrets.compare_digest(x_watcher_collector_token, settings.COLLECTOR_TOKEN)
    ):
        raise HTTPException(status_code=401, detail="Invalid collector credentials")


def require_query_token(
    x_watcher_query_token: str | None = Header(default=None),
) -> None:
    if (
        x_watcher_query_token is None
        or not secrets.compare_digest(x_watcher_query_token, settings.QUERY_TOKEN)
    ):
        raise HTTPException(status_code=401, detail="Invalid query credentials")
