from os import path

PATH = path.dirname(path.abspath(__file__))

LOGGING_LEVEL = "INFO"
PLAY_RECORDING = False

SAMPLING_RATE = 16000
CHUNK_SIZE = 512
MAX_SPEECH_SECS = 60
VAD_THRESHOLD = 0.5
VAD_MIN_SILENCE_MS = 500
MOONSHINE_MODEL = "moonshine/base"

LLM_INFER = True
LLM_INFER_EXE = "llama-cli"
LLM_MODEL = "models/gemma-3-4b-it-Q4_K_M.gguf"
LLM_SYSPROMPT = "You are a command creator. You will be given some text and you must translate it into an explicit and coincise command. Make sentences with correct grammar. Do not do anything else."

WRITE_SERIAL = True
SERIAL_PORT = "/dev/rfcomm0"
