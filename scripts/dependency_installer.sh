#!/bin/bash
set -e

MISSING=()

check_pkg() {
    local package="$1"
    dpkg -s "$package" >/dev/null 2>&1 || MISSING+=("$package")
    return 0
}
# build deps: liblgpio-dev (lgpio, hx711-rpi-py), swig + libpcsclite-dev (pyscard)
check_pkg liblgpio-dev
check_pkg swig
check_pkg libpcsclite-dev
# runtime deps: pcscd + libccid (NFC readers), network-manager (wifi setup via nmcli)
check_pkg pcscd
check_pkg libccid
check_pkg network-manager

if [[ ${#MISSING[@]} -ne 0 ]]; then
    echo "Installing missing system packages: ${MISSING[*]}"
    sudo apt update
    sudo apt install -y "${MISSING[@]}"
fi

# Check if HX711 C lib is installed
if [[ ! -f /usr/local/include/hx711/common.h ]]; then
    CURRENT_DIR=$(pwd)
    echo "Installing HX711 C library..."
    echo "> need to clone and build from https://github.com/endail/hx711"

    TMP_DIR=$(mktemp -d)
    # Pinned commit so upstream changes cannot break fresh installs.
    # When bumping hx711-rpi-py in pyproject, check if this needs a bump too.
    HX711_COMMIT="ed1da427e61d371b69ccad29f7b816243cd7299d"
    git clone https://github.com/endail/hx711.git "$TMP_DIR"
    cd "$TMP_DIR"
    git checkout --quiet "$HX711_COMMIT"

    make
    sudo make install
    sudo ldconfig
    cd "$CURRENT_DIR" || exit
fi
