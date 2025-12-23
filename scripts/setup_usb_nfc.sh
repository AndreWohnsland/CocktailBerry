#!/bin/bash

echo "installing nfc reader dependencies..."
sudo apt-get update
sudo apt-get install -y pcscd libccid pcsc-tools swig libpcsclite-dev
sudo systemctl enable --now pcscd

echo "configuring pcscd to run without polkit, this is needed for NFC readers to work properly..."
if grep -Eq '^\s*#?\s*PCSCD_ARGS=' /etc/default/pcscd; then
  sudo sed -i 's|^\s*#\?\s*PCSCD_ARGS=.*|PCSCD_ARGS=--disable-polkit|' /etc/default/pcscd
else
  echo 'PCSCD_ARGS=--disable-polkit' | sudo tee -a /etc/default/pcscd >/dev/null
fi 