"""Data-access layer: market-data / EDGAR clients, caching, and symbol lookup.

Kept separate from the API layer and the engines. For now it only holds a stopgap symbol
validator (:mod:`app.data.symbols`); US-4 replaces it with a real market-data client plus
local caching.
"""
