#!/bin/bash

WORKSPACE=$(pwd)
SERVICES_DIR=${WORKSPACE}/system_services
SYSTEMCTL_DIR=/etc/systemd/system/

CONFIG_FILE=config.cfg
CHROMECAST_CONTROLLER_SERVICE=chromecast_controller.service
MEDIA_DRIVE_WEBPAGE_SERVICE=media_drive_as_webpage.service

ERR_CODE=0

if [[ $EUID -ne 0 ]]; then
    ERR_CODE=1
    echo "RUN AS ROOT"
fi

apt install sqlite3 ffmpeg npm

# Check if services folder exists
if [ $ERR_CODE -eq 0 ] && [ ! -d "${SERVICES_DIR}" ]; then
    ERR_CODE=1
    echo "MISSING: ${SERVICES_DIR}"
fi


if [ $ERR_CODE -eq 0 ]; then
    # https://nodejs.org/en/download/package-manager
    npm install -g http-server
fi

# Check if config file exists
if [ $ERR_CODE -eq 0 ]; then
    if [ -f "$WORKSPACE/$CONFIG_FILE" ]; then
        # Source the config file
        # shellcheck source=./config.cfg
        source "$WORKSPACE/$CONFIG_FILE"
        RESULT=$?
        if [ $RESULT != 0 ]; then
            ERR_CODE=1
            echo "Source of $WORKSPACE/$CONFIG_FILE failed, fix file"
        fi
        if [[ -z "${MEDIA_DIR}" ]]; then
            ERR_CODE=1
            echo "Config file not set, update file param ${CONFIG_FILE}: MEDIA_DIR"
        fi
    else
        ERR_CODE=1
        echo "Missing ${CONFIG_FILE}: ${WORKSPACE}/${CONFIG_FILE}"
    fi
fi

# Install the media drive webpage service and update the media drive dir
if [ $ERR_CODE -eq 0 ]; then
    if [ -f "$SERVICES_DIR/$MEDIA_DRIVE_WEBPAGE_SERVICE" ]; then
        cp "$SERVICES_DIR/$MEDIA_DRIVE_WEBPAGE_SERVICE" $SYSTEMCTL_DIR
        # Update the service workspace to this repo location
        sed -i "s,MEDIA_DIR,${MEDIA_DIR},g" "$SYSTEMCTL_DIR/$MEDIA_DRIVE_WEBPAGE_SERVICE"
    else
        ERR_CODE=1
        echo "MISSING: ${SERVICES_DIR}/${MEDIA_DRIVE_WEBPAGE_SERVICE}"
    fi
fi

# Install the chromecast control service and update the install dir
if [ $ERR_CODE -eq 0 ]; then
    if [ -f "$SERVICES_DIR/$CHROMECAST_CONTROLLER_SERVICE" ]; then
        cp "$SERVICES_DIR/$CHROMECAST_CONTROLLER_SERVICE" $SYSTEMCTL_DIR
        # Update the service workspace to this repo location
        sed -i "s,INSTALL_DIR,${WORKSPACE},g" "$SYSTEMCTL_DIR/$CHROMECAST_CONTROLLER_SERVICE"
    else
        ERR_CODE=1
        echo "MISSING: ${SERVICES_DIR}/${CHROMECAST_CONTROLLER_SERVICE}"
    fi
fi

# Reload the system service
if [ $ERR_CODE -eq 0 ]; then
    systemctl daemon-reload
    RESULT=$?
    if [ $RESULT != 0 ]; then
        ERR_CODE=1
        echo "FAILED TO RESTART SYSTEMCTL: ${RESULT}"
    fi
fi

# Start the media drive webpage
if [ $ERR_CODE -eq 0 ]; then
    systemctl start $MEDIA_DRIVE_WEBPAGE_SERVICE
    RESULT=$?
    if [ $RESULT != 0 ]; then
        ERR_CODE=1
        echo "FAILED TO START $MEDIA_DRIVE_WEBPAGE_SERVICE: ${RESULT}"
    fi
fi

# Enable the media drive webpage
if [ $ERR_CODE -eq 0 ]; then
    systemctl enable $MEDIA_DRIVE_WEBPAGE_SERVICE
    RESULT=$?
    if [ $RESULT != 0 ]; then
        ERR_CODE=1
        echo "FAILED TO ENABLE $MEDIA_DRIVE_WEBPAGE_SERVICE: ${RESULT}"
    fi
fi

# Start the chromecast controller
if [ $ERR_CODE -eq 0 ]; then
    systemctl start $CHROMECAST_CONTROLLER_SERVICE
    RESULT=$?
    if [ $RESULT != 0 ]; then
        ERR_CODE=1
        echo "FAILED TO START $CHROMECAST_CONTROLLER_SERVICE: ${RESULT}"
    fi
fi

# Enable the chromecast controller
if [ $ERR_CODE -eq 0 ]; then
    systemctl enable $CHROMECAST_CONTROLLER_SERVICE
    RESULT=$?
    if [ $RESULT != 0 ]; then
        ERR_CODE=1
        echo "FAILED TO ENABLE $CHROMECAST_CONTROLLER_SERVICE: ${RESULT}"
    fi
fi

if [ $ERR_CODE -ne 0 ]; then
    echo "INSTALL FAILED"
fi
