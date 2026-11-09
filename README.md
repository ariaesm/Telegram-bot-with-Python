# Toolbox Telegram Bot

A small, practical Telegram bot written in Python with
[python-telegram-bot](https://python-telegram-bot.org/) v21 (fully async).
It bundles a few everyday utilities, with a focus on Persian users:

- **Jalali (Persian / Solar Hijri) ⇄ Gregorian date conversion** - the conversion
  algorithm is implemented from scratch in a pure module (`toolbox_bot/jalali.py`), no
  third-party calendar library.
- **Reminders** - `/remind 10 stretch` or `/remind 1h30m call mom`, scheduled with
  PTB's `JobQueue`.
- **Text statistics** - `/wordcount` on any text or on a message you reply to
  (Unicode-aware, so Persian text works too).

The business logic lives in plain Python modules that never import `telegram`, so they are
fully unit-tested; `bot.py` is a thin layer of handlers on top.

## Commands

| Command | Example | What it does |
| --- | --- | --- |
| `/start` | | Welcome message + command list |
| `/help` | | Command list |
| `/today` | | Today's date (Tehran time) in both calendars |
| `/tojalali` | `/tojalali 2024-03-20` | Gregorian → Jalali |
| `/togregorian` | `/togregorian 1403/01/01` | Jalali → Gregorian (Persian digits accepted: `۱۴۰۳/۰۱/۰۱`) |
| `/remind` | `/remind 1h30m call mom` | One-off reminder (`10`, `10m`, `2h`, `1h30m`; max one week) |
| `/reminders` | | List pending reminders in this chat |
| `/cancel` | | Cancel all pending reminders in this chat |
| `/wordcount` | `/wordcount some text` | Words, characters, sentences, reading time, top words |

## Project layout

```
toolbox_bot/
  jalali.py      # pure Jalali <-> Gregorian conversion (Borkowski / jalaali-js algorithm)
  reminders.py   # /remind argument parsing and formatting
  textstats.py   # /wordcount statistics
  bot.py         # telegram handlers + Application setup
  __main__.py    # `python -m toolbox_bot`
tests/           # pytest tests for the pure modules
```

## Installation

Requires Python 3.11+ (CI runs 3.12).

```bash
git clone https://github.com/ariaesm/telegram-bot-with-python.git
cd telegram-bot-with-python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Running the bot

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Provide it via the `TELEGRAM_BOT_TOKEN` environment variable:

```bash
cp .env.example .env          # then edit .env
export $(grep -v '^#' .env | xargs)
python -m toolbox_bot
```

Or with Docker:

```bash
docker build -t toolbox-bot .
docker run --rm --env-file .env toolbox-bot
```

Note: reminders live in memory (PTB `JobQueue`), so they are lost when the bot restarts.

## Using the pure modules

The logic modules can be used on their own. This is real output from running them:

```python
>>> import datetime as dt
>>> from toolbox_bot.jalali import gregorian_to_jalali, jalali_to_gregorian
>>> j = gregorian_to_jalali(dt.date(2024, 3, 20)); print(j, j.month_name)
1403/01/01 Farvardin
>>> print(jalali_to_gregorian(1404, 1, 1))
2025-03-21
```

```python
>>> from toolbox_bot.textstats import analyze, format_stats
>>> print(format_stats(analyze("The quick brown fox jumps over the lazy dog. The dog sleeps!")))
Words: 12 (9 unique)
Characters: 60 (49 without spaces)
Sentences: 2
Lines: 1
Reading time: ~4s at 200 wpm
Top words: the ×3, dog ×2, brown ×1
```

```python
>>> from toolbox_bot.reminders import parse_remind_args, humanize_minutes
>>> r = parse_remind_args(["1h30m", "call", "mom"]); print(r, humanize_minutes(r.minutes))
Reminder(minutes=90, text='call mom') 1 hour 30 minutes
```

## How the Jalali conversion works

The Jalali calendar is solar: Nowruz (1 Farvardin) falls on the March equinox. Instead
of astronomical calculation, `jalali.py` uses Kazimierz Borkowski's arithmetic method (the
same one used by `jalaali-js`): a table of "break" years splits history into segments
following 33-year leap cycles, from which the March day of Nowruz and the leap status of
each year are computed. Months 1-6 have 31 days, 7-11 have 30, and Esfand has 29 (30 in
leap years). Valid for Jalali years -61 to 3177.

The tests check known dates (e.g. 1403/01/01 = 2024-03-20, 1357/11/22 = 1979-02-11) and
round-trip every single day from 1950 to 2059.

## Tests

```bash
python -m pytest -q
```

The tests only import the pure modules, so they run without `python-telegram-bot`
installed. CI (GitHub Actions) runs `ruff` and `pytest` on Python 3.12.

## License

MIT - see [LICENSE](LICENSE).
