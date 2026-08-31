"""Parsing of portfolio CSV / brokerage-export files (US-2, FR-2, FR-3).

Real brokerage exports are not clean CSVs. This module is deliberately forgiving about
their well-known quirks and strict about the two values we actually need — a ticker and a
share quantity — reporting anything it cannot use rather than silently dropping it.

What it copes with, and why:

* **Preamble lines.** Schwab-style exports open with a title row
  (``"Positions for account ...as of 08/30/2026"``) before the real header. We scan for the
  first row that looks like a header instead of assuming row 1.
* **Varied header names.** ``Symbol`` / ``Ticker`` / ``Investment Name``; ``Quantity`` /
  ``Shares`` / ``Qty``. Matched case- and punctuation-insensitively.
* **Formatted numbers.** ``"1,234.567"``, ``$1,234``, ``(50)`` for negatives, trailing ``%``.
* **Footer rows.** ``Account Total``, ``Cash & Cash Investments``, ``Pending Activity``, and
  the free-text disclaimer paragraphs Fidelity appends after a blank line.
* **Cash and money-market lines.** Reported as skipped rather than as errors: they are
  legitimate rows that simply are not tradable positions.
* **A UTF-8 BOM**, CRLF line endings, and quoted fields containing commas.

The parser is pure: no database, no network. It turns bytes into rows plus problems, and
the API layer decides what to persist.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

#: Header aliases for the ticker column, **in preference order**. Order matters: a Vanguard
#: export has both "Investment Name" and "Symbol", and only the latter holds a ticker, so an
#: unambiguous symbol header must win over a descriptive name header.
_TICKER_HEADERS: tuple[frozenset[str], ...] = (
    frozenset({"symbol", "ticker", "tickersymbol", "symbolcusip", "securitysymbol"}),
    frozenset({"security", "securityid", "investment", "investmentname", "fund", "holding"}),
)

#: Header aliases for the share-quantity column, in preference order. "Quantity"/"Shares"
#: beat looser matches like "Units".
_QUANTITY_HEADERS: tuple[frozenset[str], ...] = (
    frozenset({"quantity", "qty", "shares", "sharesheld", "sharequantity"}),
    frozenset({"quantityshares", "noofshares", "numberofshares", "units"}),
)

#: Row labels that are structural rather than positions. Matched on the ticker cell.
_NON_POSITION_LABELS = frozenset(
    {
        "accounttotal",
        "total",
        "totals",
        "grandtotal",
        "subtotal",
        "cash",
        "cashcashinvestments",
        "cashandcashinvestments",
        "cashequivalents",
        "moneymarket",
        "pendingactivity",
        "accountsummary",
    }
)

#: Symbols that represent cash rather than a tradable position.
_CASH_SYMBOLS = frozenset({"cash", "usd", "spaxx", "fdrxx", "swvxx", "vmfxx", "fzfxx"})

#: A plausible ticker: 1-6 letters, optionally with a class suffix (BRK.B / BRK-B).
_TICKER_RE = re.compile(r"^[A-Za-z]{1,6}([.\-][A-Za-z]{1,2})?$")

_MAX_ROWS = 5000


def _normalize_header(value: str) -> str:
    """Lowercase and strip everything but letters/digits, so 'Share Price' -> 'shareprice'."""
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def _clean_number(raw: str) -> Decimal | None:
    """Parse a brokerage-formatted number, or ``None`` if it isn't one.

    Handles currency symbols, thousands separators, a trailing percent sign, and
    accounting-style negatives written as ``(1,234)``.
    """
    text = raw.strip()
    if not text:
        return None

    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]

    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        return None

    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    return -value if negative else value


@dataclass(frozen=True, slots=True)
class ParsedHolding:
    """A row we can use."""

    ticker: str
    quantity: Decimal
    row_number: int


@dataclass(frozen=True, slots=True)
class RowProblem:
    """A row we could not use, and why — surfaced to the user (FR-3)."""

    row_number: int
    reason: str
    #: The offending content, trimmed, so the user can find the line in their file.
    content: str


@dataclass
class ParseResult:
    holdings: list[ParsedHolding] = field(default_factory=list)
    problems: list[RowProblem] = field(default_factory=list)
    #: Rows intentionally ignored (cash lines, totals, disclaimers) — not errors.
    skipped: int = 0
    #: Which columns the header scan settled on, for transparency in the response.
    ticker_column: str | None = None
    quantity_column: str | None = None


def _decode(data: bytes) -> str:
    """Decode upload bytes, tolerating a BOM and non-UTF-8 brokerage encodings."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _find_header(rows: list[list[str]]) -> tuple[int, int, int, str, str] | None:
    """Locate the header row and the ticker/quantity column indexes.

    Returns ``(row_index, ticker_index, quantity_index, ticker_name, quantity_name)``, or
    ``None`` when no row in the file looks like a usable header. Scanning (rather than
    assuming row 0) is what lets us read exports that open with a title line.
    """

    def best_match(normalized: list[str], tiers: tuple[frozenset[str], ...]) -> int | None:
        """First column matching the most preferred tier that appears at all."""
        for tier in tiers:
            match = next((i for i, cell in enumerate(normalized) if cell in tier), None)
            if match is not None:
                return match
        return None

    for index, row in enumerate(rows[:25]):  # headers live near the top in every real export
        normalized = [_normalize_header(cell) for cell in row]
        ticker_index = best_match(normalized, _TICKER_HEADERS)
        quantity_index = best_match(normalized, _QUANTITY_HEADERS)
        if ticker_index is not None and quantity_index is not None:
            return (
                index,
                ticker_index,
                quantity_index,
                row[ticker_index].strip(),
                row[quantity_index].strip(),
            )
    return None


