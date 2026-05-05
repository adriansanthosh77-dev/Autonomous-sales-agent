from __future__ import annotations

import logging
import sys


def configure_logging(debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )
    return logging.getLogger("autonomous_sales_mcp")

