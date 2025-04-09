# ===========================
# Logging Configuration
# ===========================
LOGGING_LEVEL = "INFO"  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ===========================
# Audio Processing Settings
# ===========================
# The options in lines 12-16 can be left as they are in most cases unless specific
# adjustments are needed for your hardware or use case.
ENABLE_PLAYBACK = False  # Whether to play back the recorded audio after processing
SAMPLING_RATE = 16000  # Sampling rate for audio input in Hz
CHUNK_SIZE = 512  # Size of audio chunks processed at a time
MAX_SPEECH_SECS = 60  # Maximum duration of speech recording in seconds
VAD_THRESHOLD = 0.5  # Voice Activity Detection (VAD) threshold for detecting speech
VAD_MIN_SILENCE_MS = 500  # Minimum silence duration (in ms) to consider speech as ended

# ===========================
# STT Configuration
# ===========================
MOONSHINE_MODEL = "moonshine/base"  # Name of the Moonshine ONNX model to use

# ===========================
# WAV File Input Settings
# ===========================
WAV_FILE_PATH = "input.wav"  # Path to the default WAV file to be used as input

# ===========================
# LLM Inference Configuration
# ===========================
LLM_MODEL = "granite3.2:2b"  # Name of the LLM model to use.
LLM_SYSPROMPT = (  # System prompt for the LLM to guide its behavior
    "You are a reasoning assistant. When you answer, do not use any kind of text formatting."
)

# ===========================
# Text-to-Speech (TTS) Settings
# ===========================
PIPER_MODEL_PATH = "piper-models/en_US-amy-medium.onnx"  # Path to the Piper model
OUTPUT_DIR = "wav-outputs"  # Directory to save output audio files

