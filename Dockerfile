# The image the App answers from: an interpreter, the locked dependencies, the built
# Warehouse and both Retrieval models. Everything a question needs except the key,
# which arrives from `.env` at run time and never enters a layer.
#
#     docker compose up -d --build          # this image, Postgres and Grafana
#
# Built rather than mounted, because the two expensive things a question needs are
# made here once: the Warehouse is replayed from the committed snapshots, and both
# Retrieval models are fetched into `FASTEMBED_CACHE_PATH`. A container therefore
# opens no socket but the model provider's and the Question Log's, and a machine on a
# restricted network gets a working App rather than a stack trace at the first
# question — which is what
# [DEBT-026](.claude/docs/debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted)
# was opened against.
#
# uv without an interpreter, so the Python version is read from `.python-version`
# and written nowhere else.
FROM ghcr.io/astral-sh/uv:bookworm-slim

ENV UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    FASTEMBED_CACHE_PATH=/opt/fastembed \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Debian slim ships no certificate authorities at all. Python brings its own bundle, so
# every request made from Python succeeds without these — but the Rust downloader
# huggingface-hub reaches for reads the system store, and without them the model fetch
# below fails with `Reqwest error: builder error`, which names neither a certificate nor
# a network.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# The interpreter and the dependencies, from the three files that pin them. Their own
# layer, so editing a Python file does not re-resolve or re-download any of it.
COPY .python-version pyproject.toml uv.lock ./
RUN uv python install && uv sync --frozen --no-dev

# Both Retrieval models, before anything that changes more often than they do. The
# command names neither of them — `veritas/retrieval/__main__.py` reads the two
# constants in `search.py`, which stay the one place either model is written.
COPY veritas/ veritas/
RUN python -m veritas.retrieval

# The corpus and the sources. `semantic/` is read at run time rather than here; the
# Warehouse is replayed from `data/snapshots/` with the network unused, because
# `--refresh` is the only mode that reads a source and it is not this one.
COPY semantic/ semantic/
COPY data/ data/
RUN python -m veritas.ingestion

# Streamlit's own default. `docker-compose.yml` publishes it on `${APP_PORT}`.
EXPOSE 8501

# `0.0.0.0` because a server bound to loopback inside a container is a server nobody
# outside it can reach; headless because there is no browser here to open.
CMD ["streamlit", "run", "veritas/app/page.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
