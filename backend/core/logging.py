"""Structured-enough logging setup shared by the API, the simulator and workers."""

from __future__ import annotations

import logging
import sys

from core.settings import get_settings


def configure_logging() -> None:
    # Windows consoles default to cp1252; legacy modules print emoji.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: S110  (runs before logging exists; non-reconfigurable streams are fine)
            pass

    logging.basicConfig(
        level=get_settings().log_level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stdout,
        force=True,
    )
