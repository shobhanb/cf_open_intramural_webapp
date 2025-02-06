"""Logging config."""

import logging.config
from pathlib import Path

import yaml
from rich.logging import RichHandler

LOGCONFIG = "logging.yaml"
LOGFOLDER = "log"


def setup_logger() -> None:
    """Initialize logger."""
    Path(LOGFOLDER).mkdir(exist_ok=True, parents=True)
    config_file = Path(LOGCONFIG)
    Path("log").mkdir(exist_ok=True)
    if config_file.exists():
        log_config = yaml.safe_load(config_file.read_text())
        logging.config.dictConfig(log_config)
    else:
        logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
