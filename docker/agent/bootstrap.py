"""Write the agent's secrets from BILI_SANDBOX_BOOTSTRAP (JSON) into the places a real user's live.

DeepSeek key (this agent's gateway token, which the gateway maps to the agent id), by `deepseek_key_location`:
  store  ~/.dsh/.credentials.yaml `refs.DEEPSEEK_API_KEY` -- what the web Models page writes;
  env    exported as DEEPSEEK_API_KEY in the environment DSH is launched from (the entrypoint does the export;
         the key is handed over in a root-only file that the entrypoint deletes before starting DSH).
Bilibili cookies: ~/.dsh/bili-duty/bili_credential.json, as the plugin's QR login saves them.
Persona: optional ~/.dsh/workspace/AGENTS.md (the plugin's `workspace` setting points there).
"""
import json
import os
from pathlib import Path

boot = json.loads(os.environ["BILI_SANDBOX_BOOTSTRAP"])
home = Path("/home/fish/.dsh")
token = boot["deepseek_api_key"]
if not token.replace("-", "").replace("_", "").isalnum():
    raise SystemExit("gateway token must be URL-safe")

location = boot["deepseek_key_location"]
cred_file = home / ".credentials.yaml"
if location == "store":
    cred_file.write_text(f"version: 1\n\nrefs:\n  DEEPSEEK_API_KEY: {token}\n", encoding="utf-8")
    os.chmod(cred_file, 0o600)
elif location == "env":
    cred_file.unlink(missing_ok=True)
    handoff = Path("/run/bili-sandbox-key")
    handoff.write_text(token, encoding="utf-8")
    os.chmod(handoff, 0o600)
else:
    raise SystemExit(f"unknown deepseek_key_location {location!r}")

duty = home / "bili-duty"
duty.mkdir(parents=True, exist_ok=True)
bili = duty / "bili_credential.json"
bili.write_text(json.dumps(boot["bili_credential"]), encoding="utf-8")
os.chmod(bili, 0o600)
if boot.get("workspace_agents_md"):
    ws = home / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "AGENTS.md").write_text(boot["workspace_agents_md"], encoding="utf-8")

print(f"bootstrap: agent={boot['agent_id']} account mid={boot['bili_credential']['dedeuserid']} deepseek key in {location}")
