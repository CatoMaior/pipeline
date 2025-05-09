#!/bin/bash

set -e
trap 'echo "Error: Command failed at line $LINENO."' ERR

# Define colors
GREEN='\033[1;32m' # Bold Green
CYAN='\033[1;36m'  # Bold Cyan
DEFAULT='\033[0m'       # No Color

print_message() {
	echo -e "${CYAN}****************************************${DEFAULT}"
	echo -e "${CYAN}** $1${DEFAULT}"
	echo -e "${CYAN}****************************************${DEFAULT}"
}

allow_traversal() {
	local path="$1"
	local current_path=""
	IFS='/' read -ra steps <<< "$path"
	for step in "${steps[@]}"; do
		current_path="$current_path/$step"
		sudo chmod +x "$current_path"
	done
}

update_ollama_service() {
	local models_path="$1"
	local service_file="/etc/systemd/system/ollama.service"
	local temp_file="/tmp/ollama.service.tmp"

	if [ ! -f "$service_file" ]; then
		echo "Error: $service_file does not exist."
		exit 1
	fi

	if grep -q "Environment=\"OLLAMA_MODELS=" "$service_file"; then
		echo "OLLAMA_MODELS is already set in $service_file. Skipping update."
	else
		sudo awk -v models_path="$models_path" '
			/RestartSec=3/ {
				print $0
				print "Environment=\"OLLAMA_MODELS=" models_path "\""
				next
			}
			{ print $0 }
		' "$service_file" > "$temp_file"

		sudo mv "$temp_file" "$service_file"
	fi

	allow_traversal "$models_path"
	sudo mkdir -p /usr/share/ollama
	allow_traversal /usr/share/ollama
	sudo systemctl daemon-reload
	sudo systemctl start ollama.service

}

print_help() {
	echo "Usage: $0 [OPTIONS]"
	echo "Options:"
	echo "  --run-parts=PARTS            Specify which parts to run (comma-separated). Options:"
	echo "                                dependencies    - Install system dependencies."
	echo "                                submodules      - Download and initialize git submodules."
	echo "                                piper           - Download Piper models."
	echo "                                ollama-install  - Install the Ollama application."
	echo "                                ollama-config   - Configure Ollama service and pull models."
	echo "                                uv              - Install the UV tool."
	echo "                                python-install  - Install Python using pyenv."
	echo "                                python-config   - Configure the Python environment."
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

should_run_part() {
	[[ -z "$RUN_PARTS" || "$RUN_PARTS" == *"$1"* ]]
}

print_message "Requesting sudo access..."
sudo -v
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

if should_run_part "dependencies"; then
	print_message "Installing system dependencies..."
	sudo apt update
	sudo apt install -y git-lfs g++ cmake libportaudio2 wget curl acl zlib1g build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
fi

if should_run_part "submodules"; then
	print_message "Downloading submodules..."
	git lfs install
	git submodule init
	git submodule update --init --recursive
fi

if should_run_part "piper"; then
	print_message "Downloading Piper models..."
	mkdir -p piper_models
	if [ ! -f "piper_models/en_US-amy-medium.onnx" ]; then
		wget -O piper_models/en_US-amy-medium.onnx \
			https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true
	fi
	if [ ! -f "piper_models/en_US-amy-medium.onnx.json" ]; then
		wget -O piper_models/en_US-amy-medium.onnx.json \
			https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true
	fi
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
	allow_traversal $OLLAMA_DIR
	sudo setfacl -R -m u:ollama:rwx $OLLAMA_DIR
	sudo systemctl stop ollama.service
	sudo ln -s "$OLLAMA_DIR/bin/ollama" "$OLLAMA_DIR"
fi

if should_run_part "uv" && ! command -v uv &> /dev/null; then
	print_message "Installing UV..."
	wget -O /tmp/uv-installer.sh https://astral.sh/uv/$UV_VERSION/install.sh
	chmod +x /tmp/uv-installer.sh
	sudo env UV_INSTALL_DIR="/usr/local/bin" /tmp/uv-installer.sh
fi

if should_run_part "python-install"; then
	print_message "Installing Python..."
	git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT
	cd $PYENV_ROOT
	git checkout $PYENV_GIT_TAG
	cd ..
	PYENV_ROOT=$PYENV_ROOT $PYENV_EXECUTABLE install $PYTHON_VERSION
fi

if should_run_part "python-config"; then
	print_message "Configuring Python environment..."
	mkdir -p "$UV_CACHE_DIR"
	uv venv --python=$PYTHON_EXE
	source .venv/bin/activate
	uv pip install -r requirements.txt --cache-dir "$UV_CACHE_DIR/"
fi

if should_run_part "ollama-config"; then
	mkdir -p "$OLLAMA_MODELS_DIR"
	print_message "Configuring Ollama service..."
	update_ollama_service "$OLLAMA_MODELS_DIR"
	sleep 1
	print_message "Pulling Ollama model..."
	ollama pull $(python -c "from core.config import Config; print(Config.LLM.MODEL)")
fi

git update-index --assume-unchanged wav_performance_tests/*

print_message "Setup completed successfully"