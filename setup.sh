#!/bin/bash

set -e
trap 'echo "Error: Command failed at line $LINENO."' ERR

# Define colors
GREEN='\033[1;32m' # Bold Green
CYAN='\033[1;36m'  # Bold Cyan
NC='\033[0m'       # No Color

# Function to print a highlighted message
print_message() {
    echo -e "${CYAN}****************************************${NC}"
    echo -e "${CYAN}** $1${NC}"
    echo -e "${CYAN}****************************************${NC}"
}

# Function to update systemd service
update_ollama_service() {
    local models_path="$1"
    local service_file="/etc/systemd/system/ollama.service"
    local temp_file="/tmp/ollama.service.tmp"

    print_message "Updating Ollama service file with models path: $models_path"

    if [ ! -f "$service_file" ]; then
        echo "Error: $service_file does not exist."
        exit 1
    fi

    sudo awk -v models_path="$models_path" '
        /RestartSec=3/ {
            print $0
            print "Environment=\"OLLAMA_MODELS=" models_path "\""
            next
        }
        { print $0 }
    ' "$service_file" > "$temp_file"

    sudo mv "$temp_file" "$service_file"
    sudo systemctl daemon-reload
	setfacl -m u:ollama:rwx ~
	setfacl -m u:ollama:rwx $models_path
    sudo systemctl restart ollama.service

}

# Function to display help
print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --run-parts=PARTS            For debugging purposes. Specify which parts to run (comma-separated). Options: piper, ollama-install, ollama-config, uv, python."
    echo "  --help                       Display this help message."
    exit 0
}

# Parse command-line arguments
RUN_PARTS=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OLLAMA_MODELS_DIR="$SCRIPT_DIR/.ollama-models"
UV_CACHE_DIR="$SCRIPT_DIR/.uv-cache"

for arg in "$@"; do
    case $arg in
        --run-parts=*)
            RUN_PARTS="${arg#*=}"
            shift
            ;;
        --help)
            print_help
            ;;
        *)
            echo "Unknown option: $arg"
            print_help
            ;;
    esac
done

# Helper function to check if a part should be run
should_run_part() {
    [[ -z "$RUN_PARTS" || "$RUN_PARTS" == *"$1"* ]]
}

# Request sudo password to update Ollama service
print_message "Requesting sudo access..."
sudo -v
# Keep sudo session alive
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

if should_run_part "piper"; then
    print_message "Downloading Piper models..."
    # Download Piper models
    mkdir -p piper-models
    wget --show-progress -O piper-models/en_US-amy-medium.onnx \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true
    wget --show-progress -O piper-models/en_US-amy-medium.onnx.json \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true
fi

if should_run_part "ollama-install" && ! command -v ollama &> /dev/null; then
    print_message "Installing Ollama..."
    wget --show-progress -O /tmp/installer.sh https://ollama.com/install.sh
    chmod +x /tmp/installer.sh
    /tmp/installer.sh
fi

if should_run_part "uv" && ! command -v uv &> /dev/null; then
    print_message "Installing UV..."
    wget --show-progress -O /tmp/uv-installer.sh https://astral.sh/uv/install.sh
    chmod +x /tmp/uv-installer.sh
	sudo env UV_INSTALL_DIR="/usr/local/bin" /tmp/uv-installer.sh
fi

if should_run_part "python"; then
    print_message "Setting up Python environment..."
    mkdir -p "$UV_CACHE_DIR"
    uv python install 3.11.1 --cache-dir "$UV_CACHE_DIR/"
    uv venv --python 3.11.1 --cache-dir "$UV_CACHE_DIR/"
    source .venv/bin/activate
    uv pip install -r requirements.txt --cache-dir "$UV_CACHE_DIR/"
fi

if should_run_part "ollama-config"; then
    mkdir -p "$OLLAMA_MODELS_DIR"
    print_message "Setting OLLAMA_MODELS environment variable to $OLLAMA_MODELS_DIR"
    update_ollama_service "$OLLAMA_MODELS_DIR"
    ollama pull $(python config.py LLM_MODEL)
fi

echo -e "${GREEN}****************************************${NC}"
echo -e "${GREEN}** Setup completed successfully.${NC}"
echo -e "${GREEN}****************************************${NC}"