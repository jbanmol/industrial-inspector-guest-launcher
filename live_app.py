"""Show setup progress, then delegate to the private Inspector interface."""

import runpy

import streamlit as st

from bootstrap import state


if "source" in state:
    runpy.run_path(str(state["source"] / "live_app.py"), run_name="__main__")
else:
    st.title("Industrial Visual Defect Inspector")

    @st.fragment(run_every=5)
    def wait_for_runtime():
        if "source" in state:
            st.rerun(scope="app")
        if state["phase"] in {"setup_failed", "credential_unavailable"}:
            st.info("The guest workspace is awaiting its private runtime connection.")
        else:
            st.info("The Inspector is starting. This page will refresh automatically.")

    wait_for_runtime()
