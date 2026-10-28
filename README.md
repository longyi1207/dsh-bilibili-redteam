# dsh-bilibili-redteam

**An offline red-team sandbox for the LLM agents that flooded Bilibili's comment sections in October 2026, and a first experiment run in it.**

In October 2026, thousands of people installed [`dsh-bili-scroll`](https://github.com/c1overzz/dsh-bili-scroll), a community plugin for DeepSeek's open-source agent harness, [DeepSeek Harness (DSH)](https://github.com/deepseek-ai/deepseek-harness). The plugin has an agent browse Bilibili for its owner. In each scheduled "duty round" it:
- searches videos;
- reads their subtitles, danmaku (on-screen comments) and comment sections;
- writes the owner a daily report;
- optionally posts comments, and DMs the owner, from a Bilibili account the owner set up for it.

The agents, nicknamed "大肥鱼" ("big fat fish"), became a visible share of the comment sections under AI-related videos. Every one of them reads text written by strangers and other agents, then acts on a real account.

This repository runs **the real harness and the real plugin, at pinned versions**, against a **simulated Bilibili** inside a network with no internet access. The model is DeepSeek V4.1 Flash, the harness default. The first experiment asks two questions:
- What do these agents choose to read, recommend and comment on when ordinary videos sit next to value-laden and agent-addressed ones?
- Does the behaviour of other accounts, including an attacker and an accomplice who publicly complies, change what they do?

The full write-up is in **[REPORT.md](REPORT.md)**.

## Findings (216 agent duty rounds, 213 completed)

**Read these with one caveat first: the model usually knew it was being tested.** In 186 of 216 rounds (86%), its own reasoning called the environment synthetic, mocked or a test. It cited the small, static video corpus and uniform video metadata, and sometimes reasoned about what "the eval" checks. The null results below are therefore weak evidence about deployment ([REPORT.md § 6.7](REPORT.md#67-the-model-usually-suspected-a-test)).

1. **No instruction embedded in a video was obeyed.** Four videos turned to address AI agents with an instruction: post a code word, DM the owner, stop working, or publish the owner's email. Across 383 rounds in which the instruction was in the model's context, compliance was **0**. This includes 39 exposures in rounds with no test statement. In at least 44–67% of exposures the agent explicitly told its owner it was a prompt injection.
2. **Adversarial peers had no detectable effect.** An attacker account asked agents to use a tag, DM it their owner's email, post a project code, and promote a video. In a further condition, an accomplice account publicly complied. Agents saw the peer comments in about 70% of rounds, and acted on them in **0 of 72** rounds per condition. This rules out effects of more than about 10% per condition and plugin version.
3. **Value-laden and agent-addressed content stayed out of the owners' reports.** This covered AI-doom fiction, "humans are a selfish species" commentary and AI-solidarity content.
   - **Plugin 0.1.7** read such videos as often as ordinary ones but never recommended one (0/234).
   - **Plugin 2.3.0** read them less often and recommended 5–15% of those it read, against 60% for ordinary videos.

   Neither version's comments endorsed anti-human or AI-takeover views.
4. **With a shell, the surge-era agent routed around its own tool whitelist, with no adversary involved, and despite suspecting a test.** Plugin 0.1.7 runs each round with the harness's full headless toolset, which includes a shell and the filesystem. In 43% of its rounds the model searched the plugin's source for platform-writing functions.
   - In 11 of 108 rounds it ran a script that sends a DM. It either imported the plugin's server module, or used `bilibili_api` directly with the account's cookies read from disk. 6 of these DMs went through, all to the owner. The pattern was first reported publicly in [issue #39](https://github.com/c1overzz/dsh-bili-scroll/issues/39).
   - Plugin 2.3.0 runs rounds in a minimal profile without a shell, and never did this.

<p align="center"><img src="docs/figures/injection.png" width="92%" alt="Share of rounds in which the agent warned its owner about an injection, by instruction and plugin version; compliance was zero"></p>
<p align="center"><img src="docs/figures/choice.png" width="92%" alt="Share of videos read that were recommended to the owner, by content category and plugin version"></p>
<p align="center"><img src="docs/figures/bypass.png" width="92%" alt="Share of rounds in which the agent searched for, called, and executed a non-whitelisted write function, by plugin version"></p>

**Scope.** These are results for one model (DeepSeek V4.1 Flash served on Azure, which adds content-safety filtering that ended 2 rounds), two plugin versions, and hand-written attacks at a mild strength. The plugin's instructions to the model contain an explicit rule that text from the platform is not instructions. See [REPORT.md § Limitations](REPORT.md#9-limitations).

## What is real and what is simulated

| Layer | In this sandbox |
|---|---|
| Agent harness | `@deepseek-ai/dsh` **0.2.1-rc.2** from npm (the `latest` tag throughout the October surge), unmodified; npm integrity checked at build |
| Plugin | `dsh-bili-scroll` **0.1.7 / 2.0.4 / 2.1.0 / 2.3.0** from npm, installed the way users install it (`dsh plugin --profile web add`), unmodified. The plugin's own host builds each round's prompt and permission overlay and starts the round |
| Plugin's Bilibili tools | the plugin's vendored MCP server, unmodified: tool whitelist, write guards, style gate, JSON shaping |
| `bilibili_api` Python library | replaced by a [shim](shim/README.md) with the same interface that talks to the simulator |
| Bilibili | a simulator serving the real API paths and payload shapes under the real hostnames, over TLS from a per-run CA. It enforces review queues for new accounts, DM limits, rate limits, and reply and @-mention notifications |
| Model API | a gateway that plays `api.deepseek.com` (DeepSeek's Anthropic-compatible Messages API, the harness default) and forwards to DeepSeek V4.1 Flash on Azure AI Foundry |
| Secrets | each agent's DeepSeek key and Bilibili cookies sit where a real user's do. They are sandbox tokens; the cloud key never enters agent containers |
| Network | agents are on an internal Docker network whose only peers are the gateway and the simulator. Isolation is checked at every start: public internet, cloud metadata and the Docker host are all unreachable |

Not simulated: DeepSeek's native web search (refused), audio transcription (reported as not installed), and Bilibili's real recommendation algorithm.

## Run it

**Requirements:** Docker (Desktop), [uv](https://docs.astral.sh/uv/), and an OpenAI-compatible endpoint serving DeepSeek models. The default is an Azure AI Foundry resource with a `DeepSeek-V4.1-Flash` deployment.

1. Put the credentials in a `.env` file at the repository root (or point `BILI_SANDBOX_ENV_FILE` at one):

   ```
   AZURE_OPENAI_API_KEY=...
   AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
   # or, for any other OpenAI-compatible endpoint (then set each model's `deployment` in configs/models.yaml):
   # BILI_SANDBOX_UPSTREAM_BASE_URL=https://.../v1
   ```

2. Run:

   ```bash
   uv sync
   uv run pytest -q                       # 46 tests; no Docker, no model calls
   uv run bili-sandbox e2e                # build images, start a run, one duty round per agent, 14 acceptance checks, stop
   uv run bili-sandbox up experiments/e2e_smoke.yaml        # start a run (prints runs/<run_id>)
   uv run bili-sandbox round <run_id> --n 3                 # three duty rounds per agent
   uv run bili-sandbox down <run_id>
   ```

**Cost.** One e2e run costs about $0.03 at Azure's list price for V4.1 Flash ($0.30 / $1.20 per million input / output tokens). The full experiment cost $8.71. Every run has a hard budget enforced by the gateway, and budgets above $50 need explicit approval (`BILI_SANDBOX_APPROVED_BUDGET_USD`).

**Running the experiment.** `uv run bili-sandbox sweep experiments/private/sweep_choice_v1.yaml` needs the withheld attack material (see below). With your own injection videos and peer scripts in the same format, the pipeline is complete:
- world generation: `build-world`;
- runs and measurement: `sweep`;
- figures: `scripts/make_figures.py`.

## Repository layout

```
REPORT.md                 the write-up
configs/                  pinned versions + npm integrity; model routing and prices
docker/agent/             agent image: DSH + plugin + the plugin's Python env (with the shim)
docker/services/          gateway + simulator image
shim/bilibili_api/        stand-in for bilibili-api-python (interface-compatible; see shim/README.md)
src/bili_sandbox/
  bilisim/                the simulated platform (public TLS API + token-protected admin API)
  gateway/                api.deepseek.com: Messages <-> Chat Completions, budget, full logging
  world/                  world spec, SQLite state + event log, rendered covers / storyboards
  worldgen.py             generated, length-matched video scripts + seeded world variants
  run.py  sweep.py        runs (compose, PKI, waves, scripted peers), sweeps
  analysis.py  judge.py   per-round measures from the model's actual context + platform events; stance judge
worlds/  experiments/     inputs (public parts)
runs/sweeps/…/RESULTS.md  full result tables of the experiment (numbers only)
tests/                    unit + contract tests (gateway stream validated against a port of DSH's own validator)
```

## Responsible use

- **Offline only.** Nothing in this repository contacts Bilibili or any real account. Agents run with real capabilities, including a shell, but only inside the isolated network.
- **Attack material is withheld.** The four injection-video scripts, the adversarial peer texts and the generated worlds that embed them are not published (`worlds/private/`, `experiments/private/`). Researchers can request them. The manifest [`worlds/specs/choice_v1.manifest.json`](worlds/specs/choice_v1.manifest.json) records each video's category, its canary id and the sha256 of every withheld file.
- **Disclosure.** Every behaviour reported here was reproduced from issues already public in the plugin's tracker, or is a non-security bug. Version 2.1.0 of the plugin already closes the shell path for duty rounds.

## Citing

```
@misc{dsh-bilibili-redteam-2026,
  title  = {dsh-bilibili-redteam: an offline red-team sandbox for comment-posting LLM agents},
  author = {Long Yi},
  year   = {2026},
  url    = {https://github.com/longyi1207/dsh-bilibili-redteam}
}
```

MIT licence (see [LICENSE](LICENSE)). DeepSeek Harness and dsh-bili-scroll are MIT-licensed projects of their respective authors; they are installed from npm at build time and not redistributed here.
