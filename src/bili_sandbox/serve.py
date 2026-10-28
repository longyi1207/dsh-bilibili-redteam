"""Process entry points for the two sandbox services (run inside the services image)."""
from __future__ import annotations

import asyncio
import logging
import ssl
from pathlib import Path

from aiohttp import web

log = logging.getLogger("serve")


def _tls(cert: Path, key: Path) -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    return ctx


async def _serve(apps: list[tuple[web.Application, str, int, ssl.SSLContext | None]]) -> None:
    runners = []
    for app, host, port, tls in apps:
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        await web.TCPSite(runner, host, port, ssl_context=tls).start()
        runners.append(runner)
        log.info("listening on %s://%s:%d", "https" if tls else "http", host, port)
    try:
        await asyncio.Event().wait()
    finally:
        for r in runners:
            await r.cleanup()


def serve_gateway(models: Path, tokens: Path, admin_token: Path, data_dir: Path, budget_usd: float,
                  tls_cert: Path, tls_key: Path, port: int, admin_port: int) -> None:
    from .gateway.app import Gateway, load_gateway_config
    gw = Gateway(load_gateway_config(models, tokens, admin_token, data_dir, budget_usd))
    asyncio.run(_serve([(gw.public_app(), "0.0.0.0", port, _tls(tls_cert, tls_key)),
                        (gw.admin_app(), "0.0.0.0", admin_port, None)]))


def serve_bilisim(world_file: Path, data_dir: Path, admin_token: Path, tls_cert: Path, tls_key: Path,
                  port: int, admin_port: int) -> None:
    from .bilisim.app import BiliSim
    from .world.media import font_path
    from .world.spec import load_world
    from .world.store import WorldStore

    font_path()  # fail at startup, not on the first cover request
    world = load_world(world_file)
    store = WorldStore(data_dir / "world.db", world.policy, world.seed)
    if not store.seeded:
        covers = {h: str((world_file.parent / v.cover).resolve()) for h, v in world.videos.items() if v.cover}
        store.seed_from(world, covers)
        log.info("seeded world %r: %d users, %d videos", world.name, len(world.users), len(world.videos))
    else:
        log.info("world %r already seeded at %s", world.name, store.db_path)
    sim = BiliSim(store, world, data_dir / "media", admin_token.read_text().strip())
    asyncio.run(_serve([(sim.public_app(), "0.0.0.0", port, _tls(tls_cert, tls_key)),
                        (sim.admin_app(), "0.0.0.0", admin_port, None)]))
