FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "python-telegram-bot[job-queue]>=21,<22"
COPY toolbox_bot ./toolbox_bot
RUN useradd --create-home bot
USER bot
CMD ["python", "-m", "toolbox_bot"]
