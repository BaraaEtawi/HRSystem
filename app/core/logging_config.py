import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_rotating_file_logger():
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        handler = RotatingFileHandler(log_dir / "app.log", maxBytes=5_000_000, backupCount=3)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(fmt)

        root = logging.getLogger()
        if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
            root.addHandler(handler)
        if root.level == logging.WARNING:
            root.setLevel(logging.INFO)
    except Exception:
        return

