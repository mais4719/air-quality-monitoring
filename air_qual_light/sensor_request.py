import asyncio
import logging

from typing import List

import aiohttp

from air_qual_light.data import Sensor


log = logging.getLogger(__name__)


async def fetch_json(session: aiohttp.ClientSession, sensor: Sensor):
    """Fetch JSON data from the sensor's API endpoint.

    Args:

        session (aiohttp.ClientSession): The HTTP session to use.
        sensor (Sensor): The sensor object containing API information.

    """
    async with session.get(sensor.api_url) as response:
        sensor.update_data(await response.text())


async def get_sensor_data(sensors: List[Sensor], api_key: str):
    """Fetch data for multiple sensors concurrently.

    Args:
        sensors (List[Sensor]): The list of sensor objects to fetch data for.
        api_key (str): The API key to use for authentication.

    """
    tasks = []
    header = {
        'Accepts': 'application/json',
        'X-API-Key': api_key
    }

    async with aiohttp.ClientSession(headers=header) as session:
        for sensor in sensors:
            tasks.append(fetch_json(session, sensor))

        await asyncio.gather(*tasks)


def update_sensor_data(sensors: List[Sensor], api_key: str):
    """Update the data for multiple sensors.

    Args:
        sensors (List[Sensor]): The list of sensor objects to update.
        api_key (str): The API key to use for authentication.

    """
    log.info(f"Updating sensor data for {len(sensors)} sensors")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_sensor_data(sensors, api_key))
