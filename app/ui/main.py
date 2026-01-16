
import streamlit as st

from app.core.config import BASE_DIR
from app.ui.tabs.run_tab import render_run_tab
from app.ui.tabs.reporting_tab import render_reporting_tab
from app.ui.tabs.dashboard_tab import render_dashboard_tab
from app.ui.tabs.history_tab import render_history_tab
from app.ui.tabs.setup_tab import render_setup_tab
from app.ui.auth import check_password

def main():
    if not check_password():
        st.stop()

    st.set_page_config(page_title="Locust Web - Streamlit", layout="wide")
    st.title("Locust Load Tests - Streamlit Interface")

    tabs = st.tabs(
        [
            "Run Test",
            "View Reports",
            "Global Dashboard",
            "History Runs",
            "Setup",
        ]
    )

    with tabs[0]:
        render_run_tab(BASE_DIR)

    with tabs[1]:
        render_reporting_tab(BASE_DIR)

    with tabs[2]:
        render_dashboard_tab()

    with tabs[3]:
        render_history_tab()

    with tabs[4]:
        render_setup_tab()


if __name__ == "__main__":
    main()
