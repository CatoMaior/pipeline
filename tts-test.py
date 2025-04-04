import wave
from piper.voice import PiperVoice

model = "./piper-models/en_US-amy-medium.onnx"
voice = PiperVoice.load(model)
text = "This is an example of text to speech"
wav_file = wave.open("output.wav", "w")
audio = voice.synthesize(text, wav_file)