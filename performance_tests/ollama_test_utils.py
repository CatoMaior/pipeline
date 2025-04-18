import re
import subprocess
import psutil
import threading
import time
import json

def parse_ollama_output(stderr_output):
    """
    Parses the stderr output from the 'ollama run' command to extract metrics.

    Args:
        stderr_output (str): The stderr output string.

    Returns:
        dict: A dictionary containing the extracted metrics.
    """
    metrics = {}
    pattern = r"([\w\s]+):\s+([\d.]+)([a-zA-Z]*)"
    for line in stderr_output.splitlines():
        match = re.match(pattern, line)
        if match:
            key = match.group(1).strip().replace(" ", "_").lower()
            value = float(match.group(2))
            unit = match.group(3)
            metrics[key] = f"{value}{unit}" if unit else value
    return metrics

def run_ollama_command(model_input, model_name):
    """
    Runs LLM inference with ollama on specified model with given input.

    Args:
        model_input (str): The text to pass to the model.
        model_name (str): The name of the model to use.

    Returns:
        dict: A dictionary containing the parsed metrics or an error message.
    """
    command = ["ollama", "run", model_name, "--verbose", model_input]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        stats = parse_ollama_output(result.stderr.strip())
        return stats
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return {"error": e.stderr.strip()}

def get_ram_usage():
    """
    Monitors the RAM usage of LLM inference with ollama.

    Returns:
        float: The maximum RAM usage in MB during the process execution.
    """
    process_name = "ollama"
    max_ram_usage = 0
    while not chat_completed:
        for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
            ram_usage = 0
            if proc.info['name'] != process_name:
                continue
            try:
                cmd = proc.info['cmdline']
                if proc.info['name'].lower() == "ollama" and ("serve" in cmd or "runner" in cmd):
                    p = psutil.Process(proc.info['pid'])
                    mem_rss = p.memory_info().rss / (1024 ** 2)
                    ram_usage += mem_rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if ram_usage > max_ram_usage:
                max_ram_usage = ram_usage
        time.sleep(1)
    return round(max_ram_usage, 2)

def get_stats(model_name, model_input="Hi!"):
    """
    Retrieves statistics for a given model during inference with ollama.

    Args:
        model_name (str): The name of the model to run.
        model_input (str, optional): The input text for the model. Defaults to "Hi!".

    Returns:
        dict: A dictionary containing the model's statistics, including RAM usage.
    """
    global chat_completed, ram_usage
    chat_completed = False
    ram_usage = 0

    thread = threading.Thread(target=lambda: globals().__setitem__('ram_usage', get_ram_usage()))
    thread.start()

    ollama_stats = run_ollama_command(model_input, model_name)

    chat_completed = True
    thread.join()

    ollama_stats["ram_usage_mb"] = ram_usage

    return ollama_stats

if __name__ == "__main__":
    ollama_stats = get_stats("granite3.2:2b")
    print(json.dumps(ollama_stats, indent=4))
