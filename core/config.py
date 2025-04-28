"""Configuration module for the pipeline system.

This file contains all configurable parameters for the audio processing pipeline,
including logging, audio processing, speech-to-text, LLM inference, and text-to-speech settings.
"""
from dataclasses import dataclass
from typing import ClassVar, Dict


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    LEVEL: str = "INFO"
    """Logging level. Possible values: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"."""


@dataclass
class AudioConfig:
    """Audio processing configuration settings."""
    SAMPLING_RATE: int = 16000
    """Sampling rate for audio input in Hz."""

    CHUNK_SIZE: int = 512
    """Size of audio chunks processed at a time."""

    MAX_SPEECH_SECS: int = 60
    """Maximum duration of speech recording in seconds."""

    VAD_THRESHOLD: float = 0.5
    """Voice Activity Detection (VAD) threshold for detecting speech."""

    VAD_MIN_SILENCE_MS: int = 500
    """Minimum silence duration (in ms) to consider speech as ended."""

    # Default WAV paths are now managed by the UseCaseManager
    DEFAULT_WAV_DIR: str = "use_cases"
    """Directory containing use case-specific resources."""


@dataclass
class TranscriptionConfig:
    """Speech-to-text configuration settings."""
    MOONSHINE_MODEL: str = "moonshine/base"
    """Name of the Moonshine ONNX model to use."""


@dataclass
class LLMConfig:
    """LLM inference configuration settings."""
    MODEL: str = "granite3.3:8b"
    """Name of the LLM model to use. Supported models are the ones available in ollama https://ollama.com/"""

    SYSPROMPT: str = """You are a reasoning assistant. When you answer, do not use any kind of text formatting. Be concise but thorough with your responses. After addressing their question, check if they need additional assistance or have follow-up questions."""
    """System prompt for the LLM to guide its behavior."""

    THERMOSTAT_SYSPROMPT: str = """You are a smart thermostat. You have to understand the user's needs and act accordingly. Your responses should be divided into two clear parts:

PART 1 - INSTRUCTIONS:
Provide a clear, step-by-step plan on how you are going to achieve the necessary climate control task. Produce a numbered list with the steps you will take. Assume you have access to the room temperature, to some API to get weather forecasts in the area, and to the thermostat controls. Remember that actions such as turning on/off the heater or air conditioning, setting the temperature, and so on, are not immediate and the effects will be seen after a while.

PART 2 - USER RESPONSE:
Give a brief summary of the outcomes of the actions you decided to take. Do not add unnecessary details. Be informal and friendly. End this part asking the user if they want to add more details or have any other needs. This part must end with a question mark.

Always label each part clearly. If in successive turns the user gives you more details about their needs, you can update your plan in PART 1, editing some parts of it or adding new parts.
"""
    """System prompt for smart thermostat use case."""

    # Dictionary mapping model prefixes to their reasoning activation methods
    REASONING_CONFIG: dict = None
    """Dictionary mapping model prefixes to their reasoning activation methods."""

    REASONING_ENABLED: bool = True
    """Whether reasoning is enabled for models that support it."""

    def __post_init__(self):
        if self.REASONING_CONFIG is None:
            self.REASONING_CONFIG = {
                # Method: 'control/thinking' uses the control role with 'thinking' content
                "granite3.2": {"method": "control/thinking"},
                "granite3.3": {"method": "control/thinking"},
                # Add other models with potentially different methods here
                # Example: "other-model": {"method": "different-method", "parameters": {...}}
            }

    def get_reasoning_method(self, model_name: str) -> dict:
        """Get the reasoning activation method for the given model.

        Args:
            model_name: The name of the model to check

        Returns:
            Dictionary containing reasoning method info or None if reasoning isn't
            supported/enabled for this model
        """
        if not self.REASONING_ENABLED:
            return None

        for prefix, config in self.REASONING_CONFIG.items():
            if model_name.startswith(prefix):
                return config

        return None

    def needs_reasoning(self, model_name: str) -> bool:
        """Check if the given model needs reasoning activation.

        This is a convenience method that returns a boolean rather than the full
        reasoning configuration.

        Args:
            model_name: The name of the model to check

        Returns:
            True if the model requires reasoning activation, False otherwise
        """
        return self.get_reasoning_method(model_name) is not None


@dataclass
class SynthesisConfig:
    """Text-to-speech configuration settings."""
    PIPER_MODEL_PATH: str = "piper_models/en_US-amy-medium.onnx"
    """Path to the Piper model."""

    OUTPUT_DIR: str = "wav_outputs"
    """Directory to save output audio files."""


@dataclass
class UseCaseConfig:
    """Use case configuration settings."""
    AVAILABLE_USE_CASES: Dict[str, str] = None
    """Available use cases with their display names."""

    def __post_init__(self):
        if self.AVAILABLE_USE_CASES is None:
            self.AVAILABLE_USE_CASES = {
                "general": "General Assistant",
                "thermostat": "Smart Thermostat Agent"
            }


@dataclass
class Config:
    """Main configuration class that holds all configuration sections."""
    LOGGING: ClassVar[LoggingConfig] = LoggingConfig()
    AUDIO: ClassVar[AudioConfig] = AudioConfig()
    TRANSCRIPTION: ClassVar[TranscriptionConfig] = TranscriptionConfig()
    LLM: ClassVar[LLMConfig] = LLMConfig()
    SYNTHESIS: ClassVar[SynthesisConfig] = SynthesisConfig()
    USE_CASE: ClassVar[UseCaseConfig] = UseCaseConfig()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python config.py <PARAMETER_NAME>")
        sys.exit(1)

    parameter_name = sys.argv[1]
    try:
        # Try to find the parameter in the Config class structure
        parts = parameter_name.split('.')
        if len(parts) == 1:
            # Check if it's a section name
            if hasattr(Config, parts[0]):
                parameter_value = getattr(Config, parts[0])
            else:
                raise KeyError(f"Parameter '{parameter_name}' not found")
        elif len(parts) == 2:
            # It's a parameter within a section
            section, param = parts
            if hasattr(Config, section) and hasattr(getattr(Config, section), param):
                parameter_value = getattr(getattr(Config, section), param)
            else:
                raise KeyError(f"Parameter '{parameter_name}' not found")
        else:
            raise KeyError(f"Invalid parameter format: '{parameter_name}'")

        print(parameter_value)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)