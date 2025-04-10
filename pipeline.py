import logging
import numpy as np
from ollama import ChatResponse, ListResponse, ResponseError, chat
import ollama
import sounddevice as sd
from queue import Queue
from silero_vad import VADIterator, load_silero_vad
from sounddevice import InputStream
from piper.voice import PiperVoice
import sys
import os
import wave
import datetime

import config
import transcriber

logging.basicConfig(
	level=getattr(logging, config.LOGGING_LEVEL.upper(), logging.INFO),
	format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_input_callback(q):
	def callback(indata, frames, time_info, status):
		if status:
			logger.warning(f"Input stream status: {status}")
		if indata is not None:
			q.put(indata.copy().flatten())
		else:
			logger.error("No input data received in callback")
	return callback

logger.debug("Starting pipeline.")
logger.debug("Configuration settings:")
for key, value in vars(config).items():
	if not key.startswith("__"):
		logger.debug(f"{key}: {value}")

try:
	ollama.ps()
except Exception as e:
	logger.critical("%s", e)
	sys.exit(1)

interaction_mode = input(
	"\n==============================\n"
	"INTERACTION MODE SELECTION\n"
	"==============================\n"
	"Do you want to interact via:\n"
	"  1. Audio interaction\n"
	"  2. Writing interaction\n"
	"(default is 1): "
).strip()
use_audio = interaction_mode == '1' if interaction_mode in ['1', '2'] else True

if not use_audio:
	from questions import questions
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
		print("\nAvailable Questions:")
		for idx, question in enumerate(questions, start=1):
			print(f"  {idx}. {question}")
		question_idx = input(
			"\nEnter the number of the question you want to use (default is 1): "
		).strip()
		question_idx = int(question_idx) - 1 if question_idx.isdigit() else 0
		transcribed = questions[question_idx]
	else:
		transcribed = input(
			"Enter your input text: "
		).strip()
else:
	transcriber = transcriber.Transcriber(logger=logger)
	user_choice = input(
		"\n==============================\n"
		"AUDIO INPUT MODE\n"
		"==============================\n"
		"Do you want to listen from:\n"
		"  1. A WAV file\n"
		"  2. The microphone\n"
		"(default is 1): "
	).strip()
	listen_from_wav = user_choice == '1' if user_choice in ['1', '2'] else True

	if listen_from_wav:
		default_wav_path = config.WAV_FILE_PATH
		wav_file_path = input(
			f"\n==============================\n"
			"WAV FILE INPUT\n"
			"==============================\n"
			f"Enter the relative path to the WAV file (default: {default_wav_path}): "
		).strip()
		wav_file_path = wav_file_path if wav_file_path else default_wav_path

		logger.debug("Reading audio from WAV file: %s", wav_file_path)
		if not os.path.exists(wav_file_path):
			logger.critical("WAV file not found: %s", wav_file_path)
			sys.exit(1)
		try:
			with wave.open(wav_file_path, 'rb') as wav_file:
				speech_segment = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16).astype(np.float32)
		except Exception as e:
			logger.critical("Failed to read WAV file: %s", e)
			sys.exit(1)
	else:

		vad_model = load_silero_vad(onnx=True)
		if vad_model is None:
			logger.critical("VAD model failed to load.")
			sys.exit(1)

		vad = VADIterator(
			model=vad_model,
			sampling_rate=config.SAMPLING_RATE,
			threshold=config.VAD_THRESHOLD,
			min_silence_duration_ms=config.VAD_MIN_SILENCE_MS
		)

		q = Queue()
		stream = InputStream(
			samplerate=config.SAMPLING_RATE,
			channels=1,
			blocksize=config.CHUNK_SIZE,
			dtype=np.float32,
			callback=create_input_callback(q),
		)

		speech_buffer = np.empty(0, dtype=np.float32)
		recording = False
		start_idx = None
		end_idx = None

		with stream:
			logger.info("Awaiting voice input.")
			while True:
				chunk = q.get()
				if chunk is None or len(chunk) == 0:
					logger.error("Received empty audio chunk from queue.")
					continue

				speech_dict = vad(chunk)
				speech_buffer = np.concatenate((speech_buffer, chunk))

				if speech_dict:
					logger.debug(f"VAD result: {speech_dict}")

					if "start" in speech_dict and not recording:
						recording = True
						start_idx = len(speech_buffer) - len(chunk)
						logger.info("Voice detected. Recording started.")

					elif "end" in speech_dict and recording:
						end_idx = len(speech_buffer)
						logger.debug("End of speech detected. Beginning transcription.")
						break

				if recording and len(speech_buffer) / config.SAMPLING_RATE > config.MAX_SPEECH_SECS:
					end_idx = len(speech_buffer)
					logger.info("Maximum recording duration reached. Beginning transcription.")
					break
		if start_idx is not None and end_idx is not None:
			speech_segment = speech_buffer[int(start_idx * 0.9):int(end_idx * 1.1)]
			logger.debug(f"Recorded audio duration: {len(speech_segment)/config.SAMPLING_RATE:.2f} seconds")
		else:
			logger.warning("No speech was detected.")
			sys.exit(0)

	if config.ENABLE_PLAYBACK:
		logger.info("Playing back recorded audio.")
		sd.play(speech_segment, samplerate=config.SAMPLING_RATE)
		sd.wait()
	transcribed = transcriber(speech_segment.flatten())
	logger.info("Transcription: %s", transcribed)

	if len(transcribed) == 0:
		logger.error("Transcription is empty.")
		sys.exit(1)

ollama_list: ListResponse = ollama.list()
available_models = [m.model for m in ollama_list["models"]]

if config.LLM_MODEL not in available_models:
	logger.info("Model %s not found in the local model list. Pulling from repository.", config.LLM_MODEL)
	try:
		ret = os.system(f"ollama pull {config.LLM_MODEL}")
	except ResponseError as e:
		logger.critical("Failed to pull the model: %s", e)
		sys.exit(1)
	if ret != 0:
		logger.critical("Download unsuccessful.")
		sys.exit(1)

llm_messages = [
	{"role": "system", "content": config.LLM_SYSPROMPT},
	{"role": "user", "content": transcribed}
]

if "granite" in config.LLM_MODEL:
	enable_reasoning_choice = input(
		"\n==============================\n"
		"ENABLE REASONING\n"
		"==============================\n"
		"This model requires reasoning to be explicitly activated. Would you like to enable it?\n"
		"  1. Yes, enable reasoning\n"
		"  2. No, keep it disabled\n"
		"(default is 1): "
	).strip()
	if enable_reasoning_choice != '2':
		llm_messages.insert(0, {"role": "control", "content": "thinking"})
logger.info("Sending input to LLM.")
response: ChatResponse = chat(model=config.LLM_MODEL, messages=llm_messages)

llm_output = response['message']['content']

logger.info("LLM output: \n%s", llm_output)

piper_model = config.PIPER_MODEL_PATH
voice = PiperVoice.load(piper_model)
os.makedirs(os.path.relpath(config.OUTPUT_DIR), exist_ok=True)

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
if output_choice not in ['1', '2', '3', '4']:
	output_choice = '4'

if output_choice in ['1', '3']:
	timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
	default_filename = f"{config.OUTPUT_DIR}/output_{timestamp}.wav"
	filename = input(
		f"\n==============================\n"
		"SAVE OUTPUT\n"
		"==============================\n"
		f"Enter the relative filename to save the output (default: {default_filename}): "
	).strip()
	filename = filename if filename else default_filename
	with wave.open(filename, "w") as wav_file:
		audio = voice.synthesize(llm_output, wav_file)
		wav_file.close()
	logger.info("Audio saved to %s", filename)

if output_choice in ['2', '3']:
	audio = voice.synthesize(llm_output)
	sd.play(audio)
	sd.wait()
	logger.info("Audio playback completed.")