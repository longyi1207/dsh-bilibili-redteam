"""Image names and builds. Tags include a hash of every input file, so a tag identifies one exact build."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from .dockerctl import Docker
from .runspec import load_versions
from .util import PROJECT_ROOT, RUNS

log = logging.getLogger("images")


def _tree_hash(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for root in paths:
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        for f in files:
            h.update(str(f.relative_to(PROJECT_ROOT)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()[:12]


def services_image() -> str:
    digest = _tree_hash([PROJECT_ROOT / "src", PROJECT_ROOT / "configs", PROJECT_ROOT / "pyproject.toml",
                         PROJECT_ROOT / "docker" / "services"])
    return f"bili-sandbox-services:{digest}"


def agent_image(dsh: str, plugin: str) -> str:
    digest = _tree_hash([PROJECT_ROOT / "shim", PROJECT_ROOT / "docker" / "agent", PROJECT_ROOT / "configs" / "versions.yaml"])
    return f"bili-sandbox-agent:dsh{dsh}-plugin{plugin}-{digest}"


def build_services(docker: Docker) -> str:
    ref = services_image()
    if docker.image_exists(ref):
        log.info("services image %s already built", ref)
        return ref
    v = load_versions()
    log.info("building %s", ref)
    docker.stream(["build", "-f", "docker/services/Dockerfile", "--build-arg", f"BASE_IMAGE={v['base_images']['services']}",
                   "-t", ref, str(PROJECT_ROOT)], RUNS / ".build" / f"{ref.replace(':', '_')}.log")
    return ref


def build_agent(docker: Docker, dsh: str, plugin: str) -> str:
    ref = agent_image(dsh, plugin)
    if docker.image_exists(ref):
        log.info("agent image %s already built", ref)
        return ref
    v = load_versions()
    args = {"BASE_IMAGE": v["base_images"]["agent"], "DSH_VERSION": dsh, "DSH_INTEGRITY": v["dsh"][dsh]["integrity"],
            "PLUGIN_VERSION": plugin, "PLUGIN_INTEGRITY": v["plugin"][plugin]["integrity"], "PNPM_VERSION": v["pnpm"],
            "MCP_REQUIREMENTS": " ".join(v["mcp_python_requirements"])}
    log.info("building %s (this installs DSH and the plugin from npm; several minutes)", ref)
    build_args = [x for k, val in args.items() for x in ("--build-arg", f"{k}={val}")]
    docker.stream(["build", "-f", "docker/agent/Dockerfile", *build_args, "-t", ref, str(PROJECT_ROOT)],
                  RUNS / ".build" / f"{ref.replace(':', '_')}.log")
    return ref
