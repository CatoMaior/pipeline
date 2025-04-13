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

	sudo mkdir -p /usr/share/ollama
	sudo setfacl -m u:ollama:rwx /usr/share/ollama
    sudo systemctl daemon-reload
	setfacl -m u:ollama:rwx ~
	setfacl -m u:ollama:rwx $models_path
    sudo systemctl start ollama.service

}

# Function to display help
print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --run-parts=PARTS            For debugging purposes. Specify which parts to run (comma-separated). Options: dependencies, piper, ollama-install, ollama-config, uv, python."
    echo "  --help                       Display this help message."
    exit 0
}

OLLAMA_VERSION="0.6.5"
PYTHON_VERSION="3.11.1"
UV_VERSION="0.6.10"
PYENV_GIT_TAG="97993fcc26999fb9f9d2172afd6914738df274d8"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OLLAMA_DIR=$SCRIPT_DIR/ollama
OLLAMA_MODELS_DIR="$OLLAMA_DIR/models"
UV_CACHE_DIR="$SCRIPT_DIR/.uv-cache"
PYENV_ROOT="$SCRIPT_DIR/.pyenv"
PYENV_EXECUTABLE="$PYENV_ROOT/libexec/pyenv"
PYTHON_EXE="$PYENV_ROOT/versions/$PYTHON_VERSION/bin/python"

# Parse command-line arguments
RUN_PARTS=""
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

if should_run_part "dependencies"; then
    print_message "Installing system dependencies..."
    sudo apt update
    sudo apt install -y g++ cmake libportaudio2 wget curl acl zlib1g zlib1g-dev libssl-dev libbz2-dev libsqlite3-dev
fi

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
    wget -O /tmp/install.sh https://ollama.com/install.sh
	mkdir -p "$OLLAMA_DIR"
    awk '{
        if ($0 ~ /OLLAMA_INSTALL_DIR=\$\(dirname \${BINDIR}\)/)
            print "OLLAMA_INSTALL_DIR=\"'$OLLAMA_DIR'\"";
        else
            print $0;
    }' /tmp/install.sh > /tmp/install.sh.tmp && mv /tmp/install.sh.tmp /tmp/install.sh
    OLLAMA_VERSION=$OLLAMA_VERSION chmod +x /tmp/install.sh
    /tmp/install.sh
	sudo systemctl stop ollama.service
	sudo ln -s "$OLLAMA_DIR/bin/ollama" "$OLLAMA_DIR"
fi

if should_run_part "uv" && ! command -v uv &> /dev/null; then
    print_message "Installing UV..."
    wget -O /tmp/uv-installer.sh https://astral.sh/uv/$UV_VERSION/install.sh
    chmod +x /tmp/uv-installer.sh
	sudo env UV_INSTALL_DIR="/usr/local/bin" /tmp/uv-installer.sh
fi

if should_run_part "python"; then
    print_message "Setting up Python environment..."
	git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT
	cd $PYENV_ROOT
	git checkout $PYENV_GIT_TAG
	cd ..
	PYENV_ROOT=$PYENV_ROOT $PYENV_EXECUTABLE install $PYTHON_VERSION
    mkdir -p "$UV_CACHE_DIR"
    uv venv --python=$PYTHON_EXE
    source .venv/bin/activate
    uv pip install -r requirements.txt --cache-dir "$UV_CACHE_DIR/"
fi

if should_run_part "ollama-config"; then
    mkdir -p "$OLLAMA_MODELS_DIR"
    print_message "Setting OLLAMA_MODELS environment variable to $OLLAMA_MODELS_DIR"
    update_ollama_service "$OLLAMA_MODELS_DIR"
	sleep 1
	print_message "Pulling Ollama model..."
    ollama pull $(python config.py LLM_MODEL)
fi

echo -e "${GREEN}****************************************${NC}"
echo -e "${GREEN}** Setup completed successfully.${NC}"
echo -e "${GREEN}****************************************${NC}"