#!/bin/bash

# Script to manage Cloud Workstations

set -e

# Source the authentication script
source ./authenticate_codespaces.sh

# Function to list workstations
list_workstations() {
  echo "Listing workstations..."
  gcloud workstations workstations list --format="table(name, workstation_config_id, workstation_cluster_id, state)"
}

# Function to start a workstation
start_workstation() {
  local workstation_id=$1
  echo "Starting workstation $workstation_id..."
  gcloud workstations workstations start $workstation_id
}

# Function to stop a workstation
stop_workstation() {
  local workstation_id=$1
  echo "Stopping workstation $workstation_id..."
  gcloud workstations workstations stop $workstation_id
}

# Function to create a workstation
create_workstation() {
  local workstation_id=$1
  local workstation_config_id=$2
  local workstation_cluster_id=$3
  echo "Creating workstation $workstation_id..."
  gcloud workstations workstations create $workstation_id \
    --workstation-config=$workstation_config_id \
    --workstation-cluster=$workstation_cluster_id
}

# Function to delete a workstation
delete_workstation() {
  local workstation_id=$1
  echo "Deleting workstation $workstation_id..."
  gcloud workstations workstations delete $workstation_id
}

# Main function
main() {
  if [ $# -eq 0 ]; then
    echo "Usage: $0 <command> [options]"
    echo "Commands:"
    echo "  list"
    echo "  start <workstation_id>"
    echo "  stop <workstation_id>"
    echo "  create <workstation_id> <workstation_config_id> <workstation_cluster_id>"
    echo "  delete <workstation_id>"
    exit 1
  fi

  case $1 in
    list)
      list_workstations
      ;;
    start)
      start_workstation $2
      ;;
    stop)
      stop_workstation $2
      ;;
    create)
      create_workstation $2 $3 $4
      ;;
    delete)
      delete_workstation $2
      ;;
    *)
      echo "Invalid command: $1"
      exit 1
      ;;
  esac
}

# Execute main function
main