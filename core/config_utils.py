"""Configuration utilities for the pipeline system.

This module provides helper functions for working with the configuration system.
"""

from .config import Config, LoggingConfig, AudioConfig, TranscriptionConfig, LLMConfig, SynthesisConfig

def get_config_as_dict():
    """
    Get all configuration as a nested dictionary.

    Returns:
        dict: A dictionary containing all configuration values organized by section.
    """
    return {
        "logging": {k: v for k, v in vars(Config.LOGGING).items() if not k.startswith("__")},
        "audio": {k: v for k, v in vars(Config.AUDIO).items() if not k.startswith("__")},
        "transcription": {k: v for k, v in vars(Config.TRANSCRIPTION).items() if not k.startswith("__")},
        "llm": {k: v for k, v in vars(Config.LLM).items() if not k.startswith("__")},
        "synthesis": {k: v for k, v in vars(Config.SYNTHESIS).items() if not k.startswith("__")}
    }

def print_config():
    """
    Print all configuration values in a human-readable format.
    """
    config_dict = get_config_as_dict()

    print("Configuration Settings:")
    print("=======================")

    for section_name, section_values in config_dict.items():
        print(f"\n{section_name.upper()} CONFIGURATION:")
        print("-" * (len(section_name) + 14))

        for key, value in section_values.items():
            print(f"  {key}: {value}")

def log_config(logger):
    """
    Log all configuration values using the provided logger.

    Args:
        logger: A logging.Logger instance to use for logging.
    """
    config_dict = get_config_as_dict()

    logger.debug("Configuration Settings:")

    for section_name, section_values in config_dict.items():
        logger.debug(f"{section_name.upper()} CONFIGURATION:")

        for key, value in section_values.items():
            logger.debug(f"  {key}: {value}")

if __name__ == "__main__":
    print_config()
