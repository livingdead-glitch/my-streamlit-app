"""Keep the existing Streamlit Cloud entrypoint while running the learning app."""
from pathlib import Path
import runpy


# Execute on every Streamlit rerun; importing the app would cache its UI module.
# The target's __file__ remains correct for local .env and package resolution.
runpy.run_path(
    str(Path(__file__).resolve().parent / "learning_assistant" / "app.py"),
    run_name="__main__",
)
