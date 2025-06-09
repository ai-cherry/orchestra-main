#!/usr/bin/env python3
"""
"""
PERFORMANCE_LOG = WORKSPACE_T / ".vscode" / "extension_performance.json"
LOG_DIR = WORKSPACE_T / "logs"
MONITOR_LOG = LOG_DIR / "extension_monitor.log"

# Set up centralized logging (INFO level, JSON format for standard log aggregators)
LOG_FILE = WORKSPACE_T / "logs" / "extension_performance.log"
# Ensure logs directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Thresholds for identifying problematic extensions
THRESHOLD_CPU_PERCENT = 20.0  # CPU usage threshold in percent
THRESHOLD_MEMORY_MB = 200.0  # Memory usage threshold in MB
HIGH_USAGE_COUNT_THRESHOLD = 5  # Number of high usage occurrences before flagging

# Use centralized logging configuration from core/logging_config.py
from core.logging_config import get_logger, setup_logging

# Set up logger for this module
logger = get_logger(__name__)

def get_extension_processes() -> List[Dict[str, Any]]:
    """
    """
            ["ps", "-eo", "pid,%cpu,%mem,command", "--sort=-%cpu"],
            capture_output=True,
            text=True,
            check=True,
        )

        processes = []
        # TODO: Consider using list comprehension for better performance

        for line in result.stdout.splitlines():
            if "extensionHost" in line:
                parts = line.strip().split()
                if len(parts) >= 3:
                    pid = parts[0]
                    cpu = float(parts[1])
                    mem = float(parts[2])
                    processes.append(
                        {
                            "pid": pid,
                            "cpu": cpu,
                            "memory": mem,
                            "command": " ".join(parts[3:]),
                        }
                    )
        return processes
    except Exception:

        pass
        logger.error(f"Error getting extension processes: {e}")
        return []

def get_installed_extensions() -> List[str]:
    """
        List of installed extensions in format "publisher.name@version"
    """
            ["code", "--list-extensions", "--show-versions"],
            capture_output=True,
            text=True,
            check=True,
        )

        extensions = []
        for line in result.stdout.splitlines():
            if line:
                extensions.append(line)
        return extensions
    except Exception:

        pass
        logger.error(f"Error getting installed extensions: {e}")
        return []

def load_performance_log() -> Dict[str, Any]:
    """
    """
            with open(PERFORMANCE_LOG, "r") as f:
                return json.load(f)
        except Exception:

            pass
            logger.warning("Performance log exists but is not valid JSON. Creating new log.")
            return {"extensions": {}, "last_updated": "", "high_usage_events": []}

    return {"extensions": {}, "last_updated": "", "high_usage_events": []}

def save_performance_log(data: Dict[str, Any]) -> None:
    """
    """
    with open(PERFORMANCE_LOG, "w") as f:
        json.dump(data, f, indent=2)

def check_resource_usage(processes: List[Dict[str, Any]]) -> Tuple[bool, bool]:
    """
    """
        if proc["cpu"] > THRESHOLD_CPU_PERCENT:
            high_cpu = True
            logger.warning(f"High CPU usage detected: {proc['cpu']}% (PID: {proc['pid']})")

        if proc["memory"] > THRESHOLD_MEMORY_MB:
            high_memory = True
            logger.warning(f"High memory usage detected: {proc['memory']}MB (PID: {proc['pid']})")

    return high_cpu, high_memory

def get_extension_categories() -> Dict[str, str]:
    """
    """
    extensions_config_path = WORKSPACE_T / "extensions.json"
    categories = {}

    if not extensions_config_path.exists():
        return categories

    try:


        pass
        with open(extensions_config_path, "r") as f:
            config = json.load(f)

        for category, extensions in config.items():
            for ext in extensions:
                categories[ext] = category

        return categories
    except Exception:

        pass
        logger.error(f"Error loading extension categories: {e}")
        return categories

def get_problematic_extensions(performance_log: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    """
    for ext_id, data in performance_log.get("extensions", {}).items():
        if (
            data.get("high_cpu_count", 0) > HIGH_USAGE_COUNT_THRESHOLD
            or data.get("high_memory_count", 0) > HIGH_USAGE_COUNT_THRESHOLD
        ):
            problematic.append(
                {
                    "id": ext_id,
                    "high_cpu_count": data.get("high_cpu_count", 0),
                    "high_memory_count": data.get("high_memory_count", 0),
                    "last_high_usage": data.get("last_high_usage", ""),
                    "category": data.get("category", "unknown"),
                }
            )

    return problematic

def main() -> None:
    """Main entry point for the script."""
    setup_logging(level="INFO", json_format=True)
    logger.info("Starting VS Code Extension Performance Monitor")

    # Get current performance data
    processes = get_extension_processes()
    installed_extensions = get_installed_extensions()

    logger.info(f"Found {len(processes)} extension host processes")
    logger.info(f"Found {len(installed_extensions)} installed extensions")

    # Load existing log
    performance_log = load_performance_log()

    # Update log with current data
    timestamp = datetime.now().isoformat()
    performance_log["last_updated"] = timestamp

    # Get extension categories
    categories = get_extension_categories()

    # Process each extension
    for ext in installed_extensions:
        ext_id = ext.split("@")[0]
        if ext_id not in performance_log["extensions"]:
            performance_log["extensions"][ext_id] = {
                "high_cpu_count": 0,
                "high_memory_count": 0,
                "last_high_usage": "",
                "category": categories.get(ext_id, "unknown"),
            }
        else:
            # Update category in case it changed
            performance_log["extensions"][ext_id]["category"] = categories.get(
                ext_id, performance_log["extensions"][ext_id].get("category", "unknown")
            )

    # Check for high resource usage
    high_cpu, high_memory = check_resource_usage(processes)

    # If high usage detected, record the event
    if high_cpu or high_memory:
        event = {
            "timestamp": timestamp,
            "high_cpu": high_cpu,
            "high_memory": high_memory,
            "processes": processes,
        }
        performance_log["high_usage_events"].append(event)

        # Keep only the last 10 events to avoid the log growing too large
        if len(performance_log["high_usage_events"]) > 10:
            performance_log["high_usage_events"] = performance_log["high_usage_events"][-10:]

        # Increment counters for all extensions
        # This is a simplification - in a real implementation, you would
        # want to identify which specific extension is causing the issue
        for ext_id in performance_log["extensions"]:
            if high_cpu:
                performance_log["extensions"][ext_id]["high_cpu_count"] += 1
            if high_memory:
                performance_log["extensions"][ext_id]["high_memory_count"] += 1
            performance_log["extensions"][ext_id]["last_high_usage"] = timestamp

    # Save updated log
    save_performance_log(performance_log)

    # Check for problematic extensions
    problematic = get_problematic_extensions(performance_log)
    if problematic:
        logger.warning(f"Found {len(problematic)} potentially problematic extensions:")
        for ext in problematic:
            category = ext["category"]
            category_label = f"({category})" if category != "unknown" else ""
            logger.warning(
                f"  - {ext['id']} {category_label}: CPU issues: {ext['high_cpu_count']}, Memory issues: {ext['high_memory_count']}"
            )

            # Provide recommendations based on category
            if category == "optional":
                logger.info(f"    Recommendation: Consider disabling {ext['id']} as it's marked as optional")
            elif category == "ai":
                logger.info(
                    f"    Recommendation: AI extensions like {ext['id']} can be resource intensive. Consider using them only when needed."
                )
            elif category == "development":
                logger.info(
                    f"    Recommendation: {ext['id']} is a development tool. Check if there are lighter alternatives."
                )
            elif category == "critical":
                logger.info(
                    f"    Recommendation: {ext['id']} is marked as critical. Check for updates or configuration issues."
                )
    else:
        logger.info("No problematic extensions found")

    logger.info("Extension performance monitoring complete")

if __name__ == "__main__":
    main()
