import time
import os
from questions import questions
import config
from synthesizer import Synthesizer
from transcriber import Transcriber
import logging
import platform
import psutil
import socket
from datetime import datetime

synthesizer = Synthesizer(config.PIPER_MODEL_PATH, f"{config.OUTPUT_DIR}/questions")

total_inference_time = 0
total_audio_duration = 0

for idx, question in enumerate(questions):
    output_path = os.path.join(synthesizer.output_dir, f"question_{idx + 1}.wav")
    start_time = time.time()
    synthesizer.save_output(question, output_path)
    inference_time = time.time() - start_time

    audio_duration = synthesizer.calculate_audio_duration(output_path)

    total_inference_time += inference_time
    total_audio_duration += audio_duration

    print(f"Question {idx + 1}:")
    print(f"  Inference time: {inference_time:.3f} seconds")
    print(f"  Audio duration: {audio_duration:.3f} seconds")
    print(f"  Saved to: {output_path}")

avg_synthesis_rtf = total_inference_time / total_audio_duration if total_audio_duration > 0 else 0
print(f"\nAverage Real-Time Factor (RTF): {avg_synthesis_rtf:.3f}")

transcriber = Transcriber()

audio_files = [f for f in os.listdir(synthesizer.output_dir) if f.endswith(".wav")]
total_transcription_time = 0
total_audio_duration_transcription = 0

for idx, audio_file in enumerate(audio_files):
    audio_path = os.path.join(synthesizer.output_dir, audio_file)
    start_time = time.time()
    transcription = transcriber.transcribe_from_file(audio_path)
    transcription_time = time.time() - start_time

    audio_duration = synthesizer.calculate_audio_duration(audio_path)
    total_transcription_time += transcription_time
    total_audio_duration_transcription += audio_duration

    print(f"Audio {idx + 1}:")
    print(f"  Transcription time: {transcription_time:.3f} seconds")
    print(f"  Audio duration: {audio_duration:.3f} seconds")
    print(f"  Transcription: {transcription}")
    print(f"  File: {audio_path}")

avg_transcription_rtf = total_transcription_time / total_audio_duration_transcription if total_audio_duration_transcription > 0 else 0
print(f"\nAverage Transcription Real-Time Factor (RTF): {avg_transcription_rtf:.3f}")

system_info = (
    f"System Information:\n"
    f"  OS: {platform.system()} {platform.release()} ({platform.version()})\n"
    f"  CPU: {platform.processor()}\n"
    f"  Total Memory: {psutil.virtual_memory().total / (1024 ** 3):.2f} GB\n"
)

recap = (
    "=" * 30 + "\n" +
    "PERFORMANCE RECAP\n" +
    "=" * 30 + "\n" +
    system_info +
    f"Average Synthesis Real-Time Factor (RTF): {avg_synthesis_rtf:.3f}\n" +
    f"Average Transcription Real-Time Factor (RTF): {avg_transcription_rtf:.3f}\n"
)

print(recap)

logs_dir = os.path.join("./performance-logs")
os.makedirs(logs_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
hostname = socket.gethostname()
log_file_path = os.path.join(logs_dir, f"performance_log_{hostname}_{timestamp}.txt")

with open(log_file_path, "w") as log_file:
    log_file.write(recap)
