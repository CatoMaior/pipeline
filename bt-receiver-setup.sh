#!/bin/bash

if [ "$EUID" -ne 0 ]; then
	echo "[!] This script must be run as superuser."
	exit 1
fi

CHANNEL=1
DEVICE=/dev/rfcomm0

echo "[*] Enabling Bluetooth..."
systemctl start bluetooth

echo "[*] Adding RFCOMM Serial Port (SPP) on channel $CHANNEL..."
sdptool add --channel=$CHANNEL SP

echo "[*] Listening for incoming RFCOMM connection..."
rfcomm listen $DEVICE $CHANNEL &
LISTEN_PID=$!

trap "echo '[*] Cleaning up...'; rfcomm release $DEVICE; kill $LISTEN_PID" EXIT
wait $LISTEN_PID
