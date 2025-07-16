#!/bin/bash

# A script to start or reload the Feeyu UI static server on the remote host.
# This script is idempotent and can be run safely multiple times.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# The name for the application process in PM2
readonly PM2_PROCESS_NAME="feeyu-ui"
# The directory on the remote host where your static files are located
readonly APP_DIR="/home/pi/apps/feeyu/ui"
# The port you want the application to be served on
readonly PORT="3000"

# --- Script Logic ---

echo "--> Checking for required commands..."

# 1. Check for 'serve' command, install if not found
if ! command -v serve &> /dev/null; then
    echo "--> 'serve' command not found. Installing globally via npm..."
    # Using 'sudo' as it's a global installation.
    sudo npm install -g serve
    echo "--> 'serve' installed successfully."
else
    echo "--> 'serve' is already installed."
fi

echo "--> Managing the '${PM2_PROCESS_NAME}' application with PM2..."

# 2. Check if the process is already managed by PM2
if pm2 describe "${PM2_PROCESS_NAME}" > /dev/null 2>&1; then
    # If it exists, reload it for a zero-downtime update
    echo "--> Application is already running. Reloading to apply changes..."
    pm2 reload "${PM2_PROCESS_NAME}"
else
    # If it doesn't exist, start it for the first time
    echo "--> Application not found in PM2. Starting it now..."
    # The '--' separates pm2 options from the script's (serve's) options.
    # -s: Serve a single-page app (rewrites all requests to index.html)
    # -l: Listen on a specific port
    pm2 start serve --name "${PM2_PROCESS_NAME}" -- -s "${APP_DIR}" -l "${PORT}"

    # Save the process list so it restarts on server reboot
    echo "--> Saving PM2 process list for startup..."
    pm2 save
fi

echo ""
echo "✅ Success! Application '${PM2_PROCESS_NAME}' is online."
echo "   You can view logs with: pm2 logs ${PM2_PROCESS_NAME}"
echo ""

# Display the final status of all PM2 processes
pm2 list