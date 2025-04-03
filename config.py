# ===========================
# Logging Configuration
# ===========================
LOGGING_LEVEL = "DEBUG"  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ===========================
# Audio Processing Settings
# ===========================
# The options in lines 13-17 can be left as they are in most cases unless specific
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
LISTEN_FROM_WAV = False  # Whether to read audio input from a WAV file instead of a microphone
WAV_FILE_PATH = "input.wav"  # Path to the WAV file to be used as input

# ===========================
# LLM Inference Configuration
# ===========================
LLM_INFER = True  # Whether to enable LLM inference for command generation
LLM_INFER_EXE = "llama-cli"  # Path to the LLM inference executable
LLM_MODEL = "granite3.2-2b"  # Name of the LLM model to use.
							 # Supported models are gemma3-1b, gemma3-4b, granite3.2-2b
LLM_MODEL_DIR = "models"  # Directory where the LLM model is stored
LLM_SYSPROMPT = (  # System prompt for the LLM to guide its behavior
    "You are a command creator. You will be given some text and you must translate it into an "
    "explicit and concise command. Make sentences with correct grammar. Do not do anything else."
)

# ===========================
# Serial Communication Settings
# ===========================
WRITE_SERIAL = True  # Whether to send the generated command via serial communication
SERIAL_PORT = "/dev/rfcomm0"  # Path to the serial port used for Bluetooth communication

