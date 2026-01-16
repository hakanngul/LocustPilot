
import streamlit as st
from app.core.data import list_runs

def render_history_tab():
    st.subheader("History Runs")
    runs = list_runs()
    if not runs:
        st.info("No recorded runs.")
    else:
        for r in runs:
            any_stats = any(r.glob("*_stats.csv"))
            html_exists = (r / "report.html").exists()
            st.write(
                f"- {r.name}  | CSV: {'✅' if any_stats else '❌'} | HTML: {'✅' if html_exists else '❌'}  | Directory: {r}"
            )
