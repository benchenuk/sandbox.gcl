#!/bin/bash
set -e # Exit immediately if a command fails

# --- Configuration ---
# Replace with your remote server's details
REMOTE_USER="remote_user"
REMOTE_HOST="remote_host"

# --- App Details ---
PROJECT_NAME="feeyu"
APP_NAME="context_engine"
REMOTE_APP_DIR="/home/${REMOTE_USER}/apps/${PROJECT_NAME}"
REMOTE_VENV_DIR="/home/${REMOTE_USER}/apps/venv_apps"
ARCHIVE_NAME="${APP_NAME}.tar.gz"
CONFIG_FILE_NAME="ecosystem.config.js"

echo "### Step 1: Creating application archive ###"
# Package the source code, requirements, and production environment file
# IMPORTANT: Ensure you have a '.env.prod' file with your production API keys.
tar -czf ${ARCHIVE_NAME} src requirements.txt .env

echo -e "\n### Step 2: Creating PM2 ecosystem config file ###"
# Create the config file locally before transferring
cat > ${CONFIG_FILE_NAME} << EOF
// ${CONFIG_FILE_NAME}
module.exports = {
  apps: [{
    name: '${PROJECT_NAME}-${APP_NAME}',
    script: 'gunicorn',
    args: '--workers 1 --bind 0.0.0.0:5001 --chdir context_engine/src context_engine:app',
    interpreter: '${REMOTE_VENV_DIR}/bin/python',
    cwd: '${REMOTE_APP_DIR}',
  }]
};
EOF

echo -e "\n### Step 3: Transferring files to ${REMOTE_HOST} ###"
scp ${ARCHIVE_NAME} ${CONFIG_FILE_NAME} ${REMOTE_USER}@${REMOTE_HOST}:/tmp/

echo -e "\n### Step 4: Cleaning up local files ###"
rm ${ARCHIVE_NAME} ${CONFIG_FILE_NAME}

echo -e "\n### Step 5: Deploying on remote host ###"
# The following block of commands is executed on the remote server
ssh -t ${REMOTE_USER}@${REMOTE_HOST} << EOF
  set -e
  echo "--- Setting up application directory ---"
  mkdir -p ${REMOTE_APP_DIR}
  mv /tmp/${ARCHIVE_NAME} /tmp/${CONFIG_FILE_NAME} ${REMOTE_APP_DIR}/${APP_NAME}
  cd ${REMOTE_APP_DIR}/${APP_NAME}

  echo "--- Unpacking application ---"
  tar -xzf ${ARCHIVE_NAME}
  # Rename production env file to the standard .env for the service
  # mv .env.prod .env
  rm ${ARCHIVE_NAME}

  echo "--- Setting up Python virtual environment ---"
  # Create venv if it doesn't exist
  if [ ! -d "${REMOTE_VENV_DIR}" ]; then
    python -m venv ${REMOTE_VENV_DIR}
  fi
  source ${REMOTE_VENV_DIR}/bin/activate
  pip install -r requirements.txt

  echo "--- Setting up PM2 (requires sudo) ---"
  # Install or update PM2 globally using npm
  sudo npm install pm2 -g

  # Start or restart the application based on the ecosystem file
  pm2 startOrRestart ${CONFIG_FILE_NAME}

  # Set up PM2 to start on server boot
  # This generates and configures a systemd service for PM2
  pm2 startup | sudo bash

  # Save the current process list to be resurrected on reboot
  pm2 save

  echo "--- Application Status ---"
  pm2 list

  echo "✅ Deployment to ${REMOTE_HOST} complete."
  echo "Service is running and managed by PM2."
  echo "Run 'pm2 logs ${APP_NAME}' on the server to see logs."
EOF