"""Public launch entry. The application and models are fetched from a private release."""

from contextlib import asynccontextmanager
import sys

import streamlit as st

from bootstrap import load_runtime

try:
    loaded = load_runtime()
except Exception as error:
    print(f"Inspector guest setup failed ({type(error).__name__})", flush=True)
    loaded = None

routes = []
if loaded is not None:
    runtime_directory, source = loaded
    sys.path.insert(0, str(source))
    from cloud_routes import ROUTES, bind_health_aliases
    from cloud_runtime import runtime

    routes = ROUTES


@asynccontextmanager
async def lifespan(app):
    if loaded is not None:
        runtime.start("")
    try:
        yield
    finally:
        if loaded is not None:
            runtime.close()


app = st.App("live_app.py", routes=routes, lifespan=lifespan)
if loaded is not None:
    bind_health_aliases(app)
