import logging
import sys
from datetime import datetime

from core.config import Config
from core.config_utils import log_config
from .ui_manager import UIManager
from .audio_handler import AudioHandler
from .transcriber_handler import TranscriberHandler
from .llm_handler import LLMHandler
from .synthesis_handler import SynthesisHandler

class Pipeline:
    """Main Pipeline class that orchestrates the entire process flow."""

    def __init__(self):
        """Initialize pipeline components and set up logging."""
        logging.basicConfig(
            level=getattr(logging, Config.LOGGING.LEVEL.upper(), logging.INFO),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Starting pipeline.")

        log_config(self.logger)

        self.ui = UIManager()
        self.audio = AudioHandler(self.logger)
        self.transcriber = TranscriberHandler(self.logger)
        self.llm = LLMHandler(self.logger)
        self.synthesis = SynthesisHandler(self.logger)

    def run(self):
        """Execute the entire pipeline."""
        try:
            if not self.llm.check_ollama_running():
                self.logger.critical("Ollama service is not running.")
                sys.exit(1)
            transcribed_text = self._handle_input()
            if not transcribed_text:
                self.logger.error("No valid input received.")
                sys.exit(1)
            llm_output = self._process_with_llm(transcribed_text)
            if not llm_output:
                self.logger.error("No valid output from LLM.")
                sys.exit(1)
            self._handle_output(llm_output)

        except KeyboardInterrupt:
            self.logger.info("Pipeline interrupted by user.")
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            sys.exit(1)

    def _handle_input(self):
        """Handle user input via text or audio and return transcribed text."""
        use_audio = self.ui.get_interaction_mode()
        if not use_audio:
            return self.ui.get_text_input()
        else:
            listen_from_wav = self.ui.get_audio_source()
            if listen_from_wav:
                wav_file_path = self.ui.get_wav_file_path()
                speech_segment = self.audio.load_from_wav(wav_file_path)
            else:
                speech_segment = self.audio.record_from_microphone()
            if speech_segment is None:
                return None
            transcribed = self.transcriber.transcribe(speech_segment)
            self.logger.info(f"Transcription: {transcribed}")
            return transcribed

    def _process_with_llm(self, transcribed_text):
        """Process the transcribed text with LLM."""
        if not self.llm.ensure_model_available(Config.LLM.MODEL):
            self.logger.critical(f"Could not obtain model {Config.LLM.MODEL}.")
            sys.exit(1)
        messages = [
            {"role": "system", "content": Config.LLM.SYSPROMPT},
            {"role": "user", "content": transcribed_text}
        ]
        if "granite3.2" in Config.LLM.MODEL and self.ui.should_enable_reasoning():
            messages.insert(0, {"role": "control", "content": "thinking"})
        self.logger.info("Sending input to LLM.")
        response = self.llm.chat(Config.LLM.MODEL, messages)

        if response and 'message' in response and 'content' in response['message']:
            llm_output = response['message']['content']
            self.logger.info(f"LLM output: \n{llm_output}")
            return llm_output

        return None

    def _handle_output(self, llm_output):
        """Handle the output from LLM (save/play synthesized speech)."""
        output_choice = self.ui.get_output_mode()

        filename = None
        if output_choice in ['1', '3']:  # Save or Save and play
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{Config.SYNTHESIS.OUTPUT_DIR}/output_{timestamp}.wav"
            filename = self.ui.get_output_filename(default_filename)

            self.synthesis.save_output(llm_output, filename)
            self.logger.info(f"Audio saved to {filename}")

        if output_choice == '2':  # Play only
            self.synthesis.play_raw_output(llm_output)
            self.logger.info("Audio playback completed.")
        elif output_choice == '3':  # Save and play
            self.synthesis.play_output(filename)
            self.logger.info("Audio playback completed.")
