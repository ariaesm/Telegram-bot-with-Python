"""Telegram handlers and entry point (python-telegram-bot v21, async).

Run with ``python -m toolbox_bot`` after setting ``TELEGRAM_BOT_TOKEN``.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from zoneinfo import ZoneInfo

from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from .jalali import JalaliDate, gregorian_to_jalali, jalali_to_gregorian, parse_date
from .reminders import ReminderError, humanize_minutes, parse_remind_args
from .textstats import analyze, format_stats

logger = logging.getLogger(__name__)
TEHRAN = ZoneInfo("Asia/Tehran")

COMMANDS = [
    ("start", "Welcome message"),
    ("help", "List all commands"),
    ("today", "Today's date in Jalali and Gregorian"),
    ("tojalali", "Gregorian -> Jalali, e.g. /tojalali 2024-03-20"),
    ("togregorian", "Jalali -> Gregorian, e.g. /togregorian 1403/01/01"),
    ("remind", "Reminder, e.g. /remind 10 stretch or /remind 1h30m call mom"),
    ("reminders", "List your pending reminders"),
    ("cancel", "Cancel all your pending reminders"),
    ("wordcount", "Text stats for the given text or the replied-to message"),
]

HELP_TEXT = "\n".join(f"/{name} - {desc}" for name, desc in COMMANDS)


def _describe(j: JalaliDate, g: dt.date) -> str:
    return (
        f"Jalali: <b>{j}</b> ({j.day} {j.month_name} {j.year})\n"
        f"Gregorian: <b>{g.isoformat()}</b> ({g.strftime('%A, %d %B %Y')})"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.effective_user.first_name if update.effective_user else "there"
    await update.message.reply_text(
        f"Hi {name}! I'm a small toolbox bot.\n\n{HELP_TEXT}",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    g = dt.datetime.now(TEHRAN).date()
    await update.message.reply_text(
        "Today in Tehran:\n" + _describe(gregorian_to_jalali(g), g), parse_mode=ParseMode.HTML
    )


async def to_jalali(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /tojalali YYYY-MM-DD")
        return
    try:
        g = dt.date(*parse_date(context.args[0]))
        j = gregorian_to_jalali(g)
    except ValueError as exc:
        await update.message.reply_text(f"Invalid date: {exc}")
        return
    await update.message.reply_text(_describe(j, g), parse_mode=ParseMode.HTML)


async def to_gregorian(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /togregorian YYYY/MM/DD")
        return
    try:
        y, m, d = parse_date(context.args[0])
        g = jalali_to_gregorian(y, m, d)
    except ValueError as exc:
        await update.message.reply_text(f"Invalid date: {exc}")
        return
    await update.message.reply_text(_describe(JalaliDate(y, m, d), g), parse_mode=ParseMode.HTML)


async def _send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"⏰ Reminder: {job.data}")


def _chat_jobs(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    return context.job_queue.get_jobs_by_name(f"remind-{chat_id}")


async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        reminder = parse_remind_args(context.args or [])
    except ReminderError as exc:
        await update.message.reply_text(str(exc))
        return
    chat_id = update.effective_chat.id
    context.job_queue.run_once(
        _send_reminder,
        when=reminder.seconds,
        chat_id=chat_id,
        name=f"remind-{chat_id}",
        data=reminder.text,
    )
    await update.message.reply_text(
        f"OK, I'll remind you in {humanize_minutes(reminder.minutes)}: {reminder.text}"
    )


async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    jobs = _chat_jobs(context, update.effective_chat.id)
    if not jobs:
        await update.message.reply_text("You have no pending reminders.")
        return
    now = dt.datetime.now(dt.UTC)
    lines = []
    for job in sorted(jobs, key=lambda j: j.next_t):
        left = max(0, round((job.next_t - now).total_seconds() / 60))
        lines.append(f"• in ~{humanize_minutes(left)}: {job.data}")
    await update.message.reply_text("Pending reminders:\n" + "\n".join(lines))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    jobs = _chat_jobs(context, update.effective_chat.id)
    for job in jobs:
        job.schedule_removal()
    await update.message.reply_text(f"Cancelled {len(jobs)} reminder(s).")


async def wordcount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args or [])
    replied = update.message.reply_to_message
    if not text and replied:
        text = replied.text or replied.caption or ""
    if not text:
        await update.message.reply_text(
            "Send /wordcount <text>, or reply to a message with /wordcount."
        )
        return
    await update.message.reply_text(format_stats(analyze(text)))


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands([BotCommand(n, d) for n, d in COMMANDS])


def build_application(token: str) -> Application:
    app = Application.builder().token(token).post_init(_post_init).build()
    handlers = {
        "start": start,
        "help": help_command,
        "today": today,
        "tojalali": to_jalali,
        "togregorian": to_gregorian,
        "remind": remind,
        "reminders": list_reminders,
        "cancel": cancel,
        "wordcount": wordcount,
    }
    for name, callback in handlers.items():
        app.add_handler(CommandHandler(name, callback))
    return app


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN (see .env.example).")
    build_application(token).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
