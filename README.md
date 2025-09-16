# Air Quality Light

A Python application that monitors air quality using PurpleAir sensors and displays real-time AQI (Air Quality Index) data through LED light indicators. Perfect for Raspberry Pi deployments with WS2812 LED strips.

## Features

- **Real-time Air Quality Monitoring**: Fetches data from multiple PurpleAir sensors via API
- **Visual LED Indicators**: Displays AQI levels using customizable LED colors
- **Multi-sensor Support**: Aggregates data from multiple sensors with consensus calculations
- **REST API**: Built-in FastAPI server for programmatic access to sensor data
- **Hardware Abstraction**: Supports both real hardware (Raspberry Pi) and simulation for development
- **Configurable Schedule**: LED lights can be scheduled to turn on/off at specific times
- **Robust Error Handling**: Automatic retry logic and graceful error recovery

## Hardware Support

- **Primary**: Raspberry Pi with WS2812/NeoPixel LED strips
- **Development**: Simulation mode for development on any platform
- **LED Connection**: GPIO pin D18 (configurable)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mais4719/air-quality-monitoring.git
cd air-quality-monitoring

# Install the package
pip install .
```

### Configuration

1. Copy the example configuration:
```bash
cp config/air_qual.conf.example config/air_qual.conf
```

2. Edit `config/air_qual.conf` with your settings:
```ini
[generic]
# Get your API key from PurpleAir
api_key = YOUR_PURPLEAIR_API_KEY
# Update frequency in seconds (300 = 5 minutes)
update_frequency = 300
# Active hours (8 = 8am, 22 = 10pm)
active_time = 8-22

[sensors]
# Add your PurpleAir sensor IDs
road_foo_bar = 12345
backyard = 67890
```

### Running

```bash
# Run with default settings
airqual

# Run with custom options
airqual --log-level DEBUG --api-port 8080
```

## API Endpoints

The application includes a built-in REST API server:

- `GET /` - API information and available endpoints
- `GET /sensors` - Current sensor data and AQI readings
- `GET /status` - System status and health information

Example API usage:
```bash
curl http://localhost:3000/sensors
```

## AQI Color Mapping

The LED colors correspond to EPA AQI levels:

| AQI Range | Level | Color | Description |
|-----------|-------|-------|-------------|
| 0-50 | Good | Green | Air quality is satisfactory |
| 51-100 | Moderate | Yellow/Orange | Acceptable for most people |
| 101-150 | Unhealthy for Sensitive | Orange | Sensitive groups may experience problems |
| 151-200 | Unhealthy | Red | Everyone may experience problems |
| 201-300 | Very Unhealthy | Purple | Health alert for everyone |
| 301+ | Hazardous | Maroon | Emergency conditions |

## Configuration Options

### Generic Settings
- `api_key`: Your PurpleAir API key
- `update_frequency`: Data refresh interval (seconds)
- `active_time`: LED active hours (format: start_hour-end_hour)
- `sensor_ttl_min`: Sensor data time-to-live (minutes)

### LED Settings
- `number_of_leds`: Number of LEDs in your strip
- `board_connection`: GPIO pin (default: D18)
- `light_intensity`: Brightness level (0.0-1.0)
- `use_half`: Use alternating LEDs for lower power consumption

### Custom AQI Levels
You can customize the color mapping by editing the `level_*` entries in the config file:
```ini
level_good = 0,255,0|50          # Green for AQI 0-50
level_moderate = 255,150,0|100   # Orange for AQI 51-100
```

## Development

### Testing Without Hardware

Set the environment variable to disable hardware requirements:
```bash
export RASPBERRY_PI_HARDWARE=false
airqual --log-level DEBUG
```

### Architecture

- `cli.py`: Main application entry point and API server
- `data.py`: Sensor data models and AQI calculations
- `sensor_request.py`: Asynchronous API data fetching
- `led.py`: LED control and color management
- `hardware_abstraction.py`: Hardware abstraction layer

## Command Line Options

```bash
airqual --help

Options:
  --config-file PATH     Configuration file path
  --log-level TEXT       Logging level (DEBUG, INFO, WARNING, ERROR)
  --api-host TEXT        API server host (default: 0.0.0.0)
  --api-port INTEGER     API server port (default: 3000)
  --enable-api BOOLEAN   Enable API server (default: True)
```

## Requirements

- Python 3.11+
- PurpleAir API key (free from purpleair.com)
- For hardware: Raspberry Pi with WS2812 LED strip

## Dependencies

- FastAPI & Uvicorn (REST API)
- aiohttp (async HTTP client)
- Click (CLI framework)
- numpy (data processing)
- rpi_ws281x & adafruit-circuitpython-neopixel (LED control)

## License

See LICENSE file for details.
