import os
import logging
from datetime import datetime
from .config import Config

def setup_logging(log_to_console=False):
    """
    Set up logging to file and optionally to console.

    Args:
        log_to_console (bool): Whether to also log to console.

    Returns:
        logging.Logger: Configured root logger.
    """
    os.makedirs("logs", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/pipeline_{timestamp}.log"

    latest_log = "logs/latest.log"
    if os.path.exists(latest_log) or os.path.islink(latest_log):
        os.remove(latest_log)
    os.symlink(os.path.basename(log_file), latest_log)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_format)
        console_handler.setLevel(getattr(logging, Config.LOGGING.LEVEL.upper(), logging.INFO))
        root_logger.addHandler(console_handler)

    return root_logger
