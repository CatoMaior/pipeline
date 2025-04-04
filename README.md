# Pipeline Project

This repository contains a pipeline for voice-based command transcription and execution. It listens for speech, processes the transcribed text using an LLM to generate a proper command. Each aspect is customizable, and some features can be disabled via configuration files.

## Dependencies

To use all the features of this project, ensure the following dependencies are installed on your device:
- **Python**: Tested with version 3.13.0
- **uv**: Tested with version 0.6.10
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

### 4. Run the Pipeline
Start the main pipeline script:
```bash
python pipeline.py
```

Logs will be displayed on the standard output.
