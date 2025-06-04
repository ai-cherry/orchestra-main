#!/bin/bash
# Enhanced MCP System Shutdown Script with graceful termination and cleanup

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="${MCP_LOG_DIR:-$HOME/.mcp/logs}"
PID_DIR="${MCP_PID_DIR:-$HOME/.mcp/pids}"
GRACEFUL_TIMEOUT="${MCP_GRACEFUL_TIMEOUT:-10}"
CLEANUP_LOGS="${MCP_CLEANUP_LOGS:-false}"
ARCHIVE_LOGS="${MCP_ARCHIVE_LOGS:-true}"

# Log file
LOG_FILE="$LOG_DIR/mcp_shutdown_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)  color=$BLUE ;;
        SUCCESS) color=$GREEN ;;
        WARN)  color=$YELLOW ;;
        ERROR) color=$RED ;;
        *) color=$NC ;;
    esac
    
    echo -e "${color}[$timestamp] [$level] $message${NC}" | tee -a "$LOG_FILE"
}

# Function to get process info
get_process_info() {
    local pid=$1
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        echo "Not running"
        return 1
    fi
    
    # Get process command
    local cmd=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
    echo "PID: $pid, Command: $cmd"
}

# Function to gracefully stop a server
stop_server_gracefully() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"
    
    if [ ! -f "$pid_file" ]; then
        log INFO "$name: No PID file found, skipping..."
        return 0
    fi
    
    local pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if [ -z "$pid" ]; then
        log WARN "$name: Empty PID file, removing..."
        rm -f "$pid_file"
        return 0
    fi
    
    if ! kill -0 "$pid" 2>/dev/null; then
        log INFO "$name: Process $pid not running, cleaning up PID file..."
        rm -f "$pid_file"
        return 0
    fi
    
    log INFO "Stopping $name ($(get_process_info $pid))..."
    
    # Send SIGTERM for graceful shutdown
    if kill -TERM "$pid" 2>/dev/null; then
        log INFO "Sent SIGTERM to $name (PID: $pid)"
        
        # Wait for graceful shutdown
        local count=0
        while [ $count -lt $GRACEFUL_TIMEOUT ] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            count=$((count + 1))
            if [ $((count % 3)) -eq 0 ]; then
                log INFO "Waiting for $name to stop... ($count/$GRACEFUL_TIMEOUT seconds)"
            fi
        done
        
        # Check if process stopped
        if ! kill -0 "$pid" 2>/dev/null; then
            log SUCCESS "$name stopped gracefully"
            rm -f "$pid_file"
            return 0
        else
            log WARN "$name did not stop gracefully, sending SIGKILL..."
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
            
            if ! kill -0 "$pid" 2>/dev/null; then
                log SUCCESS "$name stopped forcefully"
                rm -f "$pid_file"
                return 0
            else
                log ERROR "Failed to stop $name (PID: $pid)"
                return 1
            fi
        fi
    else
        log ERROR "Failed to send signal to $name (PID: $pid)"
        return 1
    fi
}

# Function to stop systemd units
stop_systemd_units() {
    if command -v systemctl >/dev/null 2>&1; then
        log INFO "Checking for systemd MCP units..."
        
        # Find and stop all MCP systemd units
        local units=$(systemctl list-units --all --no-legend | grep "mcp-" | awk '{print $1}')
        
        if [ -n "$units" ]; then
            log INFO "Found systemd units: $units"
            for unit in $units; do
                log INFO "Stopping systemd unit: $unit"
                systemctl --user stop "$unit" 2>/dev/null || true
            done
        else
            log INFO "No systemd MCP units found"
        fi
    fi
}

# Function to cleanup orphaned processes
cleanup_orphaned_processes() {
    log INFO "Checking for orphaned MCP processes..."
    
    # Find Python processes running MCP servers
    local mcp_processes=$(pgrep -f "mcp_server.servers" || true)
    
    if [ -n "$mcp_processes" ]; then
        log WARN "Found orphaned MCP processes: $mcp_processes"
        for pid in $mcp_processes; do
            if [ -n "$pid" ]; then
                local cmd=$(ps -p "$pid" -o args= 2>/dev/null || echo "unknown")
                log INFO "Killing orphaned process $pid: $cmd"
                kill -TERM "$pid" 2>/dev/null || true
            fi
        done
        
        sleep 2
        
        # Force kill any remaining
        mcp_processes=$(pgrep -f "mcp_server.servers" || true)
        if [ -n "$mcp_processes" ]; then
            for pid in $mcp_processes; do
                if [ -n "$pid" ]; then
                    log WARN "Force killing process $pid"
                    kill -9 "$pid" 2>/dev/null || true
                fi
            done
        fi
    else
        log INFO "No orphaned MCP processes found"
    fi
}

