import os
import platform
from datetime import datetime

def calculate_stats(values):
    """Calculate min, max, and average from a list of values"""
    if not values:
        return {"min": 0, "max": 0, "avg": 0}

    return {
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "avg": round(sum(values) / len(values), 3)
    }

def format_results(test_results, test_runners):
    """Format the results as a string"""
    results_string = "Performance Test Results:\n"

    for test_name, result in test_results.items():
        test = next((t for t in test_runners if t.name == test_name), None)
        if not test:
            continue

        results_string += f"\n{test.display_name}:\n"

        for metric_name, stats in result.items():
            if metric_name == "ram_usage":
                results_string += f"  RAM Usage:\n"
                results_string += f"    Minimum: {stats['min']} MB\n"
                results_string += f"    Maximum: {stats['max']} MB\n"
                results_string += f"    Average: {stats['avg']} MB\n"
            elif metric_name == "rtf":
                results_string += f"  Real-Time Factor (RTF):\n"
                results_string += f"    Minimum: {stats['min']}\n"
                results_string += f"    Maximum: {stats['max']}\n"
                results_string += f"    Average: {stats['avg']}\n"
            elif metric_name == "eval_rate":
                results_string += f"  Evaluation Rate:\n"
                results_string += f"    Minimum: {stats['min']} token/s\n"
                results_string += f"    Maximum: {stats['max']} token/s\n"
                results_string += f"    Average: {stats['avg']} token/s\n"

    return results_string

def save_results(results_string):
    """Save results to a log file and create a symlink to the latest results"""
    logs_dir = "./performance-logs"
    os.makedirs(logs_dir, exist_ok=True)

    log_folder_name = platform.node()
    log_folder_path = os.path.join(logs_dir, log_folder_name)
    os.makedirs(log_folder_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"results_{timestamp}.txt"
    log_file_path = os.path.join(log_folder_path, log_file_name)

    with open(log_file_path, "w") as log_file:
        log_file.write(results_string)

    print(f"\nResults saved to: {log_file_path}")

    latest_link_path = os.path.abspath(os.path.join(log_folder_path, "latest"))
    if os.path.islink(latest_link_path) or os.path.exists(latest_link_path):
        os.remove(latest_link_path)
    relative_log_file_path = os.path.relpath(log_file_path, log_folder_path)
    os.symlink(relative_log_file_path, latest_link_path)

    return log_file_path
