import datetime as dt

import pytest

from toolbox_bot.jalali import (
    JalaliDate,
    gregorian_to_jalali,
    is_leap_jalali_year,
    jalali_month_length,
    jalali_to_gregorian,
    parse_date,
)


@pytest.mark.parametrize(
    ("jalali", "gregorian"),
    [
        ((1403, 1, 1), dt.date(2024, 3, 20)),  # Nowruz 1403
        ((1404, 1, 1), dt.date(2025, 3, 21)),  # Nowruz 1404
        ((1357, 11, 22), dt.date(1979, 2, 11)),
        ((1399, 12, 30), dt.date(2021, 3, 20)),  # last day of leap year 1399
        ((1403, 12, 30), dt.date(2025, 3, 20)),  # last day of leap year 1403
        ((1400, 7, 1), dt.date(2021, 9, 23)),
        ((1, 1, 1), dt.date(622, 3, 22)),
    ],
)
def test_known_dates(jalali, gregorian):
    assert jalali_to_gregorian(*jalali) == gregorian
    assert gregorian_to_jalali(gregorian) == JalaliDate(*jalali)


def test_round_trip_every_day_over_a_century():
    day = dt.date(1950, 1, 1)
    previous = gregorian_to_jalali(day - dt.timedelta(days=1))
    while day < dt.date(2060, 1, 1):
        j = gregorian_to_jalali(day)
        assert j > previous  # strictly increasing, no gaps or repeats
        assert j.to_gregorian() == day
        previous = j
        day += dt.timedelta(days=1)


@pytest.mark.parametrize(
    ("year", "leap"), [(1399, True), (1400, False), (1403, True), (1404, False)]
)
def test_leap_years(year, leap):
    assert is_leap_jalali_year(year) is leap
    assert jalali_month_length(year, 12) == (30 if leap else 29)


def test_month_lengths():
    assert [jalali_month_length(1402, m) for m in range(1, 12)] == [31] * 6 + [30] * 5


@pytest.mark.parametrize("bad", [(1402, 12, 30), (1403, 13, 1), (1403, 7, 31), (1403, 1, 0)])
def test_invalid_dates_rejected(bad):
    with pytest.raises(ValueError):
        jalali_to_gregorian(*bad)


def test_str_and_month_name():
    j = JalaliDate(1403, 2, 5)
    assert str(j) == "1403/02/05"
    assert j.month_name == "Ordibehesht"


@pytest.mark.parametrize(
    ("text", "expected"),
    [("1403/01/01", (1403, 1, 1)), ("2024-03-20", (2024, 3, 20)), ("۱۴۰۳/۰۱/۰۱", (1403, 1, 1))],
)
def test_parse_date(text, expected):
    assert parse_date(text) == expected


@pytest.mark.parametrize("text", ["", "1403/01", "abc", "2024-03-xx"])
def test_parse_date_errors(text):
    with pytest.raises(ValueError):
        parse_date(text)
