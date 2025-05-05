#!/bin/bash

# Script to launch a remote IDE on a Cloud Workstation

set -e

# Source the authentication script
source ./authenticate_codespaces.sh

# Function to get available workstations
get_workstations() {
  gcloud workstations workstations list --format="json"
}

# Function to prompt the user to choose an IDE
choose_ide() {
  echo "Choose an IDE to launch:"
  echo "1. IntelliJ"
  echo "2. JupyterLab"
  read -p "Enter your choice (1 or 2): " ide_choice

  case $ide_choice in
    1)
      echo "Launching IntelliJ..."
      IDE="intellij"
      ;;
    2)
      echo "Launching JupyterLab..."
      IDE="jupyterlab"
      ;;
    *)
      echo "Invalid choice."
      exit 1
      ;;
  esac
}

# Main function
main() {
  # Get available workstations
  workstations=$(get_workstations)

  # Check if any workstations are available
  if [ -z "$workstations" ]; then
    echo "No workstations available."
    exit 1
  fi

  # Prompt the user to choose an IDE
  choose_ide

  # Establish SSH tunnel and launch VS Code
  # (Implementation details will depend on the specific setup)
  echo "Establishing SSH tunnel and launching VS Code..."
  echo "This part needs to be implemented based on the specific setup."
}

# Execute main function
main