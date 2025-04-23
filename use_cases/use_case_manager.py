"""Manager for loading use case-specific resources."""

import os
import importlib.util
from pathlib import Path

class UseCaseManager:
    """Manager for loading use case-specific resources."""

    def __init__(self, base_dir=None):
        """Initialize the use case manager.

        Args:
            base_dir: Base directory for use case resources. If None,
                     defaults to 'use_cases' in the current directory.
        """
        if base_dir is None:
            # Default to the 'use_cases' directory in the same directory as this file
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)

        # Validate that the directory exists
        if not self.base_dir.exists() or not self.base_dir.is_dir():
            raise ValueError(f"Use case directory not found: {self.base_dir}")

    def get_questions(self, use_case="general"):
        """Get questions for the specified use case.

        Args:
            use_case: Name of the use case (corresponds to a subdirectory)

        Returns:
            List of questions for the specified use case
        """
        questions_file = self.base_dir / use_case / "questions.py"

        if not questions_file.exists():
            raise ValueError(f"Questions file not found for use case: {use_case}")

        # Load the questions dynamically
        spec = importlib.util.spec_from_file_location("questions", questions_file)
        questions_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(questions_module)

        return questions_module.questions

    def get_input_wav_path(self, use_case="general"):
        """Get the path to the input WAV file for the specified use case.

        Args:
            use_case: Name of the use case (corresponds to a subdirectory)

        Returns:
            Path to the input WAV file
        """
        wav_file = self.base_dir / use_case / "input.wav"

        if not wav_file.exists():
            raise ValueError(f"Input WAV file not found for use case: {use_case}")

        return str(wav_file)

    def get_available_use_cases(self):
        """Get a list of available use cases.

        Returns:
            List of use case names
        """
        return [d.name for d in self.base_dir.iterdir()
                if d.is_dir() and (d / "questions.py").exists()]
