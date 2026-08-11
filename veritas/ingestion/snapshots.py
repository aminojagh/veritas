"""Snapshot-and-replay — the one mechanism every real source is read through.

**Replay is the default and the network is the exception.** A clone with no
network runs the whole pipeline from `data/snapshots/ingestion/`; `--refresh`
re-hits the sources and rewrites those files. That is the mitigation
[DEBT-002](../../.claude/docs/debt-ledger.md) was opened for, and ADR-0004 records
why it is applied to every source here rather than only to the one that needs it.

The rule this file exists to enforce: **nothing else in `veritas/ingestion/` opens
a socket.** A source module asks for bytes by name and cannot tell whether they
came from disk or the network, so there is exactly one place where "did this run
touch the internet?" is answered.
"""

import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Ingestion's own snapshot directory, deliberately not `data/snapshots/` itself.
# That directory already holds four files owned by
# `.claude/scripts/check_data_availability.py`, which rewrites them on its own
# `--refresh`. Two scripts owning one filename with two refresh policies is a
# collision waiting for whichever ran last; a subdirectory costs nothing and
# makes ownership obvious.
SNAPSHOT_DIR = REPO_ROOT / "data" / "snapshots" / "ingestion"

# A descriptive agent with a contact address, for three separate reasons, all of
# them recorded in data-availability.md: Frankfurter returns HTTP 403 to the
# default `Python-urllib` agent, the SEC's fair-access policy requires contact
# details, and anonymous scraping of a source we depend on is rude.
USER_AGENT = "veritas-capstone/0.1 (aminojaghi93@gmail.com)"

REQUEST_TIMEOUT_SECONDS = 30


# Snapshots rewritten by the current `--refresh`, in the order they were written.
#
# A refresh is not transactional: it rewrites the snapshots one file at a time, so
# a source that dies part-way leaves the repository holding some fresh files and
# some stale ones. That mix is a perfectly plausible-looking working tree and is
# exactly the sort of quietly-wrong state this project exists to refuse, so the
# entry point reports this list when a refresh fails. Making the inconsistency
# loud is cheap; making the refresh atomic is not, and would buy
# little — the fix either way is to run `--refresh` again.
REWRITTEN: list[str] = []

# Bytes already read this run, keyed by snapshot name.
#
# **One source is read once per run, whatever asks for it.** Sub-step 2.3 made
# this necessary: `yahoo_instrument` reads the `meta` block of each chart response
# and `yahoo_price` reads the `timestamp` and `indicators` blocks of the same
# response, so without a cache a `--refresh` would fetch every chart twice
# — and the two fetches would not return the same bytes. A chart pulled at 14:32
# and again at 14:33 carries a different last bar and a different
# `regularMarketTime`, so `dim_instrument` and `fct_instrument_price` would be
# built from two different observations of the same Instrument, and only the
# second would still be on disk. The cache is what makes "the snapshot on disk is
# the bytes this run used" stay true once two resources share a file.
_ALREADY_READ: dict[str, bytes] = {}


class SourceUnavailable(RuntimeError):
    """A source could not be read — no snapshot on disk, or a live fetch failed.

    Raised rather than returning empty so that a missing source stops the run.
    A pipeline that quietly loads three sources out of four produces a Warehouse
    that looks fine and is silently short, which is the failure mode this whole
    project is about.
    """


def snapshot_path(name: str) -> Path:
    return SNAPSHOT_DIR / name


def read_source(name: str, url: str, *, refresh: bool) -> bytes:
    """The bytes of one source, from the snapshot or from the network.

    `refresh=False` — the default and the mode a reviewer runs — reads the
    committed snapshot and never opens a socket. `refresh=True` fetches, writes
    the snapshot, and returns what it fetched, so the file on disk and the bytes
    this run used are the same bytes by construction rather than by a later copy.

    Either way the bytes are cached under `name`, so a second caller asking for
    the same source gets the same observation rather than a second one. See
    `_ALREADY_READ`.
    """
    if name in _ALREADY_READ:
        return _ALREADY_READ[name]

    path = snapshot_path(name)

    if not refresh:
        if not path.exists():
            raise SourceUnavailable(
                f"no snapshot at {path.relative_to(REPO_ROOT)} — run "
                f"`uv run python -m veritas.ingestion --refresh` once to create it"
            )
        body = path.read_bytes()
    else:
        body = fetch(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        REWRITTEN.append(name)

    _ALREADY_READ[name] = body
    return body


def fetch(url: str) -> bytes:
    """One live request. The only place in the package that opens a socket."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise SourceUnavailable(f"{url} returned HTTP {error.code}") from error
    except OSError as error:
        # Covers URLError, timeouts and DNS failure — every way a refresh fails
        # when the machine simply has no network, which must not look like a
        # source having died.
        raise SourceUnavailable(f"{url} could not be reached: {error}") from error
