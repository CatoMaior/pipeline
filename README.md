# Pipeline Project

This repository contains an interactive pipeline for voice transcription, local LLM interrogation, and output speech generation.

## Usage instructions

### 1. Install dependencies
To install this project you need `git`, `g++` and `cmake`. On Debian-based distributions you can install them with:
```
sudo apt update
sudo apt install git g++ cmake libportaudio2 wget
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
Start the main pipeline script:
```
source $HOME/.local/bin/env .venv/bin/activate
python pipeline.py
```
You can customize the pipeline by modifying parameters in the `config.py` file. All parameters are thoroughly documented within the file.
