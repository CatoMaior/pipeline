"""
Core Module
-----------
This module contains core functionality for the pipeline:

- config: Configuration settings for the entire pipeline
- transcriber: Speech-to-text transcription functionality
- synthesizer: Text-to-speech synthesis functionality
"""

from .config import (
    # Class-based config exports
    Config, LoggingConfig, AudioConfig, TranscriptionConfig, LLMConfig, SynthesisConfig
)
from .transcriber import Transcriber, get_stats as get_transcription_stats
from .synthesizer import Synthesizer, get_stats as get_synthesis_stats

__all__ = [
    # Config class exports
    'Config', 'LoggingConfig', 'AudioConfig', 'TranscriptionConfig', 'LLMConfig', 'SynthesisConfig',

    # Class exports
    'Transcriber', 'Synthesizer',

    # Function exports
    'get_transcription_stats', 'get_synthesis_stats'
]
