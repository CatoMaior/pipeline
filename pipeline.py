import logging
import numpy as np
import sounddevice as sd
from queue import Queue
from serial import Serial
from silero_vad import VADIterator, load_silero_vad
from sounddevice import InputStream
from os import path
import re
import subprocess
import sys
import os
import requests
from tqdm import tqdm
import wave

import config
import transcriber
import models

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

logger.info("Starting pipeline.")
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
		os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
		response = requests.get(model_url, stream=True)
		response.raise_for_status()
		total_size = int(response.headers.get('content-length', 0))
		with open(MODEL_PATH, 'wb') as model_file, tqdm(
			total=total_size, unit='B', unit_scale=True, desc="Downloading Model"
		) as progress_bar:
			for chunk in response.iter_content(chunk_size=8192):
				model_file.write(chunk)
				progress_bar.update(len(chunk))
		logger.info("Model downloaded successfully to %s", MODEL_PATH)
	except Exception as e:
		logger.critical("Failed to download the model: %s", e)
		sys.exit(1)

if config.LLM_INFER:
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

if config.LISTEN_FROM_WAV:
	logger.info("Reading audio from WAV file: %s", config.WAV_FILE_PATH)
	if not os.path.exists(config.WAV_FILE_PATH):
		logger.critical("WAV file not found: %s", config.WAV_FILE_PATH)
		sys.exit(1)
	try:
		with wave.open(config.WAV_FILE_PATH, 'rb') as wav_file:
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

if config.LLM_INFER:
	logger.info("Sending transcription to LLM for command generation.")
	stdout, stderr = process.communicate(transcribed)
	process.wait()
	logger.debug("LLM STDERR: %s", stderr.strip())

	match = re.search(r'>\s*(.*?)\s*\[end of text\]', stdout.strip())
	if match:
		command = match.group(1) + "\r"
	else:
		logger.error("Failed to extract LLM output.")
		logger.error("LLM raw output: %s", stdout.strip())
		command = "[error parsing LLM output]"
		sys.exit(1)
else:
	command = transcribed + "\r"

logger.info("Command: %s", command)

if config.WRITE_SERIAL:
	if not os.path.exists(config.SERIAL_PORT):
		logger.critical("Serial port not found: %s. Did you run bt-sender-setup.py?", config.SERIAL_PORT)
		sys.exit(1)
	ser = Serial(config.SERIAL_PORT)
	ser.write(command.encode())
	ser.close()
	logger.info(f"Command sent to {config.SERIAL_PORT}.")
