import os
import numpy as np
import sounddevice as sd
from queue import Queue
from silero_vad import VADIterator, load_silero_vad
from sounddevice import InputStream
from core import Config

class AudioHandler:
    """Handles audio input operations (file loading and microphone recording)."""

    def __init__(self, logger):
        """Initialize the audio handler."""
        self.logger = logger

    def create_input_callback(self, q):
        """Create a callback function for audio input stream."""
        def callback(indata, frames, time_info, status):
            if status:
                self.logger.warning(f"Input stream status: {status}")
            if indata is not None:
                q.put(indata.copy().flatten())
            else:
                self.logger.error("No input data received in callback")
        return callback

    def load_from_wav(self, wav_file_path):
        """Load audio data from a WAV file."""
        self.logger.debug(f"Reading audio from WAV file: {wav_file_path}")

        if not os.path.exists(wav_file_path):
            self.logger.critical(f"WAV file not found: {wav_file_path}")
            return None

        try:
            return np.memmap(wav_file_path, dtype=np.int16, mode="r")
        except Exception as e:
            self.logger.critical(f"Failed to read WAV file: {e}")
            return None

    def record_from_microphone(self):
        """Record audio from the microphone using Voice Activity Detection."""
        try:
            # Load VAD model
            vad_model = load_silero_vad(onnx=True)
            if vad_model is None:
                self.logger.critical("VAD model failed to load.")
                return None

            vad = VADIterator(
                model=vad_model,
                sampling_rate=Config.AUDIO.SAMPLING_RATE,
                threshold=Config.AUDIO.VAD_THRESHOLD,
                min_silence_duration_ms=Config.AUDIO.VAD_MIN_SILENCE_MS
            )

            # Set up audio input stream
            q = Queue()
            stream = InputStream(
                samplerate=Config.AUDIO.SAMPLING_RATE,
                channels=1,
                blocksize=Config.AUDIO.CHUNK_SIZE,
                dtype=np.float32,
                callback=self.create_input_callback(q),
            )

            # Start recording
            speech_buffer = np.empty(0, dtype=np.float32)
            recording = False
            start_idx = None
            end_idx = None

            with stream:
                self.logger.debug("Awaiting voice input.")
                while True:
                    chunk = q.get()
                    if chunk is None or len(chunk) == 0:
                        self.logger.error("Received empty audio chunk from queue.")
                        continue

                    speech_dict = vad(chunk)
                    speech_buffer = np.concatenate((speech_buffer, chunk))

                    if speech_dict:
                        self.logger.debug(f"VAD result: {speech_dict}")

                        if "start" in speech_dict and not recording:
                            recording = True
                            start_idx = len(speech_buffer) - len(chunk)
                            self.logger.debug("Voice detected. Recording started.")

                        elif "end" in speech_dict and recording:
                            end_idx = len(speech_buffer)
                            self.logger.debug("End of speech detected. Beginning transcription.")
                            break

                    if recording and len(speech_buffer) / Config.AUDIO.SAMPLING_RATE > Config.AUDIO.MAX_SPEECH_SECS:
                        end_idx = len(speech_buffer)
                        self.logger.debug("Maximum recording duration reached. Beginning transcription.")
                        break

            # Process the recorded audio
            if start_idx is not None and end_idx is not None:
                speech_segment = speech_buffer[int(start_idx * 0.9):int(end_idx * 1.1)]
                self.logger.debug(f"Recorded audio duration: {len(speech_segment)/Config.AUDIO.SAMPLING_RATE:.2f} seconds")
                return speech_segment
            else:
                self.logger.warning("No speech was detected.")
                return None

        except Exception as e:
            self.logger.error(f"Error recording from microphone: {e}")
            return None

    def play_audio(self, audio_data):
        """Play audio data."""
        try:
            self.logger.debug("Playing back recorded audio.")
            sd.play(audio_data, samplerate=Config.AUDIO.SAMPLING_RATE)
            sd.wait()
            return True
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            return False
