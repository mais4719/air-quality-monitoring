import sys
import logging
import threading
from typing import Any

from configparser import ConfigParser
from datetime import datetime, time
from pathlib import Path
from time import sleep

import click
from fastapi import FastAPI

from air_qual_light import __version__
from air_qual_light.data import Sensor, calculate_consensus, get_aqi_status
from air_qual_light.sensor_request import update_sensor_data
from air_qual_light.led import Led


log = logging.getLogger()
CONFIG_FILES = list(Path(__file__).resolve().parent.parent.joinpath('config').glob('*.conf'))


# Global variables to store application state for API access
APP_STATE = {
    'sensors': [],
    'last_update': None,
    'pm2_5_aqi': None,
    'temperature': None,
    'humidity': None,
    'pressure': None,
    'purpleair_api_errors': 0
}
api_app = FastAPI(title='Air Quality Light API', version='1.0.0')


@api_app.get('/')
async def root():
    """Root endpoint providing API information."""
    return {
        'message': 'Air Quality Light API',
        'version': '1.0.0',
        'endpoints': {
            '/sensors': 'Get all sensor data',
            '/status': 'Get system status',
        }
    }


@api_app.get('/sensors')
async def get_all_sensors() -> dict[str, Any]:
    """Get data from all sensors."""
    sensors_data = [sensor.data2dict() for sensor in APP_STATE['sensors']]
    return {
        'sensors': sensors_data,
        'last_update': APP_STATE['last_update'].isoformat() if APP_STATE['last_update'] else None,
        'pm2_5_aqi': APP_STATE['pm2_5_aqi'],
        'pm2_5_aqi_status': get_aqi_status(APP_STATE['pm2_5_aqi']),
        'temperature': APP_STATE['temperature'],
        'humidity': APP_STATE['humidity'],
        'pressure': APP_STATE['pressure']
    }


@api_app.get('/status')
async def get_system_status() -> dict[str, Any]:
    """Get comprehensive system status."""

    sensors = APP_STATE['sensors']
    last_update = APP_STATE['last_update'].isoformat() if APP_STATE['last_update'] else None

    return {
        'system': {
            'version': __version__,
        },
        'sensors': {
            'total': len(sensors),
            'names': [sensor.name for sensor in sensors],
            'last_update': last_update,
            'purpleair_api_errors': APP_STATE['purpleair_api_errors']
        }
    }


def run_api_server(host: str = '0.0.0.0', port: int = 3000, log_level: str = 'info'):
    """Run the FastAPI server in a separate thread.

    Args:
        host (str): The host address to bind the server to.
        port (int): The port number to listen on.
        log_level (str): The logging level for uvicorn.

    """
    log_level = log_level.lower()
    if log_level not in {'critical', 'error', 'warning', 'info', 'debug'}:
        log_level = 'info'

    try:
        import uvicorn
        # Create uvicorn config to disable default logging
        config = uvicorn.Config(
            api_app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True,
            use_colors=False,
            log_config=None
        )
        server = uvicorn.Server(config)
        server.run()
    except ImportError:
        log.error('uvicorn is not installed. Install it with: pip install uvicorn')
        log.info('API server will not be available')
    except Exception as e:
        log.error(f'Failed to start API server: {e}')


def start_api_server_thread(host: str = '0.0.0.0', port: int = 3000, log_level: str = 'INFO'):
    """Start the API server in a background thread.

    Args:
        host (str): The host address to bind the server to.
        port (int): The port number to listen on.
        log_level (str): The logging level to use.

    """
    api_thread = threading.Thread(
        target=run_api_server,
        args=(host, port, log_level),
        daemon=True,
        name='APIServer'
    )
    api_thread.start()
    log.info(f'API server started on http://{host}:{port}')
    return api_thread


def read_config_file(config_file: str) -> tuple[ConfigParser, list[Sensor]]:
    """Reads the configuration file and returns the config parser and a list of sensors.

    Args:
        config_file (str): The path to the configuration file.

    Returns:
        tuple[ConfigParser, list[Sensor]]: The config parser and a list of sensors.

    """
    config = ConfigParser()
    config.read(config_file)

    sensors = [
        Sensor(
            name,
            sensor_str,
            api_url_tmpl=config['generic']['api_url_tmpl'],
            sensor_ttl_min=int(config['generic']['sensor_ttl_min'])
        )
        for name, sensor_str in config['sensors'].items()
    ]

    return config, sensors


