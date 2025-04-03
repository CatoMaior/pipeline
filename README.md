# Pipeline Project

This repository contains a pipeline for voice-based command transcription and execution via Bluetooth communication. It listens for speech, processes the transcribed text using an LLM to generate a proper command, and sends the command through a Bluetooth serial connection. Each aspect is customizable, and some features can be disabled via configuration files.

## Dependencies

To use all the features of this project, ensure the following dependencies are installed on your device:
- **Python**: Tested with version 3.13.0
- **uv**: Tested with version 0.6.10
- **Bluetooth Tools**: Includes `rfcomm`, `sdptool`, and `systemctl`. Installation methods vary by distribution.
- **llama.cpp**: Follow the installation instructions provided by the developer [here](https://github.com/ggml-org/llama.cpp/wiki).
- **screen**: Used to visualize data on the serial port. It can typically be installed via your package manager under the name `screen`.

## Usage Instructions

### 1. Clone the Repository
Clone the repository and navigate to its directory:
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Install Python Dependencies
It is recommended to use a virtual environment. Install the required Python packages with:
```bash
uv pip install -r requirements.txt
```

### 3. Configure the Environment
Edit the `config.py` file to adjust the settings to your needs. Detailed explanations of each configuration parameter are provided in `config.py`.

### 4. Set Up Bluetooth
This step is necessary if you configure the pipeline to send commands via Bluetooth serial.

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

### 5. Run the Pipeline
Start the main pipeline script:
```bash
python pipeline.py
```

Logs will be displayed on the standard output. If configured Bluetooth transmission is configured, you can see the received commands on the receiver running `screen /dev/rfcomm0`.
