# Pipeline Project

This repository contains a pipeline for voice-based command transcription and execution via Bluetooth communication.

## Dependencies

Ensure the following dependencies are installed:

### System Requirements
- **Python**: Version 3.x
- **Bluetooth Tools**: `rfcomm`, `sdptool`, and `systemctl` for Bluetooth setup
- **ONNX Runtime**: Required for the Silero VAD and Moonshine models
- **SoundDevice**: For audio input and playback
- **Serial Communication**: Python's `pyserial` library
- **llama.cpp**: For LLM inference. Suggested models:
  - [Gemma3-1B-GGUF](https://huggingface.co/pjh64/Gemma3-1B-GGUF/tree/main)
  - [Gemma-3-4b-it-GGUF](https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/tree/main)
  - [Granite-3.2-2b-instruct-GGUF](https://huggingface.co/Mungert/granite-3.2-2b-instruct-GGUF/tree/main)

### Python Packages
Install the required Python packages using:
```bash
pip install -r requirements.txt
```

## Usage Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Configure the Environment
Edit the `config.py` file to adjust settings such as logging level, sampling rate, and model paths.

### 3. Set Up Bluetooth
#### Sender Setup
Run the following script to configure the Bluetooth sender:
```bash
sudo ./bt-sender-setup.sh
```

#### Receiver Setup
Run the following script to configure the Bluetooth receiver:
```bash
sudo ./bt-receiver-setup.sh
```

### 4. Run the Pipeline
Start the main pipeline script:
```bash
python pipeline.py
```

### 5. Output
- Transcriptions will be logged to the console.
- Commands will be sent via the configured serial port (`/dev/rfcomm0`).
