from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
import config
import numpy as np
import sys

class Transcriber:
	def __init__(self, logger, model_name=config.MOONSHINE_MODEL, rate=config.SAMPLING_RATE):
		try:
			self.model = MoonshineOnnxModel(model_name=model_name)
			self.tokenizer = load_tokenizer()
			self.logger = logger
		except Exception as e:
			logger.error("Failed to initialize transcriber: %s", e)
			sys.exit(1)
		self.rate = rate

	def __call__(self, audio):
		if len(audio) == 0:
			self.logger.warning("Empty audio received for transcription")
			return "[empty audio]"
		try:
			tokens = self.model.generate(audio[np.newaxis, :].astype(np.float32))
			return self.tokenizer.decode_batch(tokens)[0]
		except Exception as e:
			self.logger.error("Transcription failed: %s", e)
			return "[transcription error]"