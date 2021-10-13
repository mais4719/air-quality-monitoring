import sys
import logging

from configparser import ConfigParser
from datetime import datetime, time
from pathlib import Path
from typing import List, Tuple
from time import sleep

import click

from air_qual_light import __version__
from air_qual_light.data import Sensor, calculate_concencus_aqi
from air_qual_light.sensor_request import update_sensor_data
from air_qual_light.led import Led


log = logging.getLogger()
CONFIG_FILES = list(Path(__file__).resolve().parent.parent.joinpath('config').glob('*.conf'))


def read_config_file(config_file: str) -> Tuple[List[Sensor], ConfigParser]:

    config = ConfigParser()
    config.read(config_file)

    sensors = [Sensor(name, sensor_str, config['generic']['api_url_tmpl'])
               for name, sensor_str in config['sensors'].items()]

    return config, sensors


def setup_logging(log_level: str):

    log.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    log.addHandler(handler)


def is_time_between(start: time, end: time) -> bool:
    now = datetime.now().time()

    if start < end:
        return now >= start and now <= end
    else:  # Crosses Midnight
        return now >= start or now <= end


@click.command()
@click.option('--config_file', default=CONFIG_FILES)
@click.option('--log_level', default='INFO')
def main(config_file: str, log_level: str):

    setup_logging(log_level)

    log.info(f'Running AirQualLight version: {__version__}')
    log.info(f'Loaded config file(s): {config_file}')
    config, sensors = read_config_file(config_file)

    # Load active time
    start_time, end_time = config['generic']['active_time'].strip().split('-')
    start_time, end_time = time(int(start_time)), time(int(end_time))

    log.debug(f'Sensors: {sensors}')

    log.info('Init LED object')
    led = Led(config)

    update_frequency = int(config['generic']['update_frequency'])
    log.info(f'Starting main loop with a {update_frequency}s update frequency.')

    led.working_light(3)

    unhealty = 0
    while True:
        try:

            if is_time_between(start_time, end_time):
                update_sensor_data(sensors)
                pm2_5_aqi = calculate_concencus_aqi([s.us_epa_pm2_4_aqi for s in sensors])
                log.debug(f'Got a new pm2.5 AQI value: {pm2_5_aqi}')
                led.set_light(pm2_5_aqi)
            else:
                log.debug(f'Outside active time (start: {start_time}, end: {end_time}), lights off.')
                led.off()

            sleep(update_frequency)

        except KeyboardInterrupt:
            log.info('Shutting down the system...')
            led.off()
            break

        except Exception as e:
            log.error(e)
            unhealty += 1
            if unhealty == 3:
                log.error('Reached an unhealthy state, will exit...')
                break
            led.working_light(20)
        else:
            unhealty = 0


if __name__ == "__main__":
    main()
