from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
import config
import numpy as np
import sys

class Transcriber:
    def __init__(self, logger=None, model_name=config.MOONSHINE_MODEL, rate=config.SAMPLING_RATE):
        try:
            self.model = MoonshineOnnxModel(model_name=model_name)
            self.tokenizer = load_tokenizer()
        except Exception as e:
            if logger:
                logger.error("Failed to initialize transcriber: %s", e)
            sys.exit(1)
        self.logger = logger
        self.rate = rate

    def __call__(self, audio):
        if len(audio) == 0:
            if self.logger:
                self.logger.warning("Empty audio received for transcription")
            return "[empty audio]"
        try:
            tokens = self.model.generate(audio[np.newaxis, :].astype(np.float32))
            return self.tokenizer.decode_batch(tokens)[0]
        except Exception as e:
            if self.logger:
                self.logger.error("Transcription failed: %s", e)
            return "[transcription error]"

    def transcribe_from_file(self, file_path: str) -> str:
        try:
            audio = np.memmap(file_path, dtype=np.float32, mode="r")
            return self(audio)
        except Exception as e:
            if self.logger:
                self.logger.error("Failed to read audio file for transcription: %s", e)
            return "[file read error]"