"""Ingestion — the pipeline that fills the Warehouse.

The Glossary registers it as: *"real FX Rates, Market Prices and instrument
reference data from key-free public sources, snapshotted into the repository and
replayed by default; synthetic Trades, Cash Movements and Positions from a seeded
simulator. **Market data real, client activity synthetic — never the reverse.**"*

Built one table per Sub-step, in the order the foreign keys permit:

    2.2  dim_instrument         NASDAQ Trader · SEC · Yahoo metadata   ← here
    2.3  fct_instrument_price   Yahoo, by snapshot-and-replay
    2.4  fct_fx_rate            Frankfurter
    2.5  the synthetic half     a seeded simulator

Run it with `uv run python -m veritas.ingestion`; see `__main__` for the modes.
"""
