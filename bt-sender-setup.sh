#!/bin/bash

if [ "$EUID" -ne 0 ]; then
	echo "[!] This script must be run as superuser."
	exit 1
fi

# 90:78:41:4D:0E:CB intercapedine
# D8:3A:DD:E4:8F:B0 rpi5
TARGET_MAC="D8:3A:DD:E4:8F:B0"
CHANNEL=1
DEVICE=/dev/rfcomm0

echo "[*] Enabling Bluetooth..."
systemctl start bluetooth

echo "[*] Connecting to $TARGET_MAC on channel $CHANNEL..."
rfcomm connect $DEVICE $TARGET_MAC $CHANNEL &
CONNECT_PID=$!

sleep 5

if [ -e $DEVICE ]; then
    cat $DEVICE
else
    echo "[!] $DEVICE not found. Waiting failed or connection not established."
fi

trap "echo '[*] Cleaning up...'; rfcomm release $DEVICE; kill $CONNECT_PID" EXIT
wait $CONNECT_PID
