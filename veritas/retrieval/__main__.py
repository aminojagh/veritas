"""Retrieval's entry point — put both models on disk and prove they load.

    uv run python -m veritas.retrieval

Fetches `EMBEDDING_MODEL` and `RERANKER_MODEL` into the directory fastembed's own
`FASTEMBED_CACHE_PATH` names, then uses each one once — so what this checks is that
the weights load, not that some files are present. `Dockerfile` runs it at image
build, which is why it names neither model: the two constants in `search.py` stay
the one place either is written.

Exit status is what a build reads: 0 with both models loaded, 1 with the sentence
saying which one was not.
"""

import os
from pathlib import Path

from fastembed.common.utils import define_cache_dir

from veritas.retrieval.search import (
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    embedding_model,
    reranker,
)

# The variable fastembed reads to decide where a model is cached. `define_cache_dir`
# is fastembed's own reader of it, so the directory reported below is the directory
# the models were actually written to rather than this file's guess at it.
CACHE_VARIABLE = "FASTEMBED_CACHE_PATH"

# One short question, embedded and then re-scored against itself. Its wording does not
# matter — what matters is that both ONNX sessions run.
PROBE = "what was our net revenue"


def held(cache: Path) -> tuple[int, int]:
    """How many files the cache holds, and how many bytes they come to.

    Symbolic links are skipped rather than followed. A Hugging Face cache keeps each
    file once under `blobs/` and links to it from every snapshot that uses it, so
    following the links reports a directory twice the size of the one an image
    carries.
    """
    files = [
        path for path in cache.rglob("*") if path.is_file() and not path.is_symlink()
    ]
    return len(files), sum(path.stat().st_size for path in files)


def main() -> int:
    cache = define_cache_dir()
    print(f"  {CACHE_VARIABLE}: {os.environ.get(CACHE_VARIABLE) or 'unset'}")
    print(f"  cache directory: {cache}")

    try:
        [vector] = embedding_model().embed([PROBE])
        print(f"  {EMBEDDING_MODEL:<32} embeds in {len(vector)} dimensions")
        [score] = reranker().rerank(PROBE, [PROBE])
        print(f"  {RERANKER_MODEL:<32} scores a pair at {score:.3f}")
    except Exception as unavailable:
        print(
            f"\nFAIL — a Retrieval model would not load: {unavailable}\n"
            f"       both are fetched from the Hugging Face hub on first use, so a "
            f"first run needs a network and later ones do not"
        )
        return 1

    files, size = held(cache)
    print(
        f"\nPASS — both Retrieval models load from {cache} · "
        f"{files} files, {size / 1024 ** 2:.1f} MiB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
