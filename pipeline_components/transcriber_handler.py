from core.transcriber import Transcriber

class TranscriberHandler:
    """Handles transcription of audio data to text."""

    def __init__(self, logger):
        """Initialize the transcriber handler."""
        self.logger = logger
        self.transcriber = Transcriber(logger=logger)

    def transcribe(self, audio_data):
        """Transcribe audio data to text."""
        if audio_data is None or len(audio_data) == 0:
            self.logger.warning("Empty audio received for transcription")
            return ""

        try:
            transcribed = self.transcriber(audio_data.flatten())
            return transcribed if transcribed else ""
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return ""
