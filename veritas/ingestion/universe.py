"""The traded Instrument universe, and the two vocabulary maps ingestion needs.

Three constants, all of them decisions rather than data. Each is here — in one
place, in Python — rather than inline in SQL, because Sub-step 2.3 needs two of
them again and a mapping that lives in two files is a mapping that will disagree
with itself.

`data-availability.md` fixes the shape of the universe: *"The traded Instrument
universe is equity, ETF, future and currency pair (R1). Bond exposure is via bond
ETFs."* What it does not fix is which symbols, which is what this file decides.
"""

# The traded Instrument universe. Sixteen symbols, chosen so that every axis a
# later Sub-step has to distinguish is actually present in the data rather than
# asserted in a document:
#
#   * all four instrument_type values the Instrument term permits, because a
#     Dimension Definition that no row exercises proves nothing;
#   * four Quotation Currencies — USD, EUR, GBp and JPY — all of which
#     Frankfurter publishes against EUR, so every Position can reach the
#     Reporting Currency through a real FX Rate rather than a gap;
#   * two GBp listings rather than one, so the 100x trap is a class of row and
#     not a single special case someone could hardcode past;
#   * the EU, UK and APAC regions the region Dimension Definition names, so
#     Sub-step 2.5 can site its Clients somewhere real;
#   * **at least two Instruments of every type**, which is the bar
#     `check_warehouse.py --sources` now asserts. One is indistinguishable from a
#     special case: a metric sliced to a type with a single member returns that
#     one security's numbers, so the slice proves nothing about the type and
#     Sub-step 2.5 cannot build a distinction on it. The first version of this
#     universe held one currency pair and failed that check, which is what added
#     the second and third.
#
# Bond exposure is TLT and BNDX rather than single bonds: DEBT-003 records that no
# key-free Market Price source sells individual bonds, so bond ETFs are how a bond
# question gets a real number here.
TRADED_INSTRUMENTS = (
    # US equity (USD)
    "AAPL",
    "MSFT",
    "JNJ",
    # US exchange-traded funds (USD) — the last two carry the bond exposure
    "SPY",
    "TLT",
    "BNDX",
    # EU equity and exchange-traded fund (EUR)
    "SAP.DE",
    "ASML.AS",
    "IWDA.AS",
    # UK equity — quoted in pence, which is the whole point of including them
    "VOD.L",
    "HSBA.L",
    # APAC equity (JPY)
    "7203.T",
    "6758.T",
    # Futures (USD)
    "ES=F",
    "GC=F",
    "CL=F",
    # Currency pairs — one per non-EUR currency the book is quoted in, so a
    # question about currency-pair exposure is never a question about one pair.
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
)

# Quotation Currency codes that are a minor unit, mapped to the major unit they
# normalise to and the factor between them.
#
# The Glossary registers this as part of `Quotation Currency`: *"The currency
# **and minor unit** an Instrument's Market Price is quoted in — LSE quotes in
# pence (`GBp`), not pounds. Normalising to major units is a required ingestion
# step."*
#
# Sub-step 2.2 uses only the code half: `dim_instrument.quotation_currency`
# records GBP, never GBp, and the schema's CHECK refuses the row otherwise.
# Sub-step 2.3 uses the factor, because a price in pence divided by nothing is
# the 100x error this project exists to prevent.
#
# Known limit, inherited from the schema comment and not fixed here: the engine's
# CHECK catches `GBp` because it is not equal to its own upper case, and does
# **not** catch the `GBX` spelling, which is. This map is what covers the general
# case, so a new minor unit is one line here rather than a new constraint.
MINOR_UNIT_CURRENCIES = {
    "GBp": {"major_unit_currency": "GBP", "minor_units_per_major": 100},
}

# Yahoo's `instrumentType` vocabulary, mapped to the four values the Instrument
# term permits and `dim_instrument`'s CHECK enforces. The left side is the
# source's word and the right side is ours; keeping the translation in one table
# is what stops a source rename from silently becoming a domain rename.
YAHOO_INSTRUMENT_TYPES = {
    "EQUITY": "equity",
    "ETF": "ETF",
    "FUTURE": "future",
    "CURRENCY": "currency pair",
}
