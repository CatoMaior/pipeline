import logging
import numpy as np
import sounddevice as sd
from queue import Queue
from silero_vad import VADIterator, load_silero_vad
from sounddevice import InputStream
from os import path
from piper.voice import PiperVoice
import re
import subprocess
import sys
import os
import wave
import datetime

import config
import transcriber
import models
from model_downloader import ModelDownloader

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

if not config.LLM_MODEL in models.supported_models.keys():
	logger.critical("Unsupported model: %s", config.LLM_MODEL)
	logger.critical("Supported models: %s", ", ".join(models.supported_models.keys()))
	logger.critical("Please check the LLM_MODEL field in file config.py.")
	sys.exit(1)

PATH = path.dirname(path.abspath(__file__))
MODEL_PATH = f"{PATH}/{config.LLM_MODEL_DIR}/{config.LLM_MODEL}.gguf"

logger.debug("Starting pipeline.")
logger.debug("Configuration settings:")
for key, value in vars(config).items():
	if not key.startswith("__"):
		logger.debug(f"{key}: {value}")

if not os.path.exists(MODEL_PATH):
	logger.info("Model %s not found locally. Downloading from upstream.", config.LLM_MODEL)
	model_url = models.supported_models.get(config.LLM_MODEL)
	if model_url is None:
		logger.critical("No URL found for the specified model: %s", config.LLM_MODEL)
		sys.exit(1)
	try:
		downloader = ModelDownloader(config.LLM_MODEL, model_url, MODEL_PATH, logger)
		downloader.download()
	except Exception as e:
		logger.critical("Failed to download the model: %s", e)
		sys.exit(1)

process = subprocess.Popen(
	f"{config.LLM_INFER_EXE} -m '{MODEL_PATH}' -sys '{config.LLM_SYSPROMPT}' -st --simple-io",
	stdout=subprocess.PIPE,
	stderr=subprocess.PIPE,
	stdin=subprocess.PIPE,
	text=True,
	shell=True,
)

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

transcriber = transcriber.Transcriber(logger=logger)

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
			process.kill()
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

logger.info("Sending input to LLM.")
stdout, stderr = process.communicate(transcribed)
process.wait()
logger.debug("LLM STDERR: %s", stderr.strip())

match = re.search(r'>\s*(.*?)\s*\[end of text\]', stdout.strip(), re.DOTALL)
if match:
	llm_output = match.group(1) + "\r"
else:
	logger.error("Failed to extract LLM output.")
	logger.error("LLM raw output: %s", stdout.strip())
	llm_output = "[error parsing LLM output]"
	sys.exit(1)

logger.info("LLM output: %s", llm_output)

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