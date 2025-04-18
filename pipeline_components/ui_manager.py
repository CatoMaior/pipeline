import os
from .questions import questions
from core import Config

class UIManager:
    """Handles all user interface interactions including prompts and input parsing."""

    def get_interaction_mode(self):
        """Ask user to choose interaction mode (audio or text)."""
        interaction_mode = input(
            "\n==============================\n"
            "INTERACTION MODE SELECTION\n"
            "==============================\n"
            "Do you want to interact via:\n"
            "  1. Audio interaction\n"
            "  2. Writing interaction\n"
            "(default is 1): "
        ).strip()
        return interaction_mode != '2'  # Default to audio (True) unless '2' is selected

    def get_text_input(self):
        """Get user input as text, either custom or from predefined questions."""
        text_input_choice = input(
            "\n==============================\n"
            "TEXT INPUT MODE\n"
            "==============================\n"
            "Do you want to:\n"
            "  1. Write your own input\n"
            "  2. Use a predefined question\n"
            "(default is 2): "
        ).strip()

        if text_input_choice != '1':
            # Show predefined questions
            print("\nAvailable Questions:")
            for idx, question in enumerate(questions, start=1):
                print(f"  {idx}. {question}")

            question_idx = input(
                "\nEnter the number of the question you want to use (default is 1): "
            ).strip()
            question_idx = int(question_idx) - 1 if question_idx.isdigit() else 0

            # Validate index
            if 0 <= question_idx < len(questions):
                return questions[question_idx]
            else:
                return questions[0]  # Default to first question
        else:
            # Get custom input
            return input("Enter your input text: ").strip()

    def get_audio_source(self):
        """Ask user to choose audio source (WAV file or microphone)."""
        user_choice = input(
            "\n==============================\n"
            "AUDIO INPUT MODE\n"
            "==============================\n"
            "Do you want to listen from:\n"
            "  1. A WAV file\n"
            "  2. The microphone\n"
            "(default is 1): "
        ).strip()
        return user_choice != '2'  # Default to WAV file (True) unless '2' is selected

    def get_wav_file_path(self):
        """Get WAV file path from user."""
        default_wav_path = Config.AUDIO.WAV_FILE_PATH
        wav_file_path = input(
            f"\n==============================\n"
            "WAV FILE INPUT\n"
            "==============================\n"
            f"Enter the relative path to the WAV file (default: {default_wav_path}): "
        ).strip()
        return wav_file_path if wav_file_path else default_wav_path

    def should_enable_reasoning(self):
        """Ask if reasoning should be enabled for Granite models."""
        enable_reasoning_choice = input(
            "\n==============================\n"
            "ENABLE REASONING\n"
            "==============================\n"
            "This model requires reasoning to be explicitly activated. Would you like to enable it?\n"
            "  1. Yes, enable reasoning\n"
            "  2. No, keep it disabled\n"
            "(default is 1): "
        ).strip()
        return enable_reasoning_choice != '2'  # Default to enabled (True) unless '2' is selected

    def get_output_mode(self):
        """Ask user how to handle the output (save/play/both/neither)."""
        output_choice = input(
            "\n==============================\n"
            "OUTPUT OPTIONS\n"
            "==============================\n"
            "Do you want to:\n"
            "  1. Save the output\n"
            "  2. Play the output\n"
            "  3. Save and play the output\n"
            "  4. Do neither\n"
            "(default is 4): "
        ).strip()
        return output_choice if output_choice in ['1', '2', '3', '4'] else '4'

    def get_output_filename(self, default_filename):
        """Get filename for saving output."""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(default_filename), exist_ok=True)

        filename = input(
            f"\n==============================\n"
            "SAVE OUTPUT\n"
            "==============================\n"
            f"Enter the relative filename to save the output (default: {default_filename}): "
        ).strip()
        return filename if filename else default_filename
