#!/bin/bash
# cursor_bridge.sh - Local script called by Cursor IDE to run AI tasks on the remote server.

# --- Configuration ---
LAMBDA_HOST="ubuntu@150.136.94.139"
REMOTE_PROJECT_DIR="/opt/cherry-ai"
REMOTE_TEMP_DIR="${REMOTE_PROJECT_DIR}/cursor_temp_files"
# Ensure your local SSH agent is configured or your key is available for passwordless SSH.

# --- Script Arguments ---
AI_COMMAND="$1" # e.g., "review", "design", "optimize"
LOCAL_FILE_PATH="$2" # Absolute path to the local file from Cursor IDE

if [[ -z "$AI_COMMAND" || -z "$LOCAL_FILE_PATH" ]]; then
  echo "Usage: $0 <review|design|optimize> <local_file_path>"
  exit 1
fi

if [[ ! -f "$LOCAL_FILE_PATH" ]]; then
  echo "Error: Local file not found at '$LOCAL_FILE_PATH'"
  exit 1
fi

# --- Logic ---
FILENAME=$(basename "$LOCAL_FILE_PATH")
# Create a unique-ish remote temp file name to avoid collisions if multiple commands run
# A more robust solution might involve UUIDs if this script could be called concurrently.
REMOTE_TEMP_FILE="${REMOTE_TEMP_DIR}/${FILENAME}_$(date +%s)_$$"

# 1. Ensure remote temp directory exists
#    The `|| true` is to prevent script exit if the directory already exists and ssh returns non-zero for that.
ssh "$LAMBDA_HOST" "mkdir -p $REMOTE_TEMP_DIR" || true

# 2. Copy local file to remote server's temp location
scp -q "$LOCAL_FILE_PATH" "$LAMBDA_HOST:$REMOTE_TEMP_FILE"
if [ $? -ne 0 ]; then
  echo "Error: Failed to copy '$LOCAL_FILE_PATH' to server."
  # Attempt to clean up remote temp dir if file copy failed but dir was made
  ssh "$LAMBDA_HOST" "rm -f $REMOTE_TEMP_FILE" || true
  exit 1
fi

# 3. Execute the ai_assist command on the remote server
#    Source .bashrc to ensure environment variables (like API keys) and paths are set.
REMOTE_FULL_COMMAND="cd $REMOTE_PROJECT_DIR && source ~/.bashrc && ai_assist $AI_COMMAND $REMOTE_TEMP_FILE"

# Capture both stdout and stderr, then print them.
# This makes debugging easier if the remote command fails.
OUTPUT=$(ssh "$LAMBDA_HOST" "$REMOTE_FULL_COMMAND" 2>&1)
SSH_EXIT_CODE=$?

# 4. Print the output for Cursor IDE to capture
echo "$OUTPUT"

# 5. Clean up the temporary file on the remote server
ssh "$LAMBDA_HOST" "rm -f $REMOTE_TEMP_FILE" || true

# Exit with the same code as the remote ssh command if it's an error,
# otherwise exit 0 if local operations were fine.
if [ $SSH_EXIT_CODE -ne 0 ]; then
  # Optionally, print a more specific local error message too.
  # echo "Error: Remote command execution failed with exit code $SSH_EXIT_CODE."
  exit $SSH_EXIT_CODE
fi

exit 0 