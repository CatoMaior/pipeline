import os
from core import Config
from use_cases.use_case_manager import UseCaseManager

class UIManager:
    """Handles all user interface interactions including prompts and input parsing."""

    def __init__(self):
        """Initialize the UI manager."""
        self.use_case_manager = UseCaseManager()
        self.current_use_case = "general"  # Default use case

    def get_use_case(self):
        """Get the use case selection from the user."""
        # Display available use cases from config
        available_use_cases = Config.USE_CASE.AVAILABLE_USE_CASES

        print("\n==============================")
        print("USE CASE SELECTION")
        print("==============================")
        print("Select the use case for this session:")

        # Display available use cases
        for i, (key, name) in enumerate(available_use_cases.items(), 1):
            print(f"  {i}. {name}")

        print("(default is 1): ", end="")
        use_case_choice = input().strip()

        # Default to first option (general)
        if not use_case_choice or not use_case_choice.isdigit():
            self.current_use_case = list(available_use_cases.keys())[0]
        else:
            idx = int(use_case_choice) - 1
            if 0 <= idx < len(available_use_cases):
                self.current_use_case = list(available_use_cases.keys())[idx]
            else:
                self.current_use_case = list(available_use_cases.keys())[0]

        return self.current_use_case

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
        # Get the questions for the current use case
        use_case_questions = self.use_case_manager.get_questions(self.current_use_case)

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
            # Show predefined questions for the current use case
            print("\nAvailable Questions:")
            for idx, question in enumerate(use_case_questions, start=1):
                print(f"  {idx}. {question}")

            question_idx = input(
                "\nEnter the number of the question you want to use (default is 1): "
            ).strip()
            question_idx = int(question_idx) - 1 if question_idx.isdigit() else 0

            # Validate index
            if 0 <= question_idx < len(use_case_questions):
                return use_case_questions[question_idx]
            else:
                return use_case_questions[0]  # Default to first question
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
        # Get the default WAV file for the current use case
        default_absolute_path = self.use_case_manager.get_input_wav_path(self.current_use_case)

        # Convert to a relative path for display purposes
        cwd = os.path.abspath(os.getcwd())
        if default_absolute_path.startswith(cwd):
            # Create a path relative to current working directory
            display_path = os.path.relpath(default_absolute_path, cwd)
        else:
            # If not under current directory, just use the filename
            display_path = os.path.basename(default_absolute_path)

        wav_file_path = input(
            f"\n==============================\n"
            "WAV FILE INPUT\n"
            "==============================\n"
            f"Enter the relative path to the WAV file (default: {display_path}): "
        ).strip()

        # If user provided a path, use it; otherwise return the absolute path from use case manager
        if wav_file_path:
            # If the user provided a relative path, make it absolute
            if not os.path.isabs(wav_file_path):
                wav_file_path = os.path.abspath(os.path.join(cwd, wav_file_path))
            return wav_file_path
        else:
            return default_absolute_path

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
