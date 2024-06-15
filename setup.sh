#!/bin/bash

WORKSPACE=$(pwd)
SERVICES_DIR="${WORKSPACE}/system_services"
SYSTEMCTL_DIR=/etc/systemd/system/

CONFIG_FILE="${WORKSPACE}/config.cfg"
CHROMECAST_CONTROLLER_SERVICE=chromecast_controller.service
MEDIA_DRIVE_WEBPAGE_SERVICE=media_drive_as_webpage.service

MEDIA_DRIVE_SERVICE="${SERVICES_DIR}/${MEDIA_DRIVE_WEBPAGE_SERVICE}"
SERVER_SERVICE="${SERVICES_DIR}/${CHROMECAST_CONTROLLER_SERVICE}"

NPM_PACKAGES_DEST="${WORKSPACE}/static/"


ERR_CODE=0

if [[ $EUID -ne 0 ]]; then
    echo "RUN AS ROOT"
    exit 1
fi

install_packages() {
    apt update -y && apt install -y sqlite3 ffmpeg npm python3-venv
    # https://nodejs.org/en/download/package-manager
    npm install -g http-server
    python3 -m ensurepip --upgrade
}

setup_npm_packages() {
    cd "${NPM_PACKAGES_DEST}"
    npm install
    cd "${WORKSPACE}"
    chown -R $SUDO_USER:$SUDO_USER "${NPM_PACKAGES_DEST}"
}

source_config_file() {
    # Check if config file exists
    if [ $ERR_CODE -eq 0 ]; then
        if [ -f "${CONFIG_FILE}" ]; then
            # Source the config file
            # shellcheck source=./config.cfg
            source "${CONFIG_FILE}"
            RESULT=$?
            if [ $RESULT != 0 ]; then
                ERR_CODE=1
                echo "Source of ${CONFIG_FILE} failed, fix file"
            fi
            if [[ -z "${MEDIA_DIR}" ]]; then
                ERR_CODE=1
                echo "Config file not set, update file param ${CONFIG_FILE}: MEDIA_DIR"
            fi
        else
            ERR_CODE=1
            echo "Missing: ${CONFIG_FILE}"
        fi
    fi
}

# Install the media drive webpage service and update the media drive dir
install_media_drive_service() {
    sed -i "s,MEDIA_DIR,${MEDIA_DIR},g" "${MEDIA_DRIVE_SERVICE}"
    sed -i "s,INSTALL_USER,${SUDO_USER},g" "${MEDIA_DRIVE_SERVICE}"
    cp "${MEDIA_DRIVE_SERVICE}" "${SYSTEMCTL_DIR}"
}

install_media_server_service() {
    sed -i "s,INSTALL_DIR,${WORKSPACE},g" "${SERVER_SERVICE}"
    sed -i "s,INSTALL_USER,${SUDO_USER},g" "${SERVER_SERVICE}"
    cp "${SERVER_SERVICE}" "${SYSTEMCTL_DIR}"
}

run_service() {
    systemctl start "${1}"
    systemctl enable "${1}"
}

install_system_services() {
    install_media_drive_service
    install_media_server_service
    systemctl daemon-reload
    run_service "${MEDIA_DRIVE_WEBPAGE_SERVICE}"
    run_service "${CHROMECAST_CONTROLLER_SERVICE}"
}

if [ $ERR_CODE -eq 0 ]; then
    setup_npm_packages
fi
if [ $ERR_CODE -eq 0 ]; then
    install_packages
fi
if [ $ERR_CODE -eq 0 ]; then
    source_config_file
fi
if [ $ERR_CODE -eq 0 ]; then
    install_system_services
fi

if [ $ERR_CODE -ne 0 ]; then
    echo "INSTALL FAILED"
fi
