
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
load_dotenv(BASE_DIR / ".env")

def _resolve_dir(env_key: str, default_rel: str) -> Path:
    val = os.getenv(env_key, default_rel)
    p = Path(val)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p.resolve()

RUNS_DIR = _resolve_dir("RUNS_DIR", "runs")
LOCUSTFILES_DIR = _resolve_dir("LOCUSTFILES_DIR", "locustfiles")
LOCUSTFILES_SUBDIR = os.getenv("LOCUSTFILES_SUBDIR", "libs").strip()

# Create directories if they don't exist
RUNS_DIR.mkdir(parents=True, exist_ok=True)
LOCUSTFILES_DIR.mkdir(parents=True, exist_ok=True)

def parse_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
