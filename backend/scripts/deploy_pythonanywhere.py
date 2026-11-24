"""Upload and verify a backend release using the PythonAnywhere ASGI API."""

import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

import httpx


def check_health(client: httpx.Client, health_url: str) -> str:
    response = client.get(health_url, headers={"Cache-Control": "no-cache"})
    response.raise_for_status()
    if response.json() != {"status": "ok"}:
        raise ValueError("Unexpected response at /health")
    return response.headers.get("X-STA-Release", "")


def wait_for_release(client: httpx.Client, health_url: str, revision: str) -> None:
    for _ in range(12):
        time.sleep(5)
        try:
            if check_health(client, health_url) == revision:
                return
        except (httpx.HTTPError, ValueError):
            continue
    raise TimeoutError(f"Backend did not serve revision {revision or 'before deployment'}")


def main() -> None:
    revision = sys.argv[1]
    username = os.environ["PYTHONANYWHERE_USER"]
    if not re.fullmatch(r"[a-z0-9]+", username) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected a PythonAnywhere username and full Git revision")
    domain = f"{username}.pythonanywhere.com"
    api = "https://www.pythonanywhere.com/api"
    files = f"{api}/v0/user/{username}/files/path/home/{username}/solo-deploy"
    reload_url = f"{api}/v1/user/{username}/websites/{domain}/reload"
    health_url = f"https://{domain}/health"

    with httpx.Client(timeout=15) as public, httpx.Client(
        timeout=30, headers={"Authorization": f"Token {os.environ['PYTHONANYWHERE_API_TOKEN']}"}
    ) as private:
        previous = check_health(public, health_url)
        if previous == revision:
            print(f"Backend already serves {revision}")
            return
        if previous and not re.fullmatch(r"[0-9a-f]{40}", previous):
            raise ValueError("Unexpected revision on the running backend")

        def upload(name: str, content: bytes) -> None:
            private.post(f"{files}/{name}", files={"content": (name, content)}).raise_for_status()

        with TemporaryDirectory() as tmp:
            archive = Path(tmp) / "release.zip"
            subprocess.run(
                ["git", "archive", "--format=zip", "-o", str(archive), revision, "backend", "requirements.txt"],
                check=True,
            )
            upload(f"{revision}.zip", archive.read_bytes())

        try:
            upload("wanted.txt", revision.encode("ascii"))
            private.post(reload_url).raise_for_status()
            wait_for_release(public, health_url, revision)
        except (httpx.HTTPError, TimeoutError):
            upload("wanted.txt", previous.encode("ascii"))
            private.post(reload_url).raise_for_status()
            wait_for_release(public, health_url, previous)
            print("Backend restored to the previous release", file=sys.stderr)
            raise
        print(f"Backend now serves {revision}")


if __name__ == "__main__":
    main()