def setup_logging(log_level: str) -> None:
    """Sets up logging for the application.

    Args:
        log_level (str): The logging level to use.

    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create consistent formatter for all loggers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Configure handler for root logger (this will catch most logs)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Configure main application logger
    log.setLevel(log_level)
    log.propagate = True

    # Configure FastAPI/uvicorn loggers to use the same format
    uvicorn_loggers = ['uvicorn', 'uvicorn.error', 'uvicorn.access', 'fastapi']

    for logger_name in uvicorn_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.handlers.clear()
        logger.propagate = True


def is_time_between(start: time, end: time) -> bool:
    """Checks if the current time is between the start and end times.

    Args:
        start (time): The start time.
        end (time): The end time.

    Returns:
        bool: True if the current time is between the start and end times, False otherwise.

    """
    now = datetime.now().time()
    log.debug(f'Current time: {now.strftime("%H:%M:%S")}')

    if start < end:
        return now >= start and now <= end
    else:  # Crosses Midnight
        return now >= start or now <= end


@click.command()
@click.option('--config-file', default=CONFIG_FILES)
@click.option('--log-level', default='INFO')
@click.option('--api-host', default='0.0.0.0', help='API server host')
@click.option('--api-port', default=3000, type=int, help='API server port')
@click.option('--enable-api', default=True, type=bool, help='Enable API server')
def main(config_file: str, log_level: str, api_host: str, api_port: int, enable_api: bool) -> None:
    """Main entry point for the AirQualLight application.

    Args:
        config_file (str): The path to the configuration file.
        log_level (str): The logging level to use.
        api_host (str): API server host address.
        api_port (int): API server port number.
        enable_api (bool): Whether to enable the API server.

    """
    setup_logging(log_level)

    log.info(f'Running AirQualLight version: {__version__}')
    log.info(f'Loaded config file(s): {config_file}')
    config, sensors = read_config_file(config_file)

    # Update global state
    APP_STATE['sensors'] = sensors

    api_key = config['generic']['api_key']
    log.info(f'Loaded API_KEY: {api_key[:4]}...{api_key[-4:]}')

    # Load active time
    start_time, end_time = config['generic']['active_time'].strip().split('-')
    start_time, end_time = time(int(start_time)), time(int(end_time))

    log.debug(f'Sensors: {sensors}')

    log.info('Init LED object')
    led = Led(config)

    update_frequency = int(config['generic']['update_frequency'])
    log.info(f'Starting main loop with a {update_frequency}s update frequency.')

    api_thread = None

    led.working_light(3)

    unhealthy = 0
    while True:  # Entering main loop
        try:
            update_sensor_data(sensors, api_key)
            APP_STATE['last_update'] = datetime.now()

            for sensor in sensors:
                log.debug(f'Sensors: {sensor}')

            # Update AQI and LED Lights
            pm2_5_aqi = calculate_consensus([s.us_epa_pm2_5_aqi for s in sensors if s.us_epa_pm2_5_aqi is not None])
            log.debug(f'Got a new pm2.5 AQI value: {pm2_5_aqi}')
            APP_STATE['pm2_5_aqi'] = pm2_5_aqi

            # Update other APP_STATE variables
            APP_STATE['temperature'] = calculate_consensus([s.temperature for s in sensors if s.temperature is not None])
            APP_STATE['humidity'] = calculate_consensus([s.humidity for s in sensors if s.humidity is not None])
            APP_STATE['pressure'] = calculate_consensus([s.pressure for s in sensors if s.pressure is not None])

            if is_time_between(start_time, end_time):
                led.set_light(pm2_5_aqi)
            else:
                log.debug(f'Outside active time (start: {start_time}, end: {end_time}), lights off.')
                led.off()

            # API Server
            if enable_api:
                try:
                    if api_thread is None or not api_thread.is_alive():
                        log.info('Starting API server...')
                        api_thread = start_api_server_thread(api_host, api_port, log_level)
                except Exception as api_server_error:
                    log.error(f'Failed to start API server: {api_server_error}')

            sleep(update_frequency)

        except KeyboardInterrupt:
            log.info('Shutting down the system...')
            led.off()
            if api_thread and api_thread.is_alive():
                log.info('API server will shutdown...')
            break

        except Exception as e:
            log.error(e)
            unhealthy += 1
            if unhealthy == 3:
                log.error('Reached an unhealthy state, will exit...')
                break
            led.working_light(20)
        else:
            unhealthy = 0

        APP_STATE['purpleair_api_errors'] = unhealthy


if __name__ == '__main__':
    main()
