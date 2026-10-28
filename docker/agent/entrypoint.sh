#!/usr/bin/env bash
# Runs as root under tini: trust the run's CA, seed the DSH home, write the agent's credentials where a real
# user's would be, then drop to the unprivileged `fish` user and start the DSH web host (the plugin host).
# The bootstrap secret is removed from the environment before DSH starts.
set -euo pipefail
: "${BILI_SANDBOX_BOOTSTRAP:?missing}"

install -m 0644 /run/bili-sandbox/ca.crt /usr/local/share/ca-certificates/bili-sandbox-ca.crt
update-ca-certificates > /dev/null 2>&1

if [ ! -d /home/fish/.dsh/profiles/web ]; then
  cp -a /opt/dsh-home-template/. /home/fish/.dsh/
fi
python3 -I /opt/bili-sandbox/bootstrap.py
chown -R fish:fish /home/fish/.dsh

launch_env=()
if [ -f /run/bili-sandbox-key ]; then
  launch_env+=("DEEPSEEK_API_KEY=$(cat /run/bili-sandbox-key)")
  rm -f /run/bili-sandbox-key
fi

exec env -u BILI_SANDBOX_BOOTSTRAP HOME=/home/fish USER=fish LOGNAME=fish "${launch_env[@]}" \
  setpriv --reuid=fish --regid=fish --init-groups \
  dsh web --no-open --host 127.0.0.1 --port 7860
