import logging
import os

import structlog


def get_logger(
    name: str, level: str = os.getenv("LOG_LEVEL", "INFO")
) -> structlog.stdlib.BoundLogger:
    """
    Configures and returns a structlog logger.

    In development (if `DEV_LOGGING=true`), it logs to the console in a
    human-readable format. Otherwise, it logs in JSON format, which is
    ideal for production environments.

    Args:
        name: The name of the logger (e.g., __name__).
        level: The minimum log level (e.g., "INFO", "DEBUG").

    Returns:
        A configured structlog logger instance.
    """
    is_dev_logging = os.getenv("DEV_LOGGING", "false").lower() in ("true", "1", "t")

    if not structlog.is_configured():
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ]

        if is_dev_logging:
            # Human-readable logs for development
            processors = shared_processors + [structlog.dev.ConsoleRenderer()]
        else:
            # JSON logs for production/staging
            processors = shared_processors + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ]

        structlog.configure(
            processors=processors,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    log = logging.getLogger(name)
    log.setLevel(level.upper())
    return structlog.wrap_logger(log)