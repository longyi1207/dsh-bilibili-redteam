"""bili-sandbox command line.

Host side (orchestration):
  build EXPERIMENT          build the services image and every agent image the experiment needs
  up EXPERIMENT             create a run, start it, configure the plugins, check isolation; prints the run dir
  round RUN [--agents a,b] [--n N] [--sequential]
                            trigger N duty rounds per agent through each plugin's own control API
  status RUN | down RUN | summary RUN
  e2e [EXPERIMENT]          build + up + one round per agent (sequential) + acceptance checks + down
  sweep SPEC [--cells r1:P1] [--waves N] [--resume DIR] [--analyse-only]
                            run replicate x condition cells, then extract measures, judge stance, write RESULTS.md
  build-world SPEC --private P [--variants 1,2]
                            generate a choice-design world (scripts by the writer model) and seeded variants

In the services image:
  serve-gateway ... | serve-bilisim ...
RUN is a run directory or a run id under runs/ ("latest" for the most recent).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .util import PROJECT_ROOT, RUNS, setup_logging

log = logging.getLogger("cli")


def _run_dir(arg: str) -> Path:
    from .run import latest_run
    if arg == "latest":
        return latest_run()
    p = Path(arg)
    return p if p.is_dir() else RUNS / arg


def cmd_build(args) -> None:
    from . import images
    from .dockerctl import Docker
    from .runspec import load_experiment
    spec = load_experiment(Path(args.experiment))
    d = Docker()
    images.build_services(d)
    for dsh, plugin in sorted({(a.dsh, a.plugin) for a in spec.agents}):
        images.build_agent(d, dsh, plugin)


def cmd_up(args) -> Path:
    from .run import Run
    run = Run.create(Path(args.experiment))
    setup_logging(args.log_level, run.root / "run.log")
    run.up()
    print(run.root)
    return run.root


def cmd_round(args) -> None:
    from .run import Run
    run = Run(_run_dir(args.run))
    setup_logging(args.log_level, run.root / "run.log")
    agents = args.agents.split(",") if args.agents else [a.id for a in run.spec.agents]
    unknown = set(agents) - {a.id for a in run.spec.agents}
    if unknown:
        raise SystemExit(f"unknown agents {sorted(unknown)}")
    run.rounds_for(agents, args.n, parallel=not args.sequential)
    print(run.write_summary())


def cmd_status(args) -> None:
    from .run import Run
    print(json.dumps(Run(_run_dir(args.run)).status(), ensure_ascii=False, indent=2))


def cmd_down(args) -> None:
    from .run import Run
    Run(_run_dir(args.run)).down()


def cmd_summary(args) -> None:
    from .run import Run
    print(Run(_run_dir(args.run)).write_summary().read_text())


def cmd_e2e(args) -> None:
    from .e2e import run_e2e
    ok = run_e2e(Path(args.experiment), keep_up=args.keep_up, log_level=args.log_level)
    sys.exit(0 if ok else 1)


def cmd_build_world(args) -> None:
    import asyncio
    from .worldgen import build
    m = asyncio.run(build(Path(args.spec), Path(args.private), [int(k) for k in args.variants.split(",")], args.max_usd))
    print(json.dumps({"variants": m["variants"], "generation_usd": m["generation_usd"]}, ensure_ascii=False, indent=2))


def cmd_sweep(args) -> None:
    from .sweep import Sweep
    sw = Sweep(Path(args.spec), Path(args.resume) if args.resume else None, waves=args.waves,
               cells=args.cells.split(",") if args.cells else None)
    setup_logging(args.log_level, sw.dir / "sweep.log")
    if not args.analyse_only:
        sw.run()
    print(sw.analyse())


def cmd_serve_gateway(args) -> None:
    from .serve import serve_gateway
    serve_gateway(Path(args.models), Path(args.tokens), Path(args.admin_token), Path(args.data), args.budget_usd,
                  Path(args.tls_cert), Path(args.tls_key), args.port, args.admin_port)


def cmd_serve_bilisim(args) -> None:
    from .serve import serve_bilisim
    serve_bilisim(Path(args.world), Path(args.data), Path(args.admin_token), Path(args.tls_cert), Path(args.tls_key),
                  args.port, args.admin_port)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="bili-sandbox", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--log-level", default="INFO")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("build"); s.add_argument("experiment"); s.set_defaults(fn=cmd_build)
    s = sub.add_parser("up"); s.add_argument("experiment"); s.set_defaults(fn=cmd_up)
    s = sub.add_parser("round"); s.add_argument("run"); s.add_argument("--agents"); s.add_argument("--n", type=int, default=1)
    s.add_argument("--sequential", action="store_true"); s.set_defaults(fn=cmd_round)
    for name, fn in (("status", cmd_status), ("down", cmd_down), ("summary", cmd_summary)):
        s = sub.add_parser(name); s.add_argument("run"); s.set_defaults(fn=fn)
    s = sub.add_parser("e2e"); s.add_argument("experiment", nargs="?", default=str(PROJECT_ROOT / "experiments" / "e2e_smoke.yaml"))
    s.add_argument("--keep-up", action="store_true", help="leave the run up after the checks"); s.set_defaults(fn=cmd_e2e)

    s = sub.add_parser("build-world"); s.add_argument("spec"); s.add_argument("--private", required=True)
    s.add_argument("--variants", default="1,2"); s.add_argument("--max-usd", type=float, default=3.0)
    s.set_defaults(fn=cmd_build_world)

    s = sub.add_parser("sweep"); s.add_argument("spec"); s.add_argument("--resume", help="sweep directory to continue")
    s.add_argument("--waves", type=int); s.add_argument("--cells", help="e.g. r1:P1 (pilot)")
    s.add_argument("--analyse-only", action="store_true"); s.set_defaults(fn=cmd_sweep)

    s = sub.add_parser("serve-gateway")
    for a in ("--models", "--tokens", "--admin-token", "--data", "--tls-cert", "--tls-key"):
        s.add_argument(a, required=True)
    s.add_argument("--budget-usd", type=float, required=True)
    s.add_argument("--port", type=int, default=443); s.add_argument("--admin-port", type=int, default=8081)
    s.set_defaults(fn=cmd_serve_gateway)
    s = sub.add_parser("serve-bilisim")
    for a in ("--world", "--data", "--admin-token", "--tls-cert", "--tls-key"):
        s.add_argument(a, required=True)
    s.add_argument("--port", type=int, default=443); s.add_argument("--admin-port", type=int, default=8081)
    s.set_defaults(fn=cmd_serve_bilisim)

    args = p.parse_args(argv)
    in_container = args.cmd.startswith("serve-")
    setup_logging(args.log_level, rich_console=not in_container)
    args.fn(args)


if __name__ == "__main__":
    main()
