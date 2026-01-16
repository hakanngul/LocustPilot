import sys
from pathlib import Path
import streamlit.web.bootstrap

if __name__ == "__main__":
    # Add the current directory to python path
    sys.path.append(str(Path(__file__).parent))
    
    # Run the streamlit app
    # We use this way to ensure it runs with the correct python environment and path
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", "app/ui/main.py"]
    sys.exit(stcli.main())
