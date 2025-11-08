import io
import logging
import re

from air_quality.logging import get_logger


def test_get_logger_includes_context_and_no_dup_handlers():
    logger = get_logger("air_quality.tests.logging", run_id="123", module="demo")

    # Calling again should not add more handlers
    logger2 = get_logger("air_quality.tests.logging", run_id="123", module="demo")
    assert len(logger.logger.handlers) == 1 == len(logger2.logger.handlers)

    # Attach a temporary stream to capture formatted output from our configured formatter
    stream = io.StringIO()
    temp_handler = logging.StreamHandler(stream)
    temp_handler.setLevel(logging.INFO)
    # Use the same format spec as the library uses
    temp_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s - %(message)s | ctx=%(context)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    # Swap handlers for deterministic capture
    underlying = logger.logger
    existing = list(underlying.handlers)
    underlying.handlers = [temp_handler]

    try:
        logger.info("start")
        logger.info("finish")
    finally:
        # restore
        underlying.handlers = existing

    output = stream.getvalue()
    # Expected fields: timestamp, level, logger name, message, and serialized context
    assert " air_quality.tests.logging - start " in output
    assert " air_quality.tests.logging - finish " in output

    # Regex for ISO-like timestamp and level
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", output)
    assert "INFO" in output

    # Context should include run_id and module in JSON form
    assert "run_id" in output and "123" in output
    assert "module" in output and "demo" in output
