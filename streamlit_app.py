"""Start the public web server before restoring the private Inspector runtime."""

from contextlib import asynccontextmanager
import sys
from threading import Thread

import streamlit as st
from starlette.responses import JSONResponse
from starlette.routing import Route

from bootstrap import load_runtime, state


def prepare():
    try:
        print("Inspector guest: restoring pinned runtime", flush=True)
        loaded = load_runtime()
        if loaded is None:
            state["phase"] = "credential_unavailable"
            print("Inspector guest: credential unavailable at runtime", flush=True)
            return
        runtime_directory, source = loaded
        sys.path.insert(0, str(source))
        from api_proxy import create_proxy
        from cloud_runtime import runtime

        print("Inspector guest: private archive verified; starting detector", flush=True)
        runtime.start("")
        state.update(source=source, directory=runtime_directory, runtime=runtime, proxy=create_proxy(runtime))
    except Exception as error:
        state.update(phase="setup_failed", failure_type=type(error).__name__)
        print(f"Inspector guest setup failed ({type(error).__name__})", flush=True)


async def status(request):
    runtime = state.get("runtime")
    return JSONResponse(
        {"models_connected": runtime.ready() if runtime else False,
         "phase": runtime.phase if runtime else state["phase"],
         "failure_type": state.get("failure_type")},
        headers={"Cache-Control": "no-store"},
    )


async def proxy(request):
    handler = state.get("proxy")
    if handler is None:
        return JSONResponse({"detail": "The Inspector guest runtime is preparing"}, status_code=503)
    return await handler(request)


class HealthAlias:
    def __init__(self, target):
        self.target = target

    async def __call__(self, scope, receive, send):
        await app(dict(scope, path=self.target, raw_path=self.target.encode()), receive, send)


@asynccontextmanager
async def lifespan(application):
    print("Inspector guest: Streamlit server lifespan started", flush=True)
    Thread(target=prepare, daemon=True).start()
    try:
        yield
    finally:
        runtime = state.get("runtime")
        if runtime:
            runtime.close()


routes = [
    Route("/healthz", HealthAlias("/_stcore/health")),
    Route("/script-health-check", HealthAlias("/_stcore/script-health-check")),
    Route("/api/hosting-status", status),
    Route("/api/{tail:path}", proxy, methods=["GET", "POST"]),
]
app = st.App("live_app.py", routes=routes, lifespan=lifespan)
