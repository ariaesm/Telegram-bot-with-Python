"""Argument parsing for ``/remind`` (kept free of telegram imports for testing)."""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_MINUTES = 7 * 24 * 60  # one week
_DURATION_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m?)?$", re.IGNORECASE)


@dataclass(frozen=True)
class Reminder:
    minutes: int
    text: str

    @property
    def seconds(self) -> int:
        return self.minutes * 60


class ReminderError(ValueError):
    """Raised with a user-facing message when /remind arguments are invalid."""


def parse_duration(token: str) -> int:
    """Parse ``"15"``, ``"15m"``, ``"2h"`` or ``"1h30m"`` into minutes."""
    match = _DURATION_RE.match(token.strip())
    if not token.strip() or not match or not any(match.groups()):
        raise ReminderError(f"Can't understand duration {token!r}. Try 10, 10m, 2h or 1h30m.")
    hours, minutes = (int(g) if g else 0 for g in match.groups())
    return hours * 60 + minutes


def parse_remind_args(args: list[str]) -> Reminder:
    """Turn ``["10", "drink", "water"]`` into ``Reminder(10, "drink water")``."""
    if len(args) < 2:
        raise ReminderError("Usage: /remind <minutes> <text>, e.g. /remind 10 stretch")
    minutes = parse_duration(args[0])
    if minutes <= 0:
        raise ReminderError("Duration must be at least 1 minute.")
    if minutes > MAX_MINUTES:
        raise ReminderError(f"Duration can be at most {MAX_MINUTES} minutes (one week).")
    text = " ".join(args[1:]).strip()
    return Reminder(minutes=minutes, text=text)


def humanize_minutes(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if mins or not parts:
        parts.append(f"{mins} minute{'s' if mins != 1 else ''}")
    return " ".join(parts)
