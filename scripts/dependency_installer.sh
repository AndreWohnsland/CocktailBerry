#!/bin/bash
set -e

MISSING=()

check_pkg() {
    local package="$1"
    dpkg -s "$package" >/dev/null 2>&1 || MISSING+=("$package")
    return 0
}
check_pkg liblgpio-dev

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
    git clone https://github.com/endail/hx711.git "$TMP_DIR"
    cd "$TMP_DIR"

    make
    sudo make install
    sudo ldconfig
    cd "$CURRENT_DIR" || exit
fi
