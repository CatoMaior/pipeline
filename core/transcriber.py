import wave
from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
import sys
import numpy as np
import psutil
import json
import time
from .config import Config

class Transcriber:
	def __init__(self, logger=None, model_name=None, return_stats=False):
		try:
			self.audio_duration = -1
			model_name = model_name or Config.TRANSCRIPTION.MOONSHINE_MODEL
			self.model = MoonshineOnnxModel(model_name=model_name)
			self.tokenizer = load_tokenizer()
		except Exception as e:
			if logger:
				logger.error("Failed to initialize transcriber: %s", e)
			sys.exit(1)
		self.logger = logger
		self.return_stats = return_stats

	def __call__(self, audio):
		if len(audio) == 0:
			if self.logger:
				self.logger.warning("Empty audio received for transcription")
			return "[empty audio]"
		try:
			process = psutil.Process()
			before_ram = process.memory_info().rss / (1024 * 1024)

			start_time = time.time()

			tokens = self.model.generate(audio[np.newaxis, :].astype(np.float32))
			transcription = self.tokenizer.decode_batch(tokens)[0]

			end_time = time.time()

			after_ram = process.memory_info().rss / (1024 * 1024)
			ram_usage = after_ram - before_ram

			transcription_time = end_time - start_time
			rtf = transcription_time / self.audio_duration if self.audio_duration > 0 else None

			if self.return_stats:
				return transcription, round(ram_usage, 2), round(rtf, 3)
			return transcription
		except Exception as e:
			if self.logger:
				self.logger.error("Transcription failed: %s", e)
			return "[transcription error]"

	def transcribe_from_file(self, file_path: str) -> str:
		try:
			with wave.open(file_path, "rb") as wav_file:
				self.audio_duration = wav_file.getnframes() / wav_file.getframerate()
			audio = np.memmap(file_path, dtype=np.int16, mode="r")
			return self(audio)
		except Exception as e:
			if self.logger:
				self.logger.error("Failed to read audio file for transcription: %s", e)
			return "[file read error]"

def get_stats(file_path: str) -> dict:
	"""
	Measure RAM usage and real-time factor while transcribing an audio file.
	:param file_path: Path to the audio file to transcribe.
	:return: Dictionary with transcription, RAM usage in MB, and real-time factor.
	"""
	transcriber = Transcriber(return_stats=True)
	transcription, ram, rtf = transcriber.transcribe_from_file(file_path)
	return {
		"transcription": transcription,
		"ram_usage_mb": ram,
		"real_time_factor": rtf
	}

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Transcribe an audio file using MoonshineOnnxModel.")
	parser.add_argument("file_path", type=str, help="Path to the audio file to transcribe.")
	args = parser.parse_args()

	transcriber = Transcriber(return_stats=True)

	stats = get_stats(args.file_path)

	print(json.dumps(stats, indent=4))
