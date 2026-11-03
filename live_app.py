"""Delegate the visible page to the private Inspector application."""

import runpy

import streamlit as st

from streamlit_app import loaded

if loaded is None:
    st.title("Industrial Visual Defect Inspector")
    st.info("The guest workspace is awaiting its private runtime connection.")
else:
    runpy.run_path(str(loaded[1] / "live_app.py"), run_name="__main__")
