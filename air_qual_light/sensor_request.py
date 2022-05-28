import asyncio
from typing import List

import aiohttp

from air_qual_light.data import Sensor


async def fetch_json(session: aiohttp.ClientSession, sensor: Sensor):

    async with session.get(sensor.api_url) as response:
        sensor.update_data(await response.text())


async def get_sensor_data(sensors: List[Sensor], api_key: str):

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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_sensor_data(sensors, api_key))
