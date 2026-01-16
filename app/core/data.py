
import io
import zipfile
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Tuple
from .config import RUNS_DIR

def load_stats(run_dir: Path, prefix: str = "stats") -> Dict[str, pd.DataFrame]:
    files = {
        "stats": run_dir / f"{prefix}_stats.csv",
        "history": run_dir / f"{prefix}_stats_history.csv",
        "failures": run_dir / f"{prefix}_failures.csv",
        "requests": run_dir / f"{prefix}_requests.csv",
        "exceptions": run_dir / f"{prefix}_exceptions.csv",
        "distribution": run_dir / f"{prefix}_distribution.csv",
    }
    data = {}
    for k, p in files.items():
        if p.exists():
            try:
                data[k] = pd.read_csv(p)
            except Exception:
                pass
    return data

@st.cache_data(show_spinner=False)
def load_stats_cached(run_dir_str: str, prefix: str, sig: Tuple) -> Dict[str, pd.DataFrame]:
    return load_stats(Path(run_dir_str), prefix)

def run_signature(run_dir: Path) -> Tuple:
    parts = []
    try:
        for p in sorted(run_dir.glob("*")):
            try:
                stt = p.stat()
                parts.append((p.name, stt.st_mtime_ns, stt.st_size))
            except Exception:
                continue
    except Exception:
        pass
    return tuple(parts)

def list_runs() -> list[Path]:
    return sorted([p for p in RUNS_DIR.iterdir() if p.is_dir()], reverse=True)

def create_run_zip(run_dir: Path) -> bytes:
    """Create a ZIP archive of all files in run directory."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in run_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(run_dir)
                zf.write(file_path, arcname)
    buffer.seek(0)
    return buffer.getvalue()
