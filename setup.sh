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
fi

if ! command -v ollama &> /dev/null; then
	wget --quiet --show-progress -O /tmp/installer.sh https://ollama.com/install.sh
	chmod +x /tmp/installer.sh
	/tmp/installer.sh
fi

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    wget --quiet --show-progress -O /tmp/uv-installer.sh https://astral.sh/uv/install.sh
	chmod +x /tmp/uv-installer.sh
	/tmp/uv-installer.sh
fi


# Set up Python environment
uv python install 3.11.1
uv venv --python 3.11.1
source .venv/bin/activate
uv pip install -r requirements.txt

ollama pull $(python config.py LLM_MODEL)