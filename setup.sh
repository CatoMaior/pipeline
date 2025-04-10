#!/bin/bash

# Parse command-line arguments
ONLY_PYTHON_SETUP=false
for arg in "$@"; do
    case $arg in
        --only-python-setup)
            ONLY_PYTHON_SETUP=true
            shift
            ;;
        *)
            ;;
    esac
done

if [ "$ONLY_PYTHON_SETUP" = false ]; then

    # Download Piper models
    mkdir -p piper-models
    wget --quiet --show-progress -O piper-models/en_US-amy-medium.onnx \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true
    wget --quiet --show-progress -O piper-models/en_US-amy-medium.onnx.json \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true

    mkdir -p llm-models
fi

if ! command -v ollama &> /dev/null; then
	curl -fsSL https://ollama.com/install.sh | sh
	if [ "$EUID" -ne 0 ]; then
		sudo systemctl enable ollama.service
		systemctl start ollama.service
	else
		systemctl enable ollama.service
		systemctl start ollama.service
	fi
fi

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    wget --quiet --show-progress -O /tmp/uv-installer.sh https://astral.sh/uv/install.sh
	chmod +x /tmp/uv-installer.sh
	/tmp/uv-installer.sh --quiet
	source $HOME/.local/bin/env
fi

# Set up Python environment
uv python install 3.11.1
uv venv --python 3.11.1
source .venv/bin/activate
uv pip install -r requirements.txt