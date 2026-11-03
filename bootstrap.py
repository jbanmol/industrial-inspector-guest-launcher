"""Load the pinned private Inspector release on the guest host only."""

from functools import lru_cache
import hashlib
import os
import platform
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory

import httpx

REPO = "jbanmol/inspector-streamlit-preflight-20261103"
REVISION = "343ddedcc60961fbae62a4c990dc097039d4b420"
ARCHIVE_BYTES = 199_322_756
ARCHIVE_DIGEST = "sha256:4fe122111df8fe86e0c6556033e86346c875a70acca794bfca9488c2ec85cadc"
ORIGIN = "https://industrial-inspector-guest-jbanmol.streamlit.app"
state = {"phase": "restoring"}


@lru_cache(maxsize=1)
def load_runtime():
    if os.environ.get("INSPECTOR_DATABASE_URL"):
        raise ValueError("The guest app cannot use a private review database")
    token = os.environ.get("INSPECTOR_REPO_READ_TOKEN")
    if not token:
        import streamlit as st
        try:
            token = st.secrets.get("INSPECTOR_REPO_READ_TOKEN")
        except FileNotFoundError:
            return None
    if not token:
        return None
    if platform.system() != "Linux":
        raise RuntimeError("Restore the private Inspector runtime on hosted Linux only")
    os.environ["INSPECTOR_GUEST_ORIGIN"] = ORIGIN
    root = TemporaryDirectory(prefix="inspector-private-runtime-")
    work = Path(root.name)
    archive = work / "runtime.tar.gz"
    base = f"https://api.github.com/repos/{REPO}/releases"
    try:
        with httpx.Client(headers={"Authorization": f"Bearer {token}"}, follow_redirects=True,
                          timeout=httpx.Timeout(60, connect=15)) as client:
            release = client.get(f"{base}/tags/guest-{REVISION}").raise_for_status().json()
            assets = [asset for asset in release["assets"] if asset["name"] == "inspector-guest.tar.gz"]
            if release["target_commitish"] != REVISION or len(assets) != 1:
                raise ValueError("Unexpected private release")
            asset = assets[0]
            size, digest = asset["size"], asset["digest"]
            if size != ARCHIVE_BYTES or digest != ARCHIVE_DIGEST:
                raise ValueError("Invalid private release metadata")
            seen = 0
            fingerprint = hashlib.sha256()
            with client.stream("GET", f"{base}/assets/{int(asset['id'])}",
                               headers={"Accept": "application/octet-stream"}) as response:
                response.raise_for_status()
                with archive.open("xb") as output:
                    for block in response.iter_bytes(1024 * 1024):
                        seen += len(block)
                        if seen > size:
                            raise ValueError("Archive exceeds the recorded size")
                        fingerprint.update(block)
                        output.write(block)
            if seen != size or "sha256:" + fingerprint.hexdigest() != digest:
                raise ValueError("Private archive does not match its fingerprint")
        source = work / "source"
        source.mkdir()
        with tarfile.open(archive, "r:gz") as package:
            package.extractall(source, filter="data")
        archive.unlink()
        return root, source
    except Exception:
        root.cleanup()
        raise
