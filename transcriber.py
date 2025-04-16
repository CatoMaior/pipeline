from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
import config
import numpy as np
import sys
import psutil
import json

class Transcriber:
	def __init__(self, logger=None, model_name=config.MOONSHINE_MODEL, return_ram_usage=False):
		try:
			self.model = MoonshineOnnxModel(model_name=model_name)
			self.tokenizer = load_tokenizer()
		except Exception as e:
			if logger:
				logger.error("Failed to initialize transcriber: %s", e)
			sys.exit(1)
		self.logger = logger
		self.return_ram_usage = return_ram_usage

	def __call__(self, audio):
		if len(audio) == 0:
			if self.logger:
				self.logger.warning("Empty audio received for transcription")
			return "[empty audio]"
		try:
			process = psutil.Process()
			before_ram = process.memory_info().rss / (1024 * 1024)

			tokens = self.model.generate(audio[np.newaxis, :].astype(np.float32))
			transcription = self.tokenizer.decode_batch(tokens)[0]

			after_ram = process.memory_info().rss / (1024 * 1024)
			ram_usage = after_ram - before_ram

			if self.return_ram_usage:
				return transcription, round(ram_usage, 2)
			return transcription
		except Exception as e:
			if self.logger:
				self.logger.error("Transcription failed: %s", e)
			return "[transcription error]"

	def transcribe_from_file(self, file_path: str) -> str:
		try:
			audio = np.memmap(file_path, dtype=np.int16, mode="r")
			return self(audio)
		except Exception as e:
			if self.logger:
				self.logger.error("Failed to read audio file for transcription: %s", e)
			return "[file read error]"

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Transcribe an audio file using MoonshineOnnxModel.")
	parser.add_argument("file_path", type=str, help="Path to the audio file to transcribe.")
	args = parser.parse_args()

	transcriber = Transcriber(return_ram_usage=True)

	transcription, ram = transcriber.transcribe_from_file(args.file_path)

	output = {
		"transcription": transcription,
		"ram_usage_mb": ram
	}

	print(json.dumps(output, indent=4))