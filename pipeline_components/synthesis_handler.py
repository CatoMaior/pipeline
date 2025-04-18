import os
from core.synthesizer import Synthesizer
from core.config import Config

class SynthesisHandler:
    """Handles speech synthesis operations."""

    def __init__(self, logger):
        """Initialize the synthesis handler."""
        self.logger = logger
        self.synthesizer = Synthesizer(Config.SYNTHESIS.PIPER_MODEL_PATH)

    def save_output(self, text, filename):
        """Save synthesized speech to a WAV file."""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Synthesize and save
            self.synthesizer.save_output(text, filename)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save synthesized speech: {e}")
            return False

    def play_output(self, filename):
        """Play synthesized speech from a WAV file."""
        try:
            self.synthesizer.play_output(filename)
            return True
        except Exception as e:
            self.logger.error(f"Failed to play synthesized speech file: {e}")
            return False

    def play_raw_output(self, text):
        """Synthesize speech and play it without saving."""
        try:
            self.synthesizer.play_raw_output(text)
            return True
        except Exception as e:
            self.logger.error(f"Failed to play raw synthesized speech: {e}")
            return False
