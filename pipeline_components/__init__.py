"""
Pipeline Components Package
--------------------------
This package contains modular components for the audio processing pipeline:

- ui_manager: Handles user interface interactions
- audio_handler: Manages audio recording and file operations
- transcriber_handler: Handles speech-to-text conversion
- llm_handler: Handles LLM interactions
- synthesis_handler: Manages text-to-speech conversion
- transcriber: Core transcription functionality
- synthesizer: Core speech synthesis functionality
- questions: Predefined questions for testing
- pipeline: Main pipeline orchestration
"""

__all__ = [
    'ui_manager',
    'audio_handler',
    'transcriber_handler',
    'llm_handler',
    'synthesis_handler',
    'transcriber',
    'synthesizer',
    'questions',
    'pipeline'
]
