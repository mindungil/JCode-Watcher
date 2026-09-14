import os
import sys
from pathlib import Path

os.environ.setdefault("DB_URL", "sqlite://")
os.environ.setdefault("AUTO_CREATE_SCHEMA", "false")
os.environ.setdefault("COLLECTOR_TOKEN", "test-collector-token-at-least-32-characters")
os.environ.setdefault("QUERY_TOKEN", "test-query-token-at-least-32-characters")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
