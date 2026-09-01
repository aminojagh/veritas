"""The App — the page a person asks a question on, and reads a Grounded Answer from.

Laid out like the other components: this file re-exports, `render.py` turns a Grounded
Answer into the strings a reader sees, and `page.py` is the Streamlit script that places
them and is the only module in the repository permitted to import `streamlit`.
"""

from veritas.app.render import (
    ENFORCEMENT_NOTE,
    NOTHING,
    formatted,
    identity_lines,
    labels,
    lineage_lines,
    model_line,
    outcome_line,
    single_value,
    table,
)

__all__ = [
    "ENFORCEMENT_NOTE",
    "NOTHING",
    "formatted",
    "identity_lines",
    "labels",
    "lineage_lines",
    "model_line",
    "outcome_line",
    "single_value",
    "table",
]
