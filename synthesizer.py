import wave
import os
import json
import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
import psutil
import argparse
from config import PIPER_MODEL_PATH
import time

class Synthesizer:
	def __init__(self, model_path: str):
		self.voice = PiperVoice.load(model_path)
		with open(f"{model_path}.json", "r") as model_config_file:
			piper_config = json.load(model_config_file)
			self.sample_rate = piper_config["audio"]["sample_rate"]

	def save_output(self, text: str, filename: str):
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
		with wave.open(filename, "rb") as wav_file:
			audio_data = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)
			sd.play(audio_data, samplerate=wav_file.getframerate())
			sd.wait()

	def play_raw_output(self, text: str):
		raw_audio = b''.join(self.voice.synthesize_stream_raw(text))
		audio = np.frombuffer(raw_audio, dtype=np.int16)
		sd.play(audio, samplerate=self.sample_rate)
		sd.wait()

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
	synthesizer = Synthesizer(PIPER_MODEL_PATH)
	stats = synthesizer.save_output(text, output_file)
	stats["output_file"] = output_file,
	return stats

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Synthesize speech from text using PiperVoice.")
	parser.add_argument("text", type=str, help="Text to synthesize.")
	parser.add_argument("-o", "--output_file", type=str, help="Path to save the synthesized audio file.", default=None)
	args = parser.parse_args()

	stats = get_stats(args.text, args.output_file)
	print(json.dumps(stats, indent=4))
