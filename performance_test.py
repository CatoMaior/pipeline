from synthesizer import measure_ram as get_synth_ram
from transcriber import measure_ram as get_trans_ram
from evaluation_texts import texts
import os
import time
from tqdm import tqdm
import librosa
import platform
from datetime import datetime

output_dir = "./performance_test_outputs"
os.makedirs(output_dir, exist_ok=True)

metrics = {
    "piper": {"ram_usages": [], "rtf_values": [], "process_func": get_trans_ram},
    "moonshine": {"ram_usages": [], "rtf_values": [], "process_func": get_synth_ram},
}

dry_run_file = "input.wav"
if os.path.exists(dry_run_file):
    print("Heating up the system...")
    metrics["moonshine"]["process_func"]("Dry run text", dry_run_file)
    metrics["piper"]["process_func"](dry_run_file)
    print("Starting performance test...")

for idx, text in enumerate(tqdm(texts, desc="Processing texts")):
    output_file = os.path.join(output_dir, f"text_{idx + 1}.wav")

    start_time = time.time()
    synth_result = metrics["moonshine"]["process_func"](text, output_file)
    synth_duration = time.time() - start_time
    audio_duration = librosa.get_duration(path=output_file)
    metrics["moonshine"]["rtf_values"].append(synth_duration / audio_duration)
    metrics["moonshine"]["ram_usages"].append(synth_result["ram_usage_mb"])

    start_time = time.time()
    trans_result = metrics["piper"]["process_func"](output_file)
    trans_duration = time.time() - start_time
    metrics["piper"]["rtf_values"].append(trans_duration / audio_duration)
    metrics["piper"]["ram_usages"].append(trans_result["ram_usage_mb"])

results = {}
for key, data in metrics.items():
    results[key] = {
        "ram_usage": {
            "min_mb": round(min(data["ram_usages"]), 2),
            "max_mb": round(max(data["ram_usages"]), 2),
            "avg_mb": round(sum(data["ram_usages"]) / len(data["ram_usages"]), 2),
        },
        "rtf": {
            "min": round(min(data["rtf_values"]), 3),
            "max": round(max(data["rtf_values"]), 3),
            "avg": round(sum(data["rtf_values"]) / len(data["rtf_values"]), 3),
        },
    }

logs_dir = "./performance-logs"
os.makedirs(logs_dir, exist_ok=True)

log_folder_name = platform.node()
log_folder_path = os.path.join(logs_dir, log_folder_name)
os.makedirs(log_folder_path, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f"results_{timestamp}.txt"
log_file_path = os.path.join(log_folder_path, log_file_name)

results_string = "Performance Test Results:\n"
for key, data in results.items():
    results_string += f"\n{key.capitalize()}:\n"
    results_string += "  RAM Usage (MB):\n"
    results_string += f"    Minimum: {data['ram_usage']['min_mb']} MB\n"
    results_string += f"    Maximum: {data['ram_usage']['max_mb']} MB\n"
    results_string += f"    Average: {data['ram_usage']['avg_mb']} MB\n"
    results_string += "  Real-Time Factor (RTF):\n"
    results_string += f"    Minimum: {data['rtf']['min']}\n"
    results_string += f"    Maximum: {data['rtf']['max']}\n"
    results_string += f"    Average: {data['rtf']['avg']}\n"

print(results_string)

log_file_path_txt = os.path.join(log_folder_path, log_file_name)
with open(log_file_path_txt, "w") as log_file:
    log_file.write(results_string)

print(f"\nResults saved to: {log_file_path_txt}")

latest_link_path = os.path.join(log_folder_path, "latest")
if os.path.islink(latest_link_path) or os.path.exists(latest_link_path):
    os.remove(latest_link_path)
os.symlink(log_file_path_txt, latest_link_path)
