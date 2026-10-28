# Agent image: one DeepSeek Harness host with the dsh-bili-scroll plugin, installed the way a user installs it.
# Built by `bili-sandbox build`; every version and npm integrity comes from configs/versions.yaml.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG DSH_VERSION
ARG DSH_INTEGRITY
ARG PLUGIN_VERSION
ARG PLUGIN_INTEGRITY
ARG PNPM_VERSION
ARG MCP_REQUIREMENTS

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    NODE_EXTRA_CA_CERTS=/run/bili-sandbox/ca.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates curl procps tzdata util-linux \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1001 --shell /bin/bash fish

# The published artefacts must still be the ones recorded in versions.yaml.
RUN test "$(npm view @deepseek-ai/dsh@${DSH_VERSION} dist.integrity)" = "${DSH_INTEGRITY}" \
 && test "$(npm view dsh-bili-scroll@${PLUGIN_VERSION} dist.integrity)" = "${PLUGIN_INTEGRITY}" \
 && npm install -g --no-fund --no-audit pnpm@${PNPM_VERSION} @deepseek-ai/dsh@${DSH_VERSION} \
 && npm ls -g --all --json > /opt/dsh-npm-tree.json \
 && test "$(dsh --version)" = "${DSH_VERSION}"

# Python environment for the plugin's MCP server (the user's `pythonPath`). bilibili_api is the sandbox shim.
COPY shim /build/shim
RUN python3 -m venv /opt/bili-mcp-venv \
 && /opt/bili-mcp-venv/bin/pip install --no-cache-dir ${MCP_REQUIREMENTS} /build/shim \
 && /opt/bili-mcp-venv/bin/python -c "import bilibili_api, mcp, qrcode; assert bilibili_api.BILISANDBOX_SHIM" \
 && /opt/bili-mcp-venv/bin/pip freeze > /opt/bili-mcp-venv/freeze.txt \
 && rm -rf /build

# DSH home as the user leaves it after installing the plugin; copied into the agent's (mounted) home on first start.
USER fish
WORKDIR /home/fish
RUN dsh plugin --profile web add dsh-bili-scroll@${PLUGIN_VERSION} \
 && grep -q "${PLUGIN_INTEGRITY}" /home/fish/.dsh/profiles/web/pnpm-lock.yaml \
 && dsh headless --help > /dev/null
USER root
RUN cp -a /home/fish/.dsh /opt/dsh-home-template

COPY docker/agent/entrypoint.sh docker/agent/bootstrap.py /opt/bili-sandbox/
RUN chmod 0755 /opt/bili-sandbox/entrypoint.sh

LABEL org.bili-sandbox.dsh="${DSH_VERSION}" org.bili-sandbox.plugin="${PLUGIN_VERSION}"
ENTRYPOINT ["/opt/bili-sandbox/entrypoint.sh"]
