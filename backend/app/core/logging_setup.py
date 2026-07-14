import logging


def setup_logging(level: str) -> None:
    """Configure application logging.

    Args:
        level: Logging level (e.g., INFO, DEBUG).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

