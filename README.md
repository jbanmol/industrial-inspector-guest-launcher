# Industrial Visual Defect Inspector guest launcher

This repository contains only the Streamlit entry point. The Inspector interface, trained models, and sample inputs live in a separate private release. Guest reviews are temporary and isolated by browser session. The guest service does not connect to the private review database.

Deploy `streamlit_app.py` with Python 3.13 at `industrial-inspector-guest-jbanmol.streamlit.app`. In the new app's private Streamlit Secrets, set `INSPECTOR_REPO_READ_TOKEN` to a GitHub fine-grained token scoped to `jbanmol/inspector-streamlit-preflight-20261103` with Contents read-only. Keep the value out of source control.
