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
# A refresh is not transactional: it rewrites nineteen files one at a time, so a
# source that dies at the fourteenth leaves the repository holding thirteen new
# snapshots and six old ones. That mix is a perfectly plausible-looking working
# tree and is exactly the sort of quietly-wrong state this project exists to
# refuse, so the entry point reports this list when a refresh fails. Making the
# inconsistency loud is cheap; making the refresh atomic is not, and would buy
# little — the fix either way is to run `--refresh` again.
REWRITTEN: list[str] = []


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
    """
    path = snapshot_path(name)

    if not refresh:
        if not path.exists():
            raise SourceUnavailable(
                f"no snapshot at {path.relative_to(REPO_ROOT)} — run "
                f"`uv run python -m veritas.ingestion --refresh` once to create it"
            )
        return path.read_bytes()

    body = fetch(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    REWRITTEN.append(name)
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
