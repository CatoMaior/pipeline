import os
from core.config import Config

class SynthesisHandler:
    """Handles speech synthesis operations."""

    def __init__(self, logger):
        """Initialize the synthesis handler."""
        self.logger = logger
        from core.synthesizer import Synthesizer
        self.synthesizer = Synthesizer(Config.SYNTHESIS.PIPER_MODEL_PATH)
        self.synthesizer.logger = logger

    def save_output(self, text, filename):
        """Save synthesized speech to a WAV file."""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            result = self.synthesizer.save_output(text, filename)
            if isinstance(result, dict) and "error" in result:
                self.logger.error(f"Synthesis error: {result['error']}")
                return False
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
            return self.synthesizer.play_raw_output(text)
        except Exception as e:
            self.logger.error(f"Failed to play raw synthesized speech: {e}")
            return False
