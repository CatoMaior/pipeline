import wave
import os
import json
import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice

class Synthesizer:
	def __init__(self, model_path: str, output_dir: str):
		self.voice = PiperVoice.load(model_path)
		self.output_dir = output_dir
		os.makedirs(os.path.relpath(output_dir), exist_ok=True)
		with open(f"{model_path}.json", "r") as model_config_file:
			piper_config = json.load(model_config_file)
			self.sample_rate = piper_config["audio"]["sample_rate"]

	def save_output(self, text: str, filename: str):
		with wave.open(filename, "w") as wav_file:
			self.voice.synthesize(text, wav_file)

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
