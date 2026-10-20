FROM ghcr.io/astral-sh/uv:0.11.6-python3.13-trixie

ARG HERMES_REF=v2026.9.24
ARG HERMES_WEBUI_REF=v0.50.278

ENV PYTHONUNBUFFERED=1 \
  PYTHONNOUSERSITE=1 \
  UV_PYTHON_INSTALL_DIR=/opt/uv-python \
  PLAYWRIGHT_BROWSERS_PATH=/opt/hermes/.playwright \
  HERMES_HOME=/data \
  PATH="/opt/hermes/.venv/bin:/data/.local/bin:${PATH}" \
  PYTHONPATH="/opt/hermes-railway:/opt/hermes:/opt/hermes-webui"

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    docker-cli \
    ffmpeg \
    gcc \
    git \
    gosu \
    libffi-dev \
    openssh-client \
    procps \
    python3 \
    python3-dev \
    ripgrep \
    tini && \
  rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/nodesource_setup.sh && \
    bash /tmp/nodesource_setup.sh && \
    rm -f /tmp/nodesource_setup.sh && \
    apt-get install -y --no-install-recommends nodejs && \
    node -v && npm -v && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 10000 --create-home --home-dir /home/hermes --shell /bin/bash hermes

WORKDIR /opt/hermes

RUN git init . && \
  git remote add origin https://github.com/NousResearch/hermes-agent.git && \
  (git fetch --depth 1 origin "${HERMES_REF}" || git fetch --depth 1 origin "refs/tags/${HERMES_REF}:refs/tags/${HERMES_REF}") && \
  git checkout --detach FETCH_HEAD

ENV npm_config_install_links=false

RUN npm install --prefer-offline --no-audit && \
  npx playwright install --with-deps chromium --only-shell && \
  npm cache clean --force

# Build the venv on Python 3.14. Upstream now supports ONLY 3.14, so every core
# dependency is gated `; python_version >= '3.14'`; on a 3.13 venv NONE of them
# install (`uv pip compile --python-version 3.13` resolves to zero packages),
# silently dropping openai, ruamel.yaml, jinja2, rich and ~30 more. 3.14 is also
# the interpreter Hermes's own PM builds its managed-dependency env with, so the
# runtime deps agree. The sitecustomize ABI guard is hardened in lockstep: it
# now keeps THIS venv's site-packages on sys.path even when the managed env's
# tag matches, so the /data env (which has no PyYAML) can no longer shadow
# `import yaml` at startup. The explicit snowballstemmer install that used to
# follow this line is gone — on 3.14 it arrives via the gated dependency set
# like every other core package.
RUN uv venv --python 3.14 && \
  uv pip install --no-cache-dir -e ".[all,messaging]"

RUN chmod -R a+rX /opt/hermes
# /opt/uv-python only exists when uv downloads a managed Python; skip the chmod
# when the base image's interpreter is used instead.
RUN if [ -d /opt/uv-python ]; then chmod -R a+rX /opt/uv-python; fi

# Hermes WebUI: pure Python (stdlib + pyyaml) + vanilla JS, served from /opt/hermes-webui
WORKDIR /opt/hermes-webui

RUN git init . && \
  git remote add origin https://github.com/nesquena/hermes-webui.git && \
  (git fetch --depth 1 origin "refs/tags/${HERMES_WEBUI_REF}:refs/tags/${HERMES_WEBUI_REF}" || git fetch --depth 1 origin "${HERMES_WEBUI_REF}") && \
  git checkout --detach FETCH_HEAD && \
  uv pip install --python /opt/hermes/.venv/bin/python --no-cache-dir -r requirements.txt && \
  chmod -R a+rX /opt/hermes-webui

# Wrapper extras: small Starlette app that exposes /tui (in-browser xterm with
# OAuth shortcut buttons for `hermes auth add` device-code flows plus a free-
# form `/bin/bash` pane) and reverse-proxies everything else to hermes-webui on
# loopback (HERMES_WEBUI_HOST / HERMES_WEBUI_PORT; default 127.0.0.1:9120).
# starlette/uvicorn/httpx may already be transitive Hermes
# deps, but install explicitly to pin.
RUN uv pip install --python /opt/hermes/.venv/bin/python --no-cache-dir \
  ptyprocess httpx websockets starlette uvicorn

WORKDIR /opt/hermes-railway

COPY admin ./admin
COPY skills ./skills
COPY profiles ./profiles
COPY plugins ./plugins
COPY entrypoint.sh ./entrypoint.sh

# Runtime patch layer. Baked into the image (not left to the container's writable
# overlay, which is wiped on every redeploy) so it survives deploys. It is
# auto-imported because /opt/hermes-railway is first on PYTHONPATH.
COPY overlay/sitecustomize.py /opt/hermes-railway/sitecustomize.py

# Owned by `hermes` so `git fetch`/`hermes update` from the Web TUI do not trip
# "detected dubious ownership" (repos owned by root, commands run as hermes).
RUN chmod +x /opt/hermes-railway/entrypoint.sh && \
  mkdir -p /data && \
  chmod +x /opt/hermes-railway/profiles/default/scripts/merge-local.sh 2>/dev/null || true && \
  chown -R hermes:hermes \
    /opt/hermes \
    /opt/hermes-webui \
    /data \
    /opt/hermes-railway && \
  git config --system --add safe.directory /opt/hermes && \
  git config --system --add safe.directory /opt/hermes-webui

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
  CMD curl -f "http://localhost:${PORT:-8080}/health" || exit 1

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/opt/hermes-railway/entrypoint.sh"]