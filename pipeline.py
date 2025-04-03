import logging
import numpy as np
import sounddevice as sd
from queue import Queue
from serial import Serial
from silero_vad import VADIterator, load_silero_vad
from sounddevice import InputStream
import re
import subprocess
import sys
import os

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

if not os.path.exists(f"{config.PATH}/{config.LLM_MODEL}"):
	logger.critical("Model file not found at path: %s", f"{config.PATH}/{config.LLM_MODEL}")
	sys.exit(1)

if config.LLM_INFER:
	process = subprocess.Popen(
		f"{config.LLM_INFER_EXE} -m '{config.PATH}/{config.LLM_MODEL}' -sys '{config.LLM_SYSPROMPT}' -st --simple-io",
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
	if config.PLAY_RECORDING:
		logger.info("Playing back recorded audio.")
		sd.play(speech_segment, samplerate=config.SAMPLING_RATE)
		sd.wait()
	transcribed = transcriber(speech_segment.flatten())
	logger.info("Transcription: %s", transcribed)
else:
	logger.warning("No speech was detected.")
	process.kill()
	sys.exit(0)

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
