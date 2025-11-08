#!/usr/bin/env python3
"""
Waybar module for displaying CPU temperature and memory usage.

This script fetches CPU temperature and memory usage, outputting JSON compatible with Waybar.
"""

import argparse
import json
import time
import sys
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Display CPU temperature and memory usage in Waybar.")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Update interval in seconds (default: 30)"
    )
    return parser.parse_args()

def get_cpu_temperature():
    """
    Get CPU temperature using psutil (preferred) or fallback to /sys/class/thermal.
    
    Returns:
        float or str: Average CPU temperature in Celsius, or "N/A" if not available.
    """
    try:
        # Try using psutil first
        import psutil
        temps = psutil.sensors_temperatures()
        
        if not temps:
            logger.warning("psutil.sensors_temperatures() returned no data.")
        else:
            # Look for common CPU sensor names (prioritize coretemp/k10temp over acpi)
            cpu_keys = ['coretemp', 'k10temp', 'x86_pkg_temp', 'acpitz']
            for key in cpu_keys:
                if key in temps:
                    # Calculate average temperature across all entries for this sensor
                    # Skip invalid readings (< 0°C or > 150°C)
                    total_temp = 0
                    count = 0
                    for entry in temps[key]:
                        if entry.current is not None and 0 < entry.current < 150:
                            total_temp += entry.current
                            count += 1
                    
                    if count > 0:
                        avg_temp = total_temp / count
                        return round(avg_temp, 1)
            
            # If no known keys found, try to find any sensor with 'cpu' in its name
            for name, entries in temps.items():
                if 'cpu' in name.lower() or 'core' in name.lower():
                    total_temp = 0
                    count = 0
                    for entry in entries:
                        if entry.current is not None and 0 < entry.current < 150:
                            total_temp += entry.current
                            count += 1
                    
                    if count > 0:
                        avg_temp = total_temp / count
                        return round(avg_temp, 1)
                        
    except ImportError:
        logger.warning("psutil not installed. Falling back to /sys/class/thermal.")
    except Exception as e:
        logger.error(f"Error getting CPU temperature with psutil: {e}")

    # Fallback to /sys/class/thermal
    try:
        import glob
        import os
        
        thermal_paths = glob.glob('/sys/class/thermal/thermal_zone*/temp')
        if not thermal_paths:
            logger.warning("No thermal zones found in /sys/class/thermal/")
            return "N/A"
        
        # Separate temps by sensor type, prioritizing better CPU sensors
        preferred_temps = []  # coretemp, k10temp, x86_pkg_temp
        fallback_temps = []   # acpitz
        
        for path in thermal_paths:
            # Check if this is a CPU sensor by looking at the type file
            type_path = os.path.join(os.path.dirname(path), 'type')
            try:
                with open(type_path, 'r') as f:
                    sensor_type = f.read().strip().lower()
                
                with open(path, 'r') as f:
                    temp_milli = int(f.read().strip())
                    temp_celsius = temp_milli / 1000.0
                    
                    # Skip invalid readings (< 0°C or > 150°C)
                    if not (0 < temp_celsius < 150):
                        continue
                    
                    # Prioritize coretemp/k10temp/x86_pkg_temp over acpitz
                    if any(pref in sensor_type for pref in ['coretemp', 'k10temp', 'x86_pkg_temp']):
                        preferred_temps.append(temp_celsius)
                    elif 'acpi' in sensor_type:
                        fallback_temps.append(temp_celsius)
                        
            except (IOError, ValueError) as e:
                logger.warning(f"Could not read temperature from {path}: {e}")
                continue
        
        # Use preferred sensors if available, otherwise fall back to acpitz
        temps_to_use = preferred_temps if preferred_temps else fallback_temps
        
        if temps_to_use:
            avg_temp = sum(temps_to_use) / len(temps_to_use)
            return round(avg_temp, 1)
        else:
            return "N/A"
            
    except Exception as e:
        logger.error(f"Error getting CPU temperature from /sys/class/thermal: {e}")
        
    return "N/A"

def get_cpu_load():
    """
    Get CPU load per core and overall average.
    
    Returns:
        dict: Dictionary with 'overall' (average CPU usage) and 'per_core' (list of per-core usage).
    """
    try:
        import psutil
        # Get per-core CPU usage (interval of 1 second for accurate reading)
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        overall = psutil.cpu_percent(interval=0)  # Get overall without additional delay
        
        return {
            'overall': round(overall, 1),
            'per_core': [round(load, 1) for load in cpu_percent]
        }
    except ImportError:
        logger.warning("psutil not installed. Cannot get CPU load per core.")
        return {'overall': None, 'per_core': []}
    except Exception as e:
        logger.error(f"Error getting CPU load: {e}")
        return {'overall': None, 'per_core': []}

def get_memory_usage():
    """
    Get memory usage information.
    
    Returns:
        dict: A dictionary containing 'used_gb', 'total_gb', and 'percent' keys.
    """
    try:
        # Try using psutil first (most reliable)
        import psutil
        mem = psutil.virtual_memory()
        
        used_gb = mem.used / (1024**3)  # Convert bytes to GB
        total_gb = mem.total / (1024**3)
        percent = mem.percent
        
        return {
            "used_gb": round(used_gb, 1),
            "total_gb": round(total_gb, 1),
            "percent": round(percent, 1)
        }
                    
    except ImportError:
        logger.warning("psutil not installed. Falling back to /proc/meminfo.")
    except Exception as e:
        logger.error(f"Error getting memory usage with psutil: {e}")
    
    # Fallback to /proc/meminfo
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]  # Get the number, ignore 'kB'
                    meminfo[key] = int(value)
        
        # Calculate memory usage
        # MemTotal - MemAvailable gives us the actual used memory
        if 'MemTotal' in meminfo and 'MemAvailable' in meminfo:
            total_kb = meminfo['MemTotal']
            available_kb = meminfo['MemAvailable']
            used_kb = total_kb - available_kb
            
            used_gb = used_kb / (1024**2)  # Convert KB to GB
            total_gb = total_kb / (1024**2)
            percent = (used_kb / total_kb) * 100
            
            return {
                "used_gb": round(used_gb, 1),
                "total_gb": round(total_gb, 1),
                "percent": round(percent, 1)
            }
        else:
            logger.warning("Could not find MemTotal or MemAvailable in /proc/meminfo")
            return {"used_gb": "N/A", "total_gb": "N/A", "percent": "N/A"}
            
    except Exception as e:
        logger.error(f"Error getting memory usage from /proc/meminfo: {e}")
        return {"used_gb": "N/A", "total_gb": "N/A", "percent": "N/A"}

def format_waybar_output(cpu_temp, mem_info, cpu_load):
    """
    Format the output as a JSON string compatible with Waybar.
    
    Args:
        cpu_temp (float or str): CPU temperature.
        mem_info (dict): Dictionary with memory used, total, and percentage.
        cpu_load (dict): Dictionary with 'overall' and 'per_core' CPU usage.
        
    Returns:
        str: JSON formatted string for Waybar.
    """
    import datetime
    
    # Format the main text display
    if isinstance(cpu_temp, (int, float)):
        if cpu_load['overall'] is not None:
            cpu_text = f"{cpu_temp}°C ({cpu_load['overall']}%)"
        else:
            cpu_text = f"{cpu_temp}°C"
    else:
        cpu_text = "N/A"
        
    if isinstance(mem_info['used_gb'], (int, float)) and isinstance(mem_info['total_gb'], (int, float)) and isinstance(mem_info['percent'], (int, float)):
        # Round to whole numbers for cleaner display in main bar
        used_gb_rounded = round(mem_info['used_gb'])
        total_gb_rounded = round(mem_info['total_gb'])
        mem_text = f"{used_gb_rounded}GB/{total_gb_rounded}GB ({mem_info['percent']}%)"
    else:
        mem_text = "N/A"
        
    text = f"CPU: {cpu_text} | MEM: {mem_text}"
    
    # Format the tooltip with more detailed information
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    tooltip = f"Hardware Info\n"
    tooltip += f"CPU Temp: {cpu_text}\n"
    
    # Add CPU load per core
    if cpu_load['per_core']:
        tooltip += f"CPU Load:\n"
        for i, load in enumerate(cpu_load['per_core']):
            tooltip += f"  Core {i}: {load}%\n"
    
    if isinstance(mem_info['used_gb'], (int, float)) and isinstance(mem_info['total_gb'], (int, float)):
        used_mb = mem_info['used_gb'] * 1024
        total_mb = mem_info['total_gb'] * 1024
        tooltip += f"Memory: {used_mb:.2f}MB / {total_mb:.2f}MB ({mem_info['percent']}%)\n"
    else:
        tooltip += f"Memory: N/A\n"
    
    tooltip += f"Updated: {timestamp}"
    
    output = {
        "text": text,
        "tooltip": tooltip,
        "class": "hwinfo",
        "alt": "hwinfo"
    }
    return json.dumps(output, indent=None)

def main():
    """Main execution - runs once and exits for Waybar to restart."""
    args = parse_arguments()
    
    try:
        cpu_temp = get_cpu_temperature()
        mem_info = get_memory_usage()
        cpu_load = get_cpu_load()
        output_json = format_waybar_output(cpu_temp, mem_info, cpu_load)
        print(output_json, flush=True)
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        # Print a minimal error JSON to prevent Waybar from crashing
        error_output = {
            "text": "CPU: N/A | MEM: N/A",
            "tooltip": f"Error: {e}",
            "class": "hwinfo-error",
            "alt": "hwinfo-error"
        }
        print(json.dumps(error_output, indent=None), flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()