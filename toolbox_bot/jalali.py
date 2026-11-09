"""Pure-Python Jalali (Persian / Solar Hijri) <-> Gregorian calendar conversion.

The algorithm is the arithmetic one by Kazimierz M. Borkowski, as popularised by
the ``jalaali-js`` project. It uses the table of "break" years of the 2820-year
grand cycle and is valid for Jalali years -61 .. 3177 (Gregorian 560 .. 3798).

No third-party dependencies: Gregorian <-> day-number uses :mod:`datetime`
ordinals, so this module is safe to import anywhere (including tests).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

__all__ = [
    "JalaliDate",
    "MONTH_NAMES",
    "gregorian_to_jalali",
    "is_leap_jalali_year",
    "jalali_month_length",
    "jalali_to_gregorian",
    "parse_date",
]

MONTH_NAMES = (
    "Farvardin",
    "Ordibehesht",
    "Khordad",
    "Tir",
    "Mordad",
    "Shahrivar",
    "Mehr",
    "Aban",
    "Azar",
    "Dey",
    "Bahman",
    "Esfand",
)

_BREAKS = (
    -61,
    9,
    38,
    199,
    426,
    686,
    756,
    818,
    1111,
    1181,
    1210,
    1635,
    2060,
    2097,
    2192,
    2262,
    2324,
    2394,
    2456,
    3178,
)


def _div(a: int, b: int) -> int:
    """Integer division truncating toward zero (like C / JavaScript ``~~(a / b)``)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _mod(a: int, b: int) -> int:
    """Remainder matching :func:`_div` (sign follows the dividend)."""
    return a - _div(a, b) * b


@dataclass(frozen=True, order=True)
class JalaliDate:
    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"month must be 1..12, got {self.month}")
        max_day = jalali_month_length(self.year, self.month)
        if not 1 <= self.day <= max_day:
            raise ValueError(f"day must be 1..{max_day} for {self.year}/{self.month}")

    @property
    def month_name(self) -> str:
        return MONTH_NAMES[self.month - 1]

    def to_gregorian(self) -> _dt.date:
        return jalali_to_gregorian(self.year, self.month, self.day)

    @classmethod
    def from_gregorian(cls, date: _dt.date) -> JalaliDate:
        return gregorian_to_jalali(date)

    def __str__(self) -> str:
        return f"{self.year:04d}/{self.month:02d}/{self.day:02d}"


def _jal_cal(jy: int) -> tuple[int, int, int]:
    """Return ``(leap, gy, march)`` for Jalali year ``jy``.

    ``leap`` is 0 for a leap year (years since last leap year), ``gy`` is the
    Gregorian year in which the Jalali year starts and ``march`` is the March day
    of Nowruz (1 Farvardin).
    """
    if jy < _BREAKS[0] or jy >= _BREAKS[-1]:
        raise ValueError(f"Jalali year {jy} is out of the supported range")
    gy = jy + 621
    leap_j = -14
    jp = _BREAKS[0]
    jump = 0
    for jm in _BREAKS[1:]:
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm
    n = jy - jp
    leap_j += _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, gy, march


def is_leap_jalali_year(year: int) -> bool:
    """True if Jalali ``year`` has 366 days (Esfand has 30 days)."""
    return _jal_cal(year)[0] == 0


def jalali_month_length(year: int, month: int) -> int:
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1..12, got {month}")
    if month <= 6:
        return 31
    if month <= 11:
        return 30
    return 30 if is_leap_jalali_year(year) else 29


def jalali_to_gregorian(year: int, month: int, day: int) -> _dt.date:
    """Convert a Jalali date to a :class:`datetime.date`."""
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1..12, got {month}")
    max_day = jalali_month_length(year, month)
    if not 1 <= day <= max_day:
        raise ValueError(f"day must be 1..{max_day} for {year}/{month}")
    _, gy, march = _jal_cal(year)
    nowruz = _dt.date(gy, 3, march)
    offset = (month - 1) * 31 - (month // 7) * (month - 7) + day - 1
    return nowruz + _dt.timedelta(days=offset)


def gregorian_to_jalali(date: _dt.date) -> JalaliDate:
    """Convert a :class:`datetime.date` to a :class:`JalaliDate`."""
    jy = date.year - 621
    leap, gy, march = _jal_cal(jy)
    k = (date - _dt.date(gy, 3, march)).days
    if k >= 0:
        if k <= 185:
            return JalaliDate(jy, 1 + k // 31, k % 31 + 1)
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    return JalaliDate(jy, 7 + k // 30, k % 30 + 1)


def parse_date(text: str) -> tuple[int, int, int]:
    """Parse ``YYYY-MM-DD`` or ``YYYY/MM/DD`` (Persian/Arabic digits allowed)."""
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    cleaned = text.strip().translate(table).replace("/", "-")
    parts = cleaned.split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"expected YYYY-MM-DD or YYYY/MM/DD, got {text!r}")
    y, m, d = (int(p) for p in parts)
    return y, m, d
