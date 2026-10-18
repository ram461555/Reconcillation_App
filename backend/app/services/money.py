"""Money helpers: convert between rupee strings/Decimals and integer paise.

Amounts are never compared as float — see Docs/DEVELOPMENT_PLAN.md Section 1.1 #5
for why (IEEE-754 binary floats cannot exactly represent decimal fractions like
0.01, which breaks the tolerance-inclusivity rule in Appendix C).
"""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

_THOUSANDS_RE = re.compile(r"[,\s]")


def parse_amount_to_paise(raw: str) -> int:
    """Parse a currency string (Indian or standard grouping) into integer paise.

    Examples: "1,25,000.00" -> 12500000 ; "42,300.00" -> 4230000 ; "17.70" -> 1770
    """
    cleaned = _THOUSANDS_RE.sub("", raw).strip()
    cleaned = cleaned.replace("Rs.", "").replace("INR", "").replace("\u20b9", "").strip()
    value = Decimal(cleaned)
    paise = (value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(paise)


def paise_to_rupees(paise: int | None) -> Decimal | None:
    if paise is None:
        return None
    return (Decimal(paise) / 100).quantize(Decimal("0.01"))


def format_rupees(paise: int | None) -> str:
    if paise is None:
        return ""
    value = paise_to_rupees(paise)
    sign = "-" if value < 0 else ""
    value = abs(value)
    integer_part, _, decimal_part = f"{value:.2f}".partition(".")
    # Indian digit grouping: last 3 digits, then groups of 2
    if len(integer_part) > 3:
        last3 = integer_part[-3:]
        rest = integer_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        integer_part = ",".join(groups) + "," + last3
    return f"{sign}{integer_part}.{decimal_part}"
