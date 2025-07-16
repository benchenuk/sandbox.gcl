#!/bin/bash

# Configuration
# Replace with your remote server's details
REMOTE_USER="remote_user"
REMOTE_HOST="remote_host"
REMOTE_DIR="/home/pi/apps/feeyu/ui"
LOCAL_DIR="./dist"
PM2_PROCESS_NAME="feeyu-ui" # The name we gave the process in PM2

# Function to run a command on the remote host
run_remote() {
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "$@"
}

echo "--> Ensuring remote directory exists..."
run_remote "mkdir -p ${REMOTE_DIR}"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create remote directory. Exiting."
    exit 1
fi

echo "--> Copying package.json to build directory..."
cp package.json dist/package.json

echo "--> Copying startup script to build directory..."
cp start_ui.sh dist/start_ui.sh

echo "--> Deploying UI files..."
rsync -avz --progress --delete "${LOCAL_DIR}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
if [ $? -ne 0 ]; then
    echo "Error: Failed to deploy files. Exiting."
    exit 1
fi

echo "--> Reloading the application on the server..."
run_remote "pm2 reload ${PM2_PROCESS_NAME}"
if [ $? -ne 0 ]; then
    echo "Warning: Failed to reload PM2 process. You may need to do it manually."
    # We'll treat this as a warning, not a fatal error.
fi

echo "✅ Deployment completed successfully!"