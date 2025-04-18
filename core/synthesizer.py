import wave
import os
import json
import numpy as np
import sounddevice as sd
import psutil
import argparse
import time
from .config import Config

class Synthesizer:
	def __init__(self, model_path: str):
		self.model_path = model_path
		self.voice = None
		self.sample_rate = 16000  # Default sample rate
		self._initialized = False

	def _initialize_if_needed(self):
		"""Initialize the PiperVoice model if it hasn't been initialized yet."""
		if self._initialized:
			return True

		try:
			# Only import Piper when we need it
			from piper.voice import PiperVoice
			self.voice = PiperVoice.load(self.model_path)
			with open(f"{self.model_path}.json", "r") as model_config_file:
				piper_config = json.load(model_config_file)
				self.sample_rate = piper_config["audio"]["sample_rate"]
			self._initialized = True
			return True
		except Exception as e:
			if hasattr(self, 'logger') and self.logger:
				self.logger.error(f"Error initializing Piper: {e}")
			return False

	def save_output(self, text: str, filename: str):
		if not self._initialize_if_needed():
			return {"error": "Failed to initialize Piper", "output_file": filename}

		try:
			os.makedirs(os.path.dirname(filename), exist_ok=True)

			process = psutil.Process()
			before_ram = process.memory_info().rss / (1024 * 1024)

			start_time = time.time()

			with wave.open(filename, "w") as wav_file:
				self.voice.synthesize(text, wav_file)

			end_time = time.time()

			after_ram = process.memory_info().rss / (1024 * 1024)
			ram_usage = after_ram - before_ram

			audio_duration = self.calculate_audio_duration(filename)
			synthesis_time = end_time - start_time
			rtf = synthesis_time / audio_duration if audio_duration > 0 else float('inf')

			return {
				"ram_usage_mb": round(ram_usage, 2),
				"real_time_factor": round(rtf, 3)
			}
		except Exception as e:
			if hasattr(self, 'logger') and self.logger:
				self.logger.error("Synthesis failed: %s", e)
			raise

	def play_output(self, filename: str):
		try:
			with wave.open(filename, "rb") as wav_file:
				audio_data = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)
				sd.play(audio_data, samplerate=wav_file.getframerate())
				sd.wait()
		except Exception as e:
			if hasattr(self, 'logger') and self.logger:
				self.logger.error(f"Error playing audio: {e}")

	def play_raw_output(self, text: str):
		if not self._initialize_if_needed():
			if hasattr(self, 'logger') and self.logger:
				self.logger.error("Failed to initialize Piper")
			return False

		try:
			raw_audio = b''.join(self.voice.synthesize_stream_raw(text))
			audio = np.frombuffer(raw_audio, dtype=np.int16)
			sd.play(audio, samplerate=self.sample_rate)
			sd.wait()
			return True
		except Exception as e:
			if hasattr(self, 'logger') and self.logger:
				self.logger.error(f"Error in raw audio playback: {e}")
			return False

	def calculate_audio_duration(self, file_path: str) -> float:
		with wave.open(file_path, "rb") as wav_file:
			return wav_file.getnframes() / wav_file.getframerate()

def get_stats(text: str, output_file: str) -> dict:
	"""
	Measure RAM usage while synthesizing speech from text.
	:param text: Text to synthesize.
	:param output_file: Path to save the synthesized audio file.
	:return: Dictionary with output file path and RAM usage in MB.
	"""
	try:
		synthesizer = Synthesizer(Config.SYNTHESIS.PIPER_MODEL_PATH)
		stats = synthesizer.save_output(text, output_file)
		stats["output_file"] = output_file,
		return stats
	except Exception as e:
		return {"error": str(e), "output_file": output_file}

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Synthesize speech from text using PiperVoice.")
	parser.add_argument("text", type=str, help="Text to synthesize.")
	parser.add_argument("-o", "--output_file", type=str, help="Path to save the synthesized audio file.", default=None)
	args = parser.parse_args()

	stats = get_stats(args.text, args.output_file)
	print(json.dumps(stats, indent=4))
