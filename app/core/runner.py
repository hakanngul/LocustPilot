
import os
import shutil
import subprocess
import re
import ast
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from .config import BASE_DIR, LOCUSTFILES_DIR, LOCUSTFILES_SUBDIR

def which_locust() -> Optional[str]:
    return shutil.which("locust")

def display_path(path: Path, base: Path) -> str:
    """Return a display-friendly path string.
    If path is under base, return relative path.
    Otherwise, return the full path for readability.
    """
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)

def _has_locust_user_class(path: Path) -> bool:
    """Heuristic: returns True if file defines a Locust User class.
    Detects subclasses of HttpUser/FastHttpUser via AST; falls back to regex.
    """
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id in {
                        "HttpUser",
                        "FastHttpUser",
                    }:
                        return True
                    if isinstance(base, ast.Attribute) and base.attr in {
                        "HttpUser",
                        "FastHttpUser",
                    }:
                        return True
    except Exception:
        pass
    
    return (
        re.search(r"class\s+\w+\(.*?(HttpUser|FastHttpUser).*?\)", src) is not None
        or "@task" in src
    )

def list_locustfiles() -> List[Path]:
    """List runnable locustfiles under LOCUSTFILES_DIR."""
    base = LOCUSTFILES_DIR
    search_root = base / LOCUSTFILES_SUBDIR if LOCUSTFILES_SUBDIR else base
    if not search_root.exists():
        search_root = base

    candidates = search_root.rglob("*.py")
    selected: List[Path] = []
    for p in candidates:
        if p.name == "__init__.py":
            continue
        if "__pycache__" in p.parts:
            continue
        if any(part in {"utils", "helpers"} for part in p.parts):
            if not _has_locust_user_class(p):
                continue
        if _has_locust_user_class(p):
            selected.append(p)
    return sorted(selected)

def locustfile_declares_host(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return any(line.strip().startswith("host =") for line in text.splitlines())

def extract_locustfile_host(path: Path) -> Optional[str]:
    env_host = os.getenv("LOCUST_TARGET_HOST")
    if env_host:
        return env_host

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    m = re.search(r"^\s*host\s*=\s*['\"]([^'\"]+)['\"]", text, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()

    if re.search(r"^\s*host\s*=\s*TARGET_HOST", text, flags=re.MULTILINE):
        base_user_path = BASE_DIR / "locustfiles" / "utils" / "base_user.py"
        if base_user_path.exists():
            try:
                base_text = base_user_path.read_text(encoding="utf-8", errors="ignore")
                m_target = re.search(
                    r"^TARGET_HOST\s*=\s*(?:os\.getenv\(['\"]LOCUST_TARGET_HOST['\"]\s*,\s*)?['\"]([^'\"]+)['\"]",
                    base_text,
                    flags=re.MULTILINE,
                )
                if m_target:
                    return m_target.group(1).strip()
            except Exception:
                pass
    return None

def run_locust(
    locustfile: Path,
    host: Optional[str],
    users: int,
    spawn_rate: float,
    run_time: str,
    run_dir: Path,
    csv_prefix: str = "stats",
    html_report: bool = True,
    csv_full_history: bool = True,
    loglevel: str = "WARNING",
    csv_flush_interval: Optional[int] = None,
    stream_logs: bool = True,
    enable_rp: bool = False,
) -> Tuple[subprocess.Popen, Path, Path, str, List[str]]:
    
    run_dir.mkdir(parents=True, exist_ok=True)
    logfile = run_dir / "locust.log"
    html_path = run_dir / "report.html"
    csv_prefix_path = run_dir / csv_prefix

    cmd = [
        "locust",
        "-f", str(locustfile),
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "--run-time", str(run_time),
        "--csv", str(csv_prefix_path),
        "--logfile", str(logfile),
        "--only-summary",
    ]
    if host:
        cmd += ["--host", str(host)]
    if loglevel:
        cmd += ["--loglevel", loglevel]
    if html_report:
        cmd += ["--html", str(html_path)]
    if csv_full_history:
        cmd += ["--csv-full-history"]
    if csv_flush_interval:
        cmd += ["--csv-flush-interval", str(int(csv_flush_interval))]

    start = datetime.utcnow().isoformat()

    env = os.environ.copy()
    py_paths = [
        str(LOCUSTFILES_DIR),
        str(LOCUSTFILES_DIR / "libs"),
        str(BASE_DIR),
    ]
    existing = env.get("PYTHONPATH", "")
    for p in py_paths:
        if p and p not in existing.split(os.pathsep):
            existing = (existing + (os.pathsep if existing else "")) + p
    env["PYTHONPATH"] = existing

    # Set dynamic RP env vars if generic user flow
    # RP vars are set in app.py logic before calling this, but env is copied here.
    # The caller must have set os.environ before calling this if they want to pass vars, 
    # OR we rely on `env = os.environ.copy()` picking them up.

    proc = subprocess.Popen(
        cmd,
        stdout=(subprocess.PIPE if stream_logs else subprocess.DEVNULL),
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(BASE_DIR),
        env=env,
    )
    return proc, logfile, html_path, start, cmd
