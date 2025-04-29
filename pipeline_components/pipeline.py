import json
import sys
from datetime import datetime

from core.config import Config
from core.config_utils import log_config
from core.log_utils import setup_logging
from .ui_manager import UIManager
from .audio_handler import AudioHandler
from .transcriber_handler import TranscriberHandler
from .llm_handler import LLMHandler
from .synthesis_handler import SynthesisHandler


class Pipeline:
    """Main Pipeline class that orchestrates the entire process flow."""

    def __init__(self, options=None):
        """Initialize pipeline components and set up logging.

        Args:
            options (dict, optional): Command line options to override interactive prompts.
        """
        # Store options
        self.options = options or {}

        # Setup logging
        logger = setup_logging(
            log_to_console=self.options.get("log_to_console", False))
        self.logger = logger.getChild(__name__)
        self.logger.debug("Starting pipeline.")

        log_config(self.logger)

        self.ui = UIManager()
        self.audio = AudioHandler(self.logger)
        self.transcriber = TranscriberHandler(self.logger)
        self.llm = LLMHandler(self.logger)
        self.synthesis = SynthesisHandler(self.logger)
        self.use_case = None
        self.conversation_history = []  # Store the conversation history

        # Track the input method used
        self.use_audio = None  # Will be True for audio, False for text
        self.listen_from_wav = None  # Will be True for WAV, False for microphone
        self.wav_file_path = None  # For WAV file path if applicable

        print("Pipeline initialized. Logs will be saved to 'logs/latest.log'")

    def run(self):
        """Execute the entire pipeline."""
        try:
            # First select the use case
            if "use_case" in self.options:
                self.use_case = self.options["use_case"]
                self.logger.info(
                    f"Selected use case from command line: {self.use_case}")
            else:
                self.use_case = self.ui.get_use_case()
                self.logger.info(f"Selected use case: {self.use_case}")

            if not self.llm.check_ollama_running():
                self.logger.critical("Ollama service is not running.")
                sys.exit(1)

            # Get initial input
            initial_input = self._handle_input()
            if not initial_input:
                self.logger.error("No valid input received.")
                sys.exit(1)

            # Process initial request
            llm_output = self._process_with_llm(initial_input)
            if not llm_output:
                self.logger.error("No valid output from LLM.")
                sys.exit(1)

            self._handle_output(llm_output)

            # Check if follow-up interactions are enabled
            if self.options.get("enable_follow_up", True):
                self._handle_follow_up_interactions()

        except KeyboardInterrupt:
            self.logger.info("Pipeline interrupted by user.")
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            sys.exit(1)

    def _log_message_history(self, messages, purpose=""):
        """Log the full message history to aid in debugging.

        Args:
            messages: List of message dictionaries to log
            purpose: Optional description of the purpose of these messages
        """
        purpose_text = f" for {purpose}" if purpose else ""
        self.logger.info(
            f"Full message history sent to LLM{purpose_text}:\n{json.dumps(messages, indent=4)}")

    def _handle_follow_up_interactions(self):
        """Handle follow-up interactions with the user."""
        follow_up_needed = True

        while follow_up_needed:

            # Get follow-up input using same method as initial interaction
            additional_input = self._get_input()

            if additional_input is None:
                self.logger.error("No valid follow-up input received.")
                follow_up_needed = False
                continue

            # Add to conversation history
            self.conversation_history.append(
                {"role": "user", "content": additional_input})

            # Check if user wants to end the interaction using LLM to determine intent
            if self._is_conversation_complete(additional_input):
                # Generate a farewell message from the LLM
                farewell_message = self._generate_farewell_message(
                    additional_input)
                if farewell_message:
                    print(f"\nResponse:\n{farewell_message}")
                    self.conversation_history.append(
                        {"role": "assistant", "content": farewell_message})
                    # Handle output (play/save speech if applicable)
                    self._handle_output(farewell_message)
                else:
                    print("\nThank you for using the pipeline!")

                follow_up_needed = False
                continue

            # Process the follow-up with the entire conversation history
            follow_up_output = self._process_follow_up()

            if follow_up_output:
                # Update conversation history with assistant's response
                self.conversation_history.append(
                    {"role": "assistant", "content": follow_up_output})

                # Handle the output (synthesize speech if needed)
                self._handle_output(follow_up_output)
            else:
                self.logger.error(
                    "No valid output from follow-up LLM interaction.")
                follow_up_needed = False

    def _generate_farewell_message(self, user_input):
        """Generate a farewell message from the LLM when conversation is ending.

        Args:
            user_input: The user's last input that indicated the end of conversation

        Returns:
            str: A farewell message from the LLM
        """
        try:

            # Create a special prompt for the farewell message
            if self.use_case == "thermostat":
                system_prompt = """You are a smart thermostat. Use at most a pair of sentences.\nDo not add any details about the plan.\nKeep a simple and friendly tone. Do not ask any question."""
            else:
                system_prompt = """You are a helpful assistant. The user has indicated they're done with the conversation. Respond with a brief, friendly goodbye message that acknowledges this. Keep your response to one short sentence."""

            messages = self.conversation_history
            # Replace the system message
            for i, message in enumerate(messages):
                if message["role"] == "system":
                    messages[i] = {"role": "system", "content": system_prompt}
                    break

            messages.append({"role": "user", "content": user_input})

            # Log the full message history
            self._log_message_history(messages, "farewell")

            self.logger.info("Generating farewell message")
            response = self.llm.chat(Config.LLM.MODEL, messages)

            if response and 'message' in response and 'content' in response['message']:
                farewell = response['message']['content']
                self.logger.info(f"Farewell message: {farewell}")
                return farewell

        except Exception as e:
            self.logger.error(f"Error generating farewell message: {e}")

        return None

    def _get_input(self):
        """Get user input using the previously established method (text, microphone or WAV)."""
        if not self.use_audio:
            # Text input
            return self.ui.get_text_input()
        else:
            # Audio input
            if self.listen_from_wav:
                # For follow-ups with WAV, ask for new file path each time
                wav_file_path = self.ui.get_wav_file_path()
                speech_segment = self.audio.load_from_wav(wav_file_path)
            else:
                # Microphone input
                speech_segment = self.audio.record_from_microphone()

            if speech_segment is None:
                return None

            transcribed = self.transcriber.transcribe(speech_segment)
            self.logger.info(f"Transcription: {transcribed}")
            print(f"\nTranscription:\n{transcribed}")
            return transcribed

    def _handle_input(self):
        """Handle initial user input via text or audio and return transcribed text."""
        if "interaction_mode" in self.options:
            self.use_audio = self.options["interaction_mode"]
            self.logger.info(
                f"Using {'audio' if self.use_audio else 'text'} input mode from command line")
        else:
            self.use_audio = self.ui.get_interaction_mode()

        if not self.use_audio:
            # Text input
            if "text_input" in self.options:
                text_input = self.options["text_input"]
                self.logger.info(
                    f"Using text input from command line: {text_input}")
                return text_input
            else:
                return self.ui.get_text_input()
        else:
            # Audio input
            if "audio_source" in self.options:
                self.listen_from_wav = self.options["audio_source"]
                self.logger.info(
                    f"Using {'WAV file' if self.listen_from_wav else 'microphone'} as audio source from command line")
            else:
                self.listen_from_wav = self.ui.get_audio_source()

            if self.listen_from_wav:
                if "wav_file_path" in self.options:
                    self.wav_file_path = self.options["wav_file_path"]
                    self.logger.info(
                        f"Using WAV file from command line: {self.wav_file_path}")
                else:
                    self.wav_file_path = self.ui.get_wav_file_path()
                speech_segment = self.audio.load_from_wav(self.wav_file_path)
            else:
                speech_segment = self.audio.record_from_microphone()

            if speech_segment is None:
                return None

            transcribed = self.transcriber.transcribe(speech_segment)
            self.logger.info(f"Transcription: {transcribed}")
            print(f"\nTranscription:\n{transcribed}")
            return transcribed

    def _is_conversation_complete(self, user_input):
        """Determine if the user wants to end the conversation.

        Uses simple keyword matching as a fallback but also asks the LLM when in doubt.

        Args:
            user_input: The user's latest input

        Returns:
            bool: True if the conversation should end, False to continue
        """

        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that determines if a user input mean that they want to execute some previously agreed actions or not, ending the conversation.\nAssume that when the user asks a question he has still not agreed.\nAssume that if the is giving new information the conversation is not over.\nRespond with ONLY 'yes' if they are done or 'no' if they want to continue."},
                {"role": "user", "content": f"The last message the user got is: \"{self.conversation_history[-2]['content']}\". The user answered: \"{user_input}\". Does this user response indicate that he wants to execute the previously agreed actions? Respond with ONLY 'yes' or 'no'"}
            ]

            # Log the full message history
            self._log_message_history(
                messages, "conversation completion check")

            self.logger.info(
                "Asking LLM to determine if conversation is complete")
            response = self.llm.chat(Config.LLM.MODEL, messages)

            # Log the raw LLM response
            self.logger.info(f"LLM raw response: {response}")

            if response and 'message' in response and 'content' in response['message']:
                llm_decision = response['message']['content'].strip().lower()
                self.logger.info(
                    f"LLM completion determination: {llm_decision}")

                # Check if the LLM thinks the conversation is complete
                if 'yes' in llm_decision:
                    return True
        except Exception as e:
            self.logger.error(
                f"Error determining conversation completion: {e}")

        return False

    def _process_follow_up(self):
        """Process a follow-up input with the entire conversation context."""
        if not self.llm.ensure_model_available(Config.LLM.MODEL):
            self.logger.critical(f"Could not obtain model {Config.LLM.MODEL}.")
            return None

        # Log the conversation history before sending to LLM
        self._log_message_history(self.conversation_history, "follow-up")

        print("\nProcessing your request, please wait...")

        self.logger.info("Sending follow-up input to LLM.")
        response = self.llm.chat(Config.LLM.MODEL, self.conversation_history)

        if response and 'message' in response and 'content' in response['message']:
            llm_output = response['message']['content']
            self.logger.info(f"Follow-up LLM output: \n{llm_output}")
            print(f"\nResponse:\n{llm_output}")
            return llm_output

        return None

    def _process_with_llm(self, transcribed_text):
        """Process the transcribed text with LLM."""
        if not self.llm.ensure_model_available(Config.LLM.MODEL):
            self.logger.critical(f"Could not obtain model {Config.LLM.MODEL}.")
            sys.exit(1)

        # Use the already selected use case
        if self.use_case == "thermostat":
            system_prompt = Config.LLM.THERMOSTAT_SYSPROMPT
            self.logger.info("Using smart thermostat system prompt.")
        else:  # Default/agnostic case
            system_prompt = Config.LLM.SYSPROMPT
            self.logger.info("Using default system prompt.")

        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcribed_text}
        ]

        # Apply model-specific reasoning method BEFORE logging
        reasoning_method = Config.LLM.get_reasoning_method(Config.LLM.MODEL)
        if reasoning_method:
            if reasoning_method["method"] == "control/thinking":
                self.logger.info(
                    f"Applying reasoning method 'control/thinking' for {Config.LLM.MODEL}")
                self.conversation_history.insert(
                    1, {"role": "control", "content": "thinking"})

        # Log the full message history
        self._log_message_history(self.conversation_history, "initial request")

        print("\nProcessing your request, please wait...")

        self.logger.info("Sending input to LLM.")
        response = self.llm.chat(Config.LLM.MODEL, self.conversation_history)

        if response and 'message' in response and 'content' in response['message']:
            llm_output = response['message']['content']
            self.logger.info(f"LLM output: \n{llm_output}")
            print(f"\nResponse:\n{llm_output}")
            self.conversation_history.append(
                {"role": "assistant", "content": llm_output})
            return llm_output

        return None

    def _handle_output(self, llm_output):
        """Handle the output from LLM (save/play synthesized speech)."""
        if "output_mode" in self.options:
            output_choice = self.options["output_mode"]
            self.logger.info(f"Output mode from command line: {output_choice}")
        else:
            output_choice = self.ui.get_output_mode()

        # For thermostat use case, extract only the user response part
        synthesis_text = llm_output
        if self.use_case == "thermostat":
            try:
                # Look for the user response section
                if "USER RESPONSE:" in llm_output:
                    # Extract everything after "USER RESPONSE:"
                    parts = llm_output.split("USER RESPONSE:")
                    if len(parts) > 1:
                        synthesis_text = parts[1].strip()
                        self.logger.info(
                            "Extracted user response part for synthesis")
                else:
                    self.logger.warning(
                        "Expected 'USER RESPONSE:' not found in LLM output")
            except Exception as e:
                self.logger.error(f"Error extracting user response: {e}")
                # Fallback to using the full text
                synthesis_text = llm_output

        filename = None
        if output_choice in ['1', '3']:  # Save or Save and play
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{Config.SYNTHESIS.OUTPUT_DIR}/output_{timestamp}.wav"

            if "output_filename" in self.options:
                filename = self.options["output_filename"]
                self.logger.info(
                    f"Using output filename from command line: {filename}")
            else:
                filename = self.ui.get_output_filename(default_filename)

            self.synthesis.save_output(synthesis_text, filename)
            self.logger.info(f"Audio saved to {filename}")

        if output_choice == '2':  # Play only
            self.synthesis.play_raw_output(synthesis_text)
            self.logger.info("Audio playback completed.")
        elif output_choice == '3':  # Save and play
            self.synthesis.play_output(filename)
            self.logger.info("Audio playback completed.")
