# Thermo Waybar - Hardware Info Module (Modified Fork)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight Python module for Waybar that displays real-time CPU temperature, CPU load, and memory usage in your Wayland status bar. Perfect for Linux users running Hyprland, Sway, or other Wayland compositors.

**Note:** This is a modified fork focused on CPU and memory monitoring. GPU temperature monitoring has been removed in favor of a streamlined, dependency-light implementation. Mostly due to my dev-box not having discrete graphics.

## Features

- 🌡️ **Accurate Temperature Monitoring**: Displays CPU temperature with intelligent sensor filtering
- � **Memory Usage**: Shows real-time memory consumption
- 📊 **CPU Load**: Displays per-core and overall CPU usage
- ⚡ **Lightweight**: Minimal system resource usage with configurable refresh intervals
- 🛡️ **Robust Error Handling**: Automatically filters invalid sensor readings and falls back gracefully
- 🎨 **Waybar Integration**: Native JSON output designed specifically for Waybar
- 🔧 **Multiple Backend Support**: Works with psutil or falls back to sysfs/procfs

## Requirements

- Python 3.10 or higher
- Waybar on a Wayland compositor (Hyprland, Sway, etc.)
- **Recommended:** `psutil` Python package (for best performance and per-core CPU load)
  - If not available, automatically falls back to `/sys/class/thermal` and `/proc/meminfo`

## Installation

1. Place the `hwinfo.py` script in your Waybar config directory:
   ```bash
   mkdir -p ~/.config/waybar/modules/thermo-waybar
   cp hwinfo.py ~/.config/waybar/modules/thermo-waybar/
   chmod +x ~/.config/waybar/modules/thermo-waybar/hwinfo.py
   ```

2. **(Recommended)** Install psutil for enhanced functionality:
   ```bash
   pip install --user psutil
   # or system-wide on Arch Linux
   sudo pacman -S python-psutil
   ```

3. Configure the module in your Waybar configuration (see Configuration section below)

## Usage

Run the script directly to see output:
```bash
python3 hwinfo.py
```

The script will output JSON data compatible with Waybar:
```json
{
  "text": "CPU: 58.4°C (4.1%) | MEM: 6GB/31GB (20.1%)",
  "tooltip": "Hardware Info\nCPU Temp: 58.4°C (4.1%)\nCPU Load:\n  Core 0: 7.9%\n  Core 1: 4.0%\n  ...\nMemory: 6451.20MB / 31948.80MB (20.1%)\nUpdated: 14:30:22",
  "class": "hwinfo",
  "alt": "hwinfo"
}
```

## Configuration

Add the following to your Waybar configuration file (typically `~/.config/waybar/config.jsonc`):

```jsonc
{
  "modules-right": [
    "custom/hwinfo",
    // ... other modules
  ],
  
  "custom/hwinfo": {
    "exec": "python3 ~/.config/waybar/modules/thermo-waybar/hwinfo.py",
    "return-type": "json",
    "format": "{}",
    "interval": 10
  }
}
```

**Important:** If using a Python environment manager like `mise` or `pyenv`, specify the full path to your Python interpreter:

```jsonc
"custom/hwinfo": {
  "exec": "/home/username/.local/share/mise/installs/python/3.14.0/bin/python3 ~/.config/waybar/modules/thermo-waybar/hwinfo.py",
  "return-type": "json",
  "format": "{}",
  "interval": 10
}
```

Add the following to your Waybar CSS file (typically `~/.config/waybar/style.css`):

```css
#custom-hwinfo {
  color: #a3be8c;
  font-weight: bold;
  padding: 0 5px;
  margin-right: 12px;
}

#custom-hwinfo:hover {
  background-color: #4c566a;
}
```

## How It Works

The script intelligently gathers hardware information using multiple methods:

### CPU Temperature
- **Primary method:** Uses `psutil.sensors_temperatures()` to read from hardware sensors
- **Fallback method:** Reads directly from `/sys/class/thermal/thermal_zone*/temp` if psutil is unavailable
- **Intelligent filtering:** Automatically skips invalid sensor readings (< 0°C or > 150°C)
- **Sensor prioritization:** Prefers `coretemp`/`k10temp` over generic ACPI sensors for accuracy

### Memory Usage
- **Primary method:** Uses `psutil.virtual_memory()` for accurate memory statistics
- **Fallback method:** Parses `/proc/meminfo` if psutil is unavailable

### CPU Load
- **Requires psutil:** Provides per-core CPU usage percentages
- **Fallback:** If psutil is unavailable, CPU load information is omitted

## Troubleshooting

### Temperature shows as negative or incorrect
- The script now automatically filters out invalid sensor readings
- Ensure you're using the correct Python interpreter (especially if using `mise`, `pyenv`, or virtual environments)

### Module not appearing in Waybar
- Check that the module is included in your `modules-left`, `modules-center`, or `modules-right` array
- Verify the Python path is correct in your Waybar config
- Test the script manually: `python3 ~/.config/waybar/modules/thermo-waybar/hwinfo.py`

### Changes not taking effect
- Reload Waybar: `pkill waybar && waybar &` or `pkill -SIGUSR2 waybar`

## Contributing

This is a personal fork with specific modifications. Feel free to fork and adapt to your needs!

## Credits

**Modified by:** [@jonmdtn](https://github.com/jonmdtn)

**Modifications made:**
- Removed GPU temperature monitoring
- Added CPU load per-core monitoring
- Added memory usage monitoring
- Improved temperature sensor filtering and prioritization
- Fixed issues with invalid sensor readings
- Simplified to focus on CPU and memory metrics

**Original concept inspired by:** Community Waybar hardware monitoring scripts

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Waybar community for creating an excellent customizable status bar