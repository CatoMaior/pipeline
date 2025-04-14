# Pipeline Project

This repository contains an interactive pipeline for voice transcription, local LLM interrogation, and output speech generation. Here is a flowchart of the pipeline:
![Pipeline Flowchart](pipeline.png)
Piper models downloaded from https://huggingface.co/rhasspy/piper-voices.

## Usage instructions

### 1. Install dependencies
To install this project you need `git`, `g++`, `cmake` and `acl`. On Debian-based distributions you can install them with:
```
sudo apt update
sudo apt install git
```

### 2. Clone the Repository
Clone the repository and navigate to its directory:
```
git clone git@github.com:CatoMaior/pipeline.git
cd pipeline
```

### 3. Run setup script
Run the setup script. It creates a virtual environment and installs the dependencies.
```
./setup.sh
```

### 4. Run the Pipeline
Activate the virtual environment:
```
source .venv/bin/activate
```
Start the main pipeline script:
```
python pipeline.py
```
You can customize the pipeline by modifying parameters in the `config.py` file. All parameters are thoroughly documented within the file.

## Performance Tests

After activating the virtual environment as in the previous section, run `performance_tests.py` to evaluate the pipeline components' performance:
```
python performance_tests.py
```
The results are logged to the console and saved in the `performance-logs` directory. The log file is named with the format `performance_log_<hostname>_<timestamp>.txt`, where `<hostname>` is the machine's hostname and `<timestamp>` is the current date and time.