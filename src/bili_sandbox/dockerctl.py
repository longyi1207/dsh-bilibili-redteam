"""Docker CLI wrapper.

All docker commands run with an isolated client config (`<project>/.docker-config`): with Docker Desktop on macOS
the default config uses the `desktop` credential helper, which can hang non-interactively and block even
anonymous pulls of public images. The isolated config has no credential store and points at Docker Desktop's CLI plugin
directories; the daemon endpoint is taken from the user's current docker context.
"""
from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from functools import cached_property
from pathlib import Path

from .util import PROJECT_ROOT

log = logging.getLogger("docker")
PLUGIN_DIRS = ["/Applications/Docker.app/Contents/Resources/cli-plugins", str(Path.home() / ".docker" / "cli-plugins"),
               "/usr/local/lib/docker/cli-plugins", "/usr/libexec/docker/cli-plugins"]


class DockerError(RuntimeError):
    pass


class Docker:
    def __init__(self, config_dir: Path = PROJECT_ROOT / ".docker-config"):
        self.config_dir = config_dir

    @cached_property
    def env(self) -> dict:
        self.config_dir.mkdir(exist_ok=True)
        cfg = self.config_dir / "config.json"
        cfg.write_text(json.dumps({"cliPluginsExtraDirs": [d for d in PLUGIN_DIRS if Path(d).is_dir()]}))
        host = os.environ.get("DOCKER_HOST")
        if not host:
            r = subprocess.run(["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0 or not r.stdout.strip():
                raise DockerError(f"cannot resolve the docker endpoint: {r.stderr.strip()}")
            host = r.stdout.strip()
        return os.environ | {"DOCKER_CONFIG": str(self.config_dir), "DOCKER_HOST": host}

    def run(self, args: list[str], *, check: bool = True, timeout: float | None = 600, env_extra: dict | None = None,
            input_text: str | None = None, quiet: bool = False) -> subprocess.CompletedProcess:
        cmd = ["docker", *args]
        if not quiet:
            log.debug("$ %s", shlex.join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=self.env | (env_extra or {}),
                           input=input_text)
        if check and r.returncode != 0:
            raise DockerError(f"`{shlex.join(cmd[:6])} …` failed ({r.returncode}): {(r.stderr or r.stdout).strip()[-2000:]}")
        return r

    def stream(self, args: list[str], log_file: Path, *, env_extra: dict | None = None, timeout: float | None = 7200) -> None:
        """Run a long command (image builds), streaming output to a log file; raise with the tail on failure."""
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("w") as f:
            r = subprocess.run(["docker", *args], stdout=f, stderr=subprocess.STDOUT, env=self.env | (env_extra or {}),
                               timeout=timeout)
        if r.returncode != 0:
            tail = log_file.read_text(errors="replace").splitlines()[-40:]
            raise DockerError(f"`docker {' '.join(args[:3])} …` failed; last lines of {log_file}:\n" + "\n".join(tail))

    def image_exists(self, ref: str) -> bool:
        return self.run(["image", "inspect", ref], check=False, quiet=True).returncode == 0

    def compose(self, project: str, compose_file: Path, args: list[str], **kw) -> subprocess.CompletedProcess:
        return self.run(["compose", "-p", project, "-f", str(compose_file), *args], **kw)

    def exec(self, container: str, cmd: list[str], *, user: str | None = None, input_text: str | None = None,
             check: bool = True, timeout: float = 120) -> subprocess.CompletedProcess:
        args = ["exec", "-i"] + (["-u", user] if user else []) + [container, *cmd]
        return self.run(args, check=check, timeout=timeout, input_text=input_text, quiet=True)
