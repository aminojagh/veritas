"""Every relative link resolves, file and anchor, in the documents and in the code."""

import re
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)|<img [^>]*src=\"([^\"]+)\"")
FENCE = re.compile(r"^\s*(?:```|~~~)")


def heading_anchors(text: str) -> set[str]:
    """The anchors a markdown renderer generates for a document's headings.

    Lowercase, drop every character that is not a word character, space or hyphen,
    turn spaces into hyphens, and suffix a repeat with `-1`, `-2`. `\\w` keeps
    underscores, and a `#` line inside a fenced block is not a heading.
    """
    anchors: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not line.startswith("#"):
            continue
        slug = re.sub(r"[^\w\s-]", "", line.lstrip("#").strip().lower())
        slug = slug.strip().replace(" ", "-")
        base, repeat = slug, 0
        while slug in anchors:
            repeat += 1
            slug = f"{base}-{repeat}"
        anchors.add(slug)
    return anchors


def sources(root: Path) -> list[Path]:
    """The documents, the skills, and the code that cites them."""
    documents = [
        *(root / ".claude" / "docs").rglob("*.md"),
        *(root / ".claude" / "skills").rglob("*.md"),
        *(root / "docs").rglob("*.md"),
        root / "CLAUDE.md",
        root / "README.md",
    ]
    code = [
        path
        for directory in ("veritas", ".claude/scripts", "tests")
        for path in (root / directory).rglob("*.py")
        if "__pycache__" not in path.parts
    ]
    return sorted(documents) + sorted(code)


def test_every_relative_link_resolves(root):
    anchors: dict[Path, set[str]] = {}
    problems: list[str] = []
    links = 0
    for source in sources(root):
        for match in LINK.finditer(source.read_text()):
            target = match.group(1) or match.group(2)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            links += 1
            relative, _, fragment = target.partition("#")
            path = (source.parent / relative).resolve() if relative else source
            where = source.relative_to(root)
            if not path.exists():
                problems.append(f"{where}: dead link -> {target}")
            elif fragment and path.suffix == ".md":
                if path not in anchors:
                    anchors[path] = heading_anchors(path.read_text())
                if fragment not in anchors[path]:
                    problems.append(f"{where}: dead anchor -> {target}")
    assert links, "no relative links found — the pattern has rotted"
    assert not problems, "\n".join(problems)
