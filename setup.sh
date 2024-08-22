#!/bin/bash

WORKSPACE=$(pwd)
SERVICES_DIR="${WORKSPACE}/system_services"
SYSTEMCTL_DIR=/etc/systemd/system/

CONFIG_FILE="${WORKSPACE}/config.cfg"
CAST_CONTROLLER_SERVICE=chromecast_controller.service
MEDIA_DRIVE_WEBPAGE_SERVICE=media_drive_as_webpage.service
EDITOR_DRIVE_WEBPAGE_SERVICE=editor_drive_as_webpage.service

CAST_SERVICE="${SERVICES_DIR}/${CAST_CONTROLLER_SERVICE}"
MEDIA_DRIVE_SERVICE="${SERVICES_DIR}/${MEDIA_DRIVE_WEBPAGE_SERVICE}"
EDITOR_DRIVE_SERVICE="${SERVICES_DIR}/${EDITOR_DRIVE_WEBPAGE_SERVICE}"

NPM_PACKAGES_DEST="${WORKSPACE}/static/"
PYTHON_VENV="${WORKSPACE}/.venv"

EXIT_CODE=0

if [[ $EUID -ne 0 ]]; then
    echo "RUN AS ROOT"
    exit 1
fi

install_packages() {
    echo "Install system packages"
    apt update -y && apt install -y sqlite3 ffmpeg npm python3-venv
}

setup_npm_packages() {
    echo "Installing npm packages"
    npm install -g http-server
    cd "${NPM_PACKAGES_DEST}" && npm install
    chown -R "${SUDO_USER}:${SUDO_USER}" "${NPM_PACKAGES_DEST}"
}

create_venv() {
    echo "Creating Python venv"
    # Create virtual environment
    python3 -m venv "${PYTHON_VENV}"
    source "${PYTHON_VENV}/bin/activate"
    # Install requirements
    echo "Installing requirements"
    python3 -m ensurepip --upgrade
    pip install -r "${WORKSPACE}/requirements.txt"
    chown -R "${SUDO_USER}:${SUDO_USER}" "${PYTHON_VENV}"
}

source_config_file() {
    EXIT_CODE=0
    echo "Sourcing config file"
    # Check if config file exists
    if [ $EXIT_CODE -eq 0 ]; then
        if [ -f "${CONFIG_FILE}" ]; then
            # Source the config file
            # shellcheck source=./config.cfg
            source "${CONFIG_FILE}"
            RESULT=$?
            if [ $RESULT != 0 ]; then
                EXIT_CODE=1
                echo "Source of ${CONFIG_FILE} failed, fix file"
            fi
            if [[ -z "${MEDIA_DIR}" ]]; then
                EXIT_CODE=1
                echo "Config file not set, update file param ${CONFIG_FILE}: MEDIA_DIR"
            fi
            if [[ -z "${EDITOR_DIR}" ]]; then
                echo "Editor path not set, ignoring editor"
            fi
        else
            EXIT_CODE=1
            echo "Missing: ${CONFIG_FILE}"
        fi
    fi
    return $EXIT_CODE
}

install_service() {
    sed -i "s,INSTALL_USER,${SUDO_USER},g" "${2}"
    sed -i "s,INSTALL_DIR,${1},g" "${2}"
    cp "${2}" "${SYSTEMCTL_DIR}"
}

run_service() {
    systemctl start "${1}"
    systemctl enable "${1}"
}

install_system_services() {
    echo "Installing services"
    install_service "${WORKSPACE}" "${CAST_SERVICE}"
    install_service "${MEDIA_DIR}" "${MEDIA_DRIVE_SERVICE}"
    if [[ -n "${EDITOR_DIR}" ]]; then
        install_service "${EDITOR_DIR}" "${EDITOR_DRIVE_SERVICE}"
    fi
    systemctl daemon-reload
    run_service "${CAST_CONTROLLER_SERVICE}"
    run_service "${MEDIA_DRIVE_WEBPAGE_SERVICE}"
    if [[ -n "${EDITOR_DIR}" ]]; then
        run_service "${EDITOR_DRIVE_WEBPAGE_SERVICE}"
    fi
}

if [ $EXIT_CODE -eq 0 ]; then
    install_packages
    EXIT_CODE=$?
fi
if [ $EXIT_CODE -eq 0 ]; then
    setup_npm_packages
    EXIT_CODE=$?
fi
if [ $EXIT_CODE -eq 0 ]; then
    create_venv
    EXIT_CODE=$?
fi
if [ $EXIT_CODE -eq 0 ]; then
    source_config_file
    EXIT_CODE=$?
fi
if [ $EXIT_CODE -eq 0 ]; then
    install_system_services
    EXIT_CODE=$?
fi
if [ $EXIT_CODE -ne 0 ]; then
    echo "INSTALL FAILED"
fi
