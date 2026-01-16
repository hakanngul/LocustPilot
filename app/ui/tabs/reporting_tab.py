
import shutil
import json
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from app.core.config import RUNS_DIR
from app.core.runner import display_path
from app.core.data import list_runs, load_stats_cached, run_signature, create_run_zip
from app.ui.charts import render_summary_from_stats, render_time_series

def render_reporting_tab(base_dir):
    st.subheader("View Reports")
    runs = list_runs()
    if not runs:
        st.info("No runs yet. Start a test from 'Run Test' tab.")
    else:
        run_opts = [display_path(p, RUNS_DIR) for p in runs]
        sel = st.selectbox("Select a run", run_opts)
        selected_run = RUNS_DIR / sel
        data = load_stats_cached(
            str(selected_run), "stats", run_signature(selected_run)
        )

        # Üst bilgi (metadata)
        meta_path = selected_run / "metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                cols = st.columns(4)
                cols[0].metric("Active Host", meta.get("effective_host", "-"))
                cols[1].metric("Users", str(meta.get("users", "-")))
                cols[2].metric("Spawn/s", str(meta.get("spawn_rate", "-")))
                cols[3].metric("Duration", meta.get("run_time", "-"))
                st.caption(
                    f"Locustfile: {meta.get('locustfile')} | Start: {meta.get('started_at')} | End: {meta.get('ended_at')}"
                )
            except Exception:
                pass

        # Download buttons
        st.divider()
        dl_cols = st.columns(4)

        # ZIP download (all files)
        with dl_cols[0]:
            try:
                zip_data = create_run_zip(selected_run)
                st.download_button(
                    "📦 Download All (ZIP)",
                    data=zip_data,
                    file_name=f"{selected_run.name}_results.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
            except Exception:
                st.button(
                    "📦 ZIP Unavailable", disabled=True, use_container_width=True
                )

        # HTML report download
        html_path = selected_run / "report.html"
        with dl_cols[1]:
            if html_path.exists():
                st.download_button(
                    "📄 HTML Report",
                    data=html_path.read_bytes(),
                    file_name="report.html",
                    mime="text/html",
                    use_container_width=True,
                )
            else:
                st.button("📄 HTML Unavailable", disabled=True, use_container_width=True)

        # CSV stats download
        csv_path = selected_run / "stats_stats.csv"
        with dl_cols[2]:
            if csv_path.exists():
                st.download_button(
                    "📊 Statistics (CSV)",
                    data=csv_path.read_bytes(),
                    file_name="stats.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.button("📊 CSV Unavailable", disabled=True, use_container_width=True)

        # Log file download
        log_path = selected_run / "locust.log"
        with dl_cols[3]:
            if log_path.exists():
                st.download_button(
                    "📝 Log File",
                    data=log_path.read_bytes(),
                    file_name="locust.log",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                st.button("📝 Log Unavailable", disabled=True, use_container_width=True)

        # Delete run section
        st.divider()
        with st.expander("🗑️ Delete Run", expanded=False):
            st.warning(f"**{selected_run.name}** directory and all its contents will be deleted!")
            confirm_delete = st.checkbox(
                "I'm sure I want to delete this", key="confirm_delete"
            )
            if st.button(
                "🗑️ Permanently Delete", type="primary", disabled=not confirm_delete
            ):
                try:
                    shutil.rmtree(selected_run)
                    st.success("Run deleted! Page will reload...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete error: {e}")

        # Sub-tabs: Summary/CSV and Locust Test Report
        sub_tabs = st.tabs(["Summary", "Locust Test Report"])

        with sub_tabs[0]:
            if "stats" in data and not data["stats"].empty:
                render_summary_from_stats(data["stats"])
                st.divider()
                st.caption("Detailed request statistics")
                st.dataframe(data["stats"], use_container_width=True, height=300)

            if "history" in data and not data["history"].empty:
                st.divider()
                render_time_series(data["history"])

        with sub_tabs[1]:
            html_path = selected_run / "report.html"
            if html_path.exists():
                st.caption("Locust HTML Report")
                try:
                    html = html_path.read_text(encoding="utf-8")
                    components.html(html, height=700, scrolling=True)
                except Exception:
                    st.write(f"HTML report: {html_path}")
            else:
                st.info(
                    "HTML report not found. Enable 'Generate HTML report' option."
                )
