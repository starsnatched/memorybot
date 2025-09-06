import logging
import os
import re
import sys
import contextvars


_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.request_id = _request_id.get()
        except Exception:
            record.request_id = "-"
        return True


class RedactingFormatter(logging.Formatter):
    _token_re = re.compile(r"[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{20,}")

    def __init__(self, fmt: str, datefmt: str | None = None):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._secrets: list[str] = []
        tok = os.getenv("DISCORD_TOKEN", "")
        if tok:
            self._secrets.append(tok)

    def _redact(self, text: str) -> str:
        s = text
        for secret in self._secrets:
            if secret:
                s = s.replace(secret, "[REDACTED]")
        s = self._token_re.sub("[REDACTED]", s)
        return s

    def format(self, record: logging.LogRecord) -> str:
        try:
            if not hasattr(record, "request_id"):
                record.request_id = "-"
        except Exception:
            pass
        rendered = super().format(record)
        return self._redact(rendered)


def set_request_id(value: str) -> contextvars.Token[str]:
    return _request_id.set(value)


def reset_request_id(token: contextvars.Token[str]) -> None:
    _request_id.reset(token)


def configure_logging(level: str | int = "INFO", fmt: str | None = None, datefmt: str | None = None) -> None:
    log_level = level if isinstance(level, int) else getattr(logging, str(level).upper(), logging.INFO)
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    fmt_value = fmt or os.getenv(
        "LOG_FORMAT",
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(request_id)s | %(message)s",
    )
    datefmt_value = datefmt or os.getenv("LOG_DATEFMT", "%Y-%m-%d %H:%M:%S")
    formatter = RedactingFormatter(fmt=fmt_value, datefmt=datefmt_value)
    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())
    root.addHandler(handler)
    root.setLevel(log_level)
    lib_level = logging.DEBUG if log_level <= logging.DEBUG else logging.WARNING
    for name in ("discord", "discord.http"):
        logging.getLogger(name).setLevel(lib_level)
