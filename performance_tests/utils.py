import os
import platform
from datetime import datetime

def calculate_stats(values, precision=2):
    """Calculate min, max, and average from a list of values"""
    if not values:
        return {"min": 0, "max": 0, "avg": 0}

    return {
        "min": round(min(values), precision),
        "max": round(max(values), precision),
        "avg": round(sum(values) / len(values), precision)
    }

def format_results(test_results, test_runners, disabled_components=None):
    """Format the results as a string"""
    results_string = "Performance Test Results:\n"

    if disabled_components and len(disabled_components) > 0:
        results_string += "\nDisabled Components:\n"
        for component in disabled_components:
            results_string += f"  - {component.replace('_', ' ').capitalize()}\n"

    def format_metric(metric_name, stats):
        metric_info = {
            "ram_usage": ("RAM Usage", "MB"),
            "rtf": ("Real-Time Factor (RTF)", ""),
            "eval_rate": ("Evaluation Rate", "token/s")
        }

        if metric_name not in metric_info:
            return ""

        label, unit = metric_info[metric_name]
        formatted = f"  {label}:\n"

        unit_suffix = f" {unit}" if unit else ""

        formatted += f"    Minimum: {stats['min']}{unit_suffix}\n"
        formatted += f"    Maximum: {stats['max']}{unit_suffix}\n"
        formatted += f"    Average: {stats['avg']}{unit_suffix}\n"

        return formatted

    for test_name, result in test_results.items():
        test = next((t for t in test_runners if t.name == test_name), None)
        if not test:
            continue

        results_string += f"\n{test.display_name}:\n"

        for metric_name, stats in result.items():
            results_string += format_metric(metric_name, stats)

    return results_string

def save_results(results_string):
    """Save results to a log file and create a symlink to the latest results"""
    logs_dir = "./performance_logs"
    os.makedirs(logs_dir, exist_ok=True)

    log_folder_name = platform.node()
    log_folder_path = os.path.join(logs_dir, log_folder_name)
    os.makedirs(log_folder_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"results_{timestamp}.txt"
    log_file_path = os.path.join(log_folder_path, log_file_name)

    with open(log_file_path, "w") as log_file:
        log_file.write(results_string)

    latest_link_path = os.path.abspath(os.path.join(log_folder_path, "latest"))
    if os.path.islink(latest_link_path) or os.path.exists(latest_link_path):
        os.remove(latest_link_path)
    relative_log_file_path = os.path.relpath(log_file_path, log_folder_path)
    os.symlink(relative_log_file_path, latest_link_path)

    return log_file_path