def parse_portfolio_csv(data: bytes) -> ParseResult:
    """Parse an uploaded CSV into holdings plus a report of what could not be used."""
    text = _decode(data)
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        return ParseResult(problems=[RowProblem(0, f"Could not read the file: {exc}", "")])

    if not rows:
        return ParseResult(problems=[RowProblem(0, "The file is empty.", "")])

    header = _find_header(rows)
    if header is None:
        return ParseResult(
            problems=[
                RowProblem(
                    0,
                    "Could not find a ticker column and a share-quantity column. Expected "
                    "headers like 'Symbol' and 'Quantity'.",
                    "",
                )
            ]
        )

    header_index, ticker_index, quantity_index, ticker_name, quantity_name = header
    result = ParseResult(ticker_column=ticker_name, quantity_column=quantity_name)
    seen: dict[str, int] = {}

    for offset, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if offset - header_index > _MAX_ROWS:
            result.problems.append(RowProblem(offset, f"Stopped after {_MAX_ROWS} rows.", ""))
            break

        # Blank line, or a trailing disclaimer paragraph that isn't really a CSV row.
        if not any(cell.strip() for cell in row):
            result.skipped += 1
            continue
        if len(row) <= max(ticker_index, quantity_index):
            result.skipped += 1
            continue

        raw_ticker = row[ticker_index].strip()
        raw_quantity = row[quantity_index].strip()

        if not raw_ticker:
            result.skipped += 1
            continue

        normalized_ticker = _normalize_header(raw_ticker)
        if normalized_ticker in _NON_POSITION_LABELS or normalized_ticker in _CASH_SYMBOLS:
            result.skipped += 1
            continue

        # Fidelity marks money-market funds with trailing asterisks.
        candidate = raw_ticker.rstrip("*").strip().upper()
        if _normalize_header(candidate) in _CASH_SYMBOLS:
            result.skipped += 1
            continue

        if not _TICKER_RE.match(candidate):
            result.problems.append(
                RowProblem(offset, f"'{raw_ticker}' is not a valid ticker symbol.", raw_ticker)
            )
            continue

        quantity = _clean_number(raw_quantity)
        if quantity is None:
            result.problems.append(
                RowProblem(
                    offset,
                    f"Could not read a share quantity from '{raw_quantity}'."
                    if raw_quantity
                    else "Missing share quantity.",
                    raw_quantity,
                )
            )
            continue
        if quantity <= 0:
            result.problems.append(
                RowProblem(
                    offset, f"Share quantity must be positive (got {quantity}).", raw_quantity
                )
            )
            continue

        symbol = candidate.upper()
        if symbol in seen:
            # Same symbol twice (e.g. held across two accounts in one export): combine.
            existing = result.holdings[seen[symbol]]
            result.holdings[seen[symbol]] = ParsedHolding(
                symbol, existing.quantity + quantity, existing.row_number
            )
            continue

        seen[symbol] = len(result.holdings)
        result.holdings.append(ParsedHolding(symbol, quantity, offset))

    return result
