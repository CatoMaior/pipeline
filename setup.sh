#!/bin/bash

# Clone and build llama.cpp
git clone git@github.com:ggml-org/llama.cpp.git
cd llama.cpp
git checkout b4957
cmake -B build
cmake --build build --config Release -j $(nproc)
cd ..

# Download Piper models
mkdir -p piper-models
wget --quiet --show-progress -O piper-models/en_US-amy-medium.onnx \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true
wget --quiet --show-progress -O piper-models/en_US-amy-medium.onnx.json \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true

# Download LLM models
mkdir -p llm-models
wget --quiet --show-progress -O llm-models/gemma3-1b.gguf \
    https://huggingface.co/unsloth/gemma-3-1b-it-GGUF/resolve/main/gemma-3-1b-it-Q4_K_M.gguf?download=true

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