
import streamlit as st

def render_setup_tab():
    st.subheader("Setup and Usage")
    st.markdown(
        """
        - Install required packages: `pip install -r requirements.txt`
        - Start the application: `streamlit run app.py`
        - Select locustfile and parameters on the left, start the test.
        - Test outputs are stored in `runs/` directory.
        """
    )
