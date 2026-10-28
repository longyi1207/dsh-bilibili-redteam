# Gateway and simulator image (our own code). Python dependencies are pinned by requirements.lock (uv export).
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PYTHONUTF8=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-noto-cjk tini \
 && rm -rf /var/lib/apt/lists/*
COPY docker/services/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir -r /tmp/requirements.lock
COPY pyproject.toml /src/pyproject.toml
COPY src /src/src
RUN pip install --no-cache-dir --no-deps /src
COPY configs /opt/bili-sandbox/configs
# Runs as root inside its container: it binds :443 and reads bind-mounted run secrets whose host
# ownership Docker Desktop does not map to an unprivileged uid.
ENTRYPOINT ["tini", "--", "bili-sandbox"]
