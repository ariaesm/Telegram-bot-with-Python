import pytest

from toolbox_bot.reminders import (
    MAX_MINUTES,
    Reminder,
    ReminderError,
    humanize_minutes,
    parse_duration,
    parse_remind_args,
)


@pytest.mark.parametrize(
    ("token", "minutes"), [("10", 10), ("10m", 10), ("2h", 120), ("1h30m", 90), ("1H5", 65)]
)
def test_parse_duration(token, minutes):
    assert parse_duration(token) == minutes


@pytest.mark.parametrize("token", ["", "abc", "m", "-5", "1.5"])
def test_parse_duration_invalid(token):
    with pytest.raises(ReminderError):
        parse_duration(token)


def test_parse_args():
    r = parse_remind_args(["15", "drink", "water"])
    assert r == Reminder(15, "drink water")
    assert r.seconds == 900


@pytest.mark.parametrize("args", [[], ["10"], ["0", "x"], [str(MAX_MINUTES + 1), "x"]])
def test_parse_args_invalid(args):
    with pytest.raises(ReminderError):
        parse_remind_args(args)


@pytest.mark.parametrize(
    ("m", "text"),
    [
        (1, "1 minute"),
        (5, "5 minutes"),
        (60, "1 hour"),
        (125, "2 hours 5 minutes"),
        (0, "0 minutes"),
    ],
)
def test_humanize(m, text):
    assert humanize_minutes(m) == text
