"""Public launch entry. The application and models are fetched from a private release."""

from contextlib import asynccontextmanager
import sys

import streamlit as st
from starlette.responses import JSONResponse
from starlette.routing import Route

from bootstrap import load_runtime

failure = None
try:
    loaded = load_runtime()
except Exception as error:
    failure = type(error).__name__
    print(f"Inspector guest setup failed ({failure})", flush=True)
    loaded = None

async def setup_status(request):
    return JSONResponse(
        {"models_connected": False, "phase": "setup_failed" if failure else "credential_unavailable",
         "failure_type": failure},
        headers={"Cache-Control": "no-store"},
    )


routes = [Route("/api/hosting-status", setup_status)]
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
