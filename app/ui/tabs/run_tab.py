import os
import time
import json
from datetime import datetime
import streamlit as st
from app.core.config import RUNS_DIR
from app.core.runner import (
    which_locust,
    list_locustfiles,
    display_path,
    locustfile_declares_host,
    extract_locustfile_host,
    run_locust
)

def render_run_tab(base_dir):
    st.subheader("Run Locust Test")

    if which_locust() is None:
        st.error(
            "'locust' command not found. Please install dependencies with 'pip install -r requirements.txt'."
        )

    locustfiles = list_locustfiles()
    choices = [display_path(p, base_dir) for p in locustfiles]
    selected_file = st.selectbox(
        "Locust file", options=choices, index=0 if choices else None
    )

    # Defaults from settings
    from app.core.settings import settings
    
    default_host = settings.locust_host or "http://localhost:8000" # Locust host might not be in settings, let's check settings definition
    # Wait, settings definition has locust_target_host.
    default_host = settings.locust_target_host or "http://localhost:8000"
    
    
    default_users = settings.locust_users
    default_spawn = settings.locust_spawn_rate
    default_run_time = settings.locust_run_time
    default_csv_prefix = settings.locust_csv_prefix
    
    default_html_report = settings.locust_html_report
    default_csv_full_history = settings.locust_csv_full_history


    selected_path = base_dir / selected_file if selected_file else None
    has_file_host = bool(selected_path and locustfile_declares_host(selected_path))
    use_file_host = st.checkbox(
        "Use host from locustfile", value=has_file_host
    )

    file_host_val = (
        extract_locustfile_host(selected_path) if selected_path else None
    )

    host = st.text_input(
        "Host (e.g: https://example.com)",
        value=default_host,
        disabled=use_file_host,
        help="If left empty and above option is enabled, host from locustfile will be used.",
    )

    effective_host = (file_host_val if use_file_host else host) or ""
    st.caption(
        f"Etkin host: {effective_host if effective_host else '—'}"
        + (" (from file)" if use_file_host and file_host_val else "")
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        users = st.number_input(
            "User count (-u)", min_value=1, value=default_users
        )
    with col2:
        spawn = st.number_input(
            "Spawn rate/s (-r)", min_value=1, value=int(default_spawn)
        )
    with col3:
        run_time = st.text_input(
            "Run time (--run-time)", value=default_run_time
        )

    adv = st.expander("Advanced Settings", expanded=False)
    with adv:
        html_report = st.checkbox("Generate HTML report", value=default_html_report)
        csv_full_history = st.checkbox(
            "CSV full history", value=default_csv_full_history
        )
        csv_prefix = st.text_input("CSV prefix", value=default_csv_prefix)
        loglevel = st.selectbox(
            "Log level",
            options=["ERROR", "WARNING", "INFO", "DEBUG"],
            index=2,
            help="DEBUG level shows ReportPortal logs",
        )
        csv_flush_interval = st.number_input(
            "CSV flush interval (s)",
            min_value=0,
            value=0,
            help="0=Locust default. 5-10 seconds can be useful for large files.",
        )
        stream_logs = st.checkbox(
            "Live log streaming",
            value=False,
            help="Performance improves when disabled, logs can be viewed from file.",
        )

        st.divider()
        st.markdown("**🔗 ReportPortal Integration**")
        enable_rp = st.checkbox(
            "Send to ReportPortal",
            value=True,
            help="Sends test results to ReportPortal",
        )
        if enable_rp:
            rp_endpoint = st.text_input(
                "RP Endpoint",
                value=os.getenv(
                    "RP_ENDPOINT", ""
                ),
            )
            rp_project = st.text_input(
                "RP Project", value=os.getenv("RP_PROJECT", "locust")
            )
            rp_token = st.text_input(
                "RP Token",
                value=os.getenv(
                    "RP_TOKEN",
                    "",
                ),
                type="password",
            )
            rp_launch_name = st.text_input(
                "Launch Name", value=os.getenv("RP_LAUNCH_NAME", "Locust Load Test")
            )

    run_btn = st.button(
        "Start Test",
        type="primary",
        use_container_width=True,
        disabled=(
            which_locust() is None
            or not selected_file
            or (not use_file_host and not host and not file_host_val)
        ),
    )

    log_area = st.empty()
    status_area = st.empty()

    if run_btn:
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        st.session_state["current_run_dir"] = str(run_dir)
        st.session_state["running"] = True

        locustfile_path = base_dir / selected_file  # type: ignore

        # Set ReportPortal env vars if enabled
        if enable_rp:
            # Determine actual host that will be used (prioritize file host)
            actual_host = (
                file_host_val
                if (use_file_host and file_host_val)
                else (host or file_host_val or "Not specified")
            )

            os.environ["RP_ENDPOINT"] = rp_endpoint
            os.environ["RP_PROJECT"] = rp_project
            os.environ["RP_TOKEN"] = rp_token
            os.environ["RP_LAUNCH_NAME"] = rp_launch_name
            os.environ["RP_DESCRIPTION"] = (
                f"Locust test: {selected_file} | Users: {users} | Host: {actual_host}"
            )
            os.environ["RP_TEST_HOST"] = actual_host
            os.environ["RP_HOST_SOURCE"] = (
                "locustfile" if (use_file_host and file_host_val) else "UI"
            )
            os.environ["RP_LOCUSTFILE"] = selected_file

        proc, logfile, html_path, start, cmd = run_locust(
            locustfile=locustfile_path,
            host=file_host_val if use_file_host else host,
            users=int(users),
            spawn_rate=float(spawn),
            run_time=run_time,
            run_dir=run_dir,
            csv_prefix=csv_prefix,
            html_report=html_report,
            csv_full_history=csv_full_history,
            loglevel=loglevel,
            csv_flush_interval=(
                int(csv_flush_interval) if int(csv_flush_interval) > 0 else None
            ),
            stream_logs=stream_logs,
            enable_rp=enable_rp,
        )

        log_lines = []
        with st.spinner("Locust is running... Please wait"):
            if stream_logs and proc.stdout is not None:
                last_update = 0.0
                for line in proc.stdout:
                    log_lines.append(line.rstrip())
                    now = time.time()
                    if now - last_update > 0.25:
                        last_update = now
                        to_show = "\n".join(log_lines[-200:])
                        log_area.code(to_show)
            rc = proc.wait()
            if not stream_logs:
                try:
                    tail = (
                        logfile.read_text(
                            encoding="utf-8", errors="ignore"
                        ).splitlines()
                    )[-200:]
                    log_area.code("\n".join(tail))
                except Exception:
                    pass

        st.session_state["running"] = False
        ended = datetime.utcnow().isoformat()

        # Save run metadata
        meta = {
            "locustfile": display_path(locustfile_path, base_dir),
            "use_file_host": bool(use_file_host),
            "file_host": file_host_val,
            "typed_host": host if not use_file_host else None,
            "effective_host": effective_host,
            "users": int(users),
            "spawn_rate": float(spawn),
            "run_time": run_time,
            "csv_prefix": csv_prefix,
            "html_report": bool(html_report),
            "csv_full_history": bool(csv_full_history),
            "started_at": start,
            "ended_at": ended,
            "command": " ".join(cmd),
        }
        try:
            (run_dir / "metadata.json").write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

        if rc != 0:
            # try to show the last lines to aid debugging
            try:
                shown = "\n".join(log_lines[-50:]) if log_lines else ""
            except Exception:
                shown = ""
            status_area.error(
                f"Failed with errors (exit={rc}). Run directory: {run_dir}\n{shown}"
            )
        else:
            status_area.success(f"Completed. Run directory: {run_dir}")