# Function to cleanup ports
cleanup_ports() {
    log INFO "Checking for processes on MCP ports..."
    
    local ports=(8001 8002 8003 8006)
    for port in "${ports[@]}"; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            log WARN "Found process on port $port: $pids"
            for pid in $pids; do
                log INFO "Killing process $pid on port $port"
                kill -TERM "$pid" 2>/dev/null || true
            done
        fi
    done
}

# Function to archive logs
archive_logs() {
    if [ "$ARCHIVE_LOGS" = "true" ] && [ -d "$LOG_DIR" ]; then
        log INFO "Archiving logs..."
        
        local archive_name="mcp_logs_$(date +%Y%m%d_%H%M%S).tar.gz"
        local archive_path="$LOG_DIR/../$archive_name"
        
        # Create archive excluding the current shutdown log
        tar -czf "$archive_path" -C "$LOG_DIR" --exclude="$(basename $LOG_FILE)" . 2>/dev/null || true
        
        if [ -f "$archive_path" ]; then
            log SUCCESS "Logs archived to: $archive_path"
            
            if [ "$CLEANUP_LOGS" = "true" ]; then
                log INFO "Cleaning up old logs..."
                find "$LOG_DIR" -name "*.log" -not -name "$(basename $LOG_FILE)" -delete 2>/dev/null || true
            fi
        fi
    fi
}

# Function to display shutdown summary
display_summary() {
    log INFO "========================================="
    log INFO "MCP System Shutdown Summary"
    log INFO "========================================="
    
    echo ""
    echo "Shutdown Results:"
    
    local all_stopped=true
    for pid_file in "$PID_DIR"/*.pid; do
        [ -f "$pid_file" ] || continue
        
        server_name=$(basename "$pid_file" .pid)
        if [ -f "$pid_file" ]; then
            echo -e "  ${RED}✗${NC} $server_name: Failed to stop cleanly"
            all_stopped=false
        fi
    done
    
    if [ "$all_stopped" = "true" ]; then
        echo -e "  ${GREEN}✓${NC} All servers stopped successfully"
    fi
    
    echo ""
    echo "Cleanup Actions:"
    echo "  - Systemd units: Checked and stopped"
    echo "  - Orphaned processes: Cleaned up"
    echo "  - Ports: Released"
    if [ "$ARCHIVE_LOGS" = "true" ]; then
        echo "  - Logs: Archived"
    fi
    
    echo ""
    echo "Shutdown log: $LOG_FILE"
}

# Main execution
main() {
    log INFO "========================================="
    log INFO "Enhanced MCP System Shutdown"
    log INFO "========================================="
    
    # Stop the monitor process first if it exists
    if [ -f "$PID_DIR/monitor.pid" ]; then
        log INFO "Stopping server monitor..."
        stop_server_gracefully "monitor"
    fi
    
    # Define servers to stop (in reverse order of startup)
    local servers=("weaviate-direct" "tools" "conductor" "memory")
    local failed_servers=()
    
    # Stop each server
    for server in "${servers[@]}"; do
        if ! stop_server_gracefully "$server"; then
            failed_servers+=("$server")
        fi
    done
    
    # Stop systemd units
    stop_systemd_units
    
    # Cleanup orphaned processes
    cleanup_orphaned_processes
    
    # Cleanup ports
    cleanup_ports
    
    # Archive logs if requested
    archive_logs
    
    # Clean up empty PID directory
    if [ -d "$PID_DIR" ]; then
        rmdir "$PID_DIR" 2>/dev/null || true
    fi
    
    # Display summary
    display_summary
    
    # Exit with appropriate code
    if [ ${#failed_servers[@]} -eq 0 ]; then
        log SUCCESS "MCP system shutdown completed successfully"
        exit 0
    else
        log ERROR "Failed to stop some servers: ${failed_servers[*]}"
        exit 1
    fi
}

# Handle signals
trap 'log WARN "Received interrupt signal, cleaning up..."; cleanup_orphaned_processes; exit 130' INT TERM

# Run main function
main "$@"