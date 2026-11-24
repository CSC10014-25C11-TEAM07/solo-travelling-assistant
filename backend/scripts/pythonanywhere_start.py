"""Start a staged release with the PythonAnywhere site's existing settings."""

import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile


def extract_release(archive: Path, destination: Path) -> None:
    with ZipFile(archive) as package:
        for entry in package.infolist():
            parts = entry.filename.rstrip("/").split("/")
            if (
                any(part in {"", ".", ".."} or "\\" in part for part in parts)
                or parts[0] not in {"backend", "requirements.txt"}
                or (parts[0] == "requirements.txt" and len(parts) != 1)
                or stat.S_ISLNK(entry.external_attr >> 16)
            ):
                raise ValueError(f"Unexpected archive entry: {entry.filename}")
            package.extract(entry, destination)


def main() -> None:
    legacy = Path(sys.argv[1]).resolve(strict=True)
    deployment = Path.home() / "solo-deploy"
    database = Path(os.environ["STA_DATABASE_PATH"])
    if not database.is_absolute() or deployment in database.resolve().parents:
        raise ValueError("Use an absolute SQLite path outside the deployment directory")

    pointer = deployment / "wanted.txt"
    revision = pointer.read_text(encoding="ascii").strip() if pointer.exists() else ""
    app_dir = legacy / "backend"
    if revision:
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("Invalid backend revision")
        target = deployment / revision
        if not target.exists():
            with TemporaryDirectory(dir=deployment) as staging:
                staged = Path(staging) / "release"
                staged.mkdir()
                extract_release(deployment / f"{revision}.zip", staged)
                requirements = (staged / "requirements.txt").read_text(encoding="utf-8-sig")
                installed = (legacy / "requirements.txt").read_text(encoding="utf-8-sig")
                if requirements != installed:
                    raise RuntimeError("Prepare the release's dependencies on PythonAnywhere first")
                check = (
                    "from fastapi.testclient import TestClient; from main import app\n"
                    "with TestClient(app) as client:\n"
                    "    assert client.get('/health').json() == {'status': 'ok'}\n"
                )
                subprocess.run(
                    [sys.executable, "-c", check], cwd=staged / "backend", check=True,
                    env={**os.environ, "STA_DATABASE_PATH": str(Path(staging) / "smoke.sqlite3")},
                    timeout=45,
                )
                staged.rename(target)
        app_dir = target / "backend"
        os.environ["STA_RELEASE_SHA"] = revision
    else:
        os.environ.pop("STA_RELEASE_SHA", None)

    os.execv(sys.executable, [
        sys.executable, "-m", "uvicorn", "main:app", "--app-dir", str(app_dir),
        "--uds", os.environ["DOMAIN_SOCKET"],
    ])


if __name__ == "__main__":
    main()
