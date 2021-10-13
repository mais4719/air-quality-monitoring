import json
import logging

from typing import List

import numpy as np


log = logging.getLogger()


class Sensor():

    def __init__(self, name: str, sensor_str: str, api_url_tmpl: str):

        self.name = name
        self.id = int(sensor_str.strip())
        self._data_dict = None

        self._api_url_tmpl = api_url_tmpl

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'<Sensor, name: {self.name}, id: {self.id}, pm2.5 AQI: {self.us_epa_pm2_4_aqi}>'

    def update_data(self, json_str: str):
        self._data_dict = json.loads(json_str)

    @property
    def api_url(self) -> str:
        return self._api_url_tmpl.format(sensor_id=self.id)

    @property
    def pm2_5_atm(self) -> List[float]:
        if self._data_dict is not None:

            results = [float(r['pm2_5_atm']) for r in self._data_dict['results']]
            return results

        return []

    @property
    def us_epa_pm2_4_aqi(self) -> List[float]:
        return [calculate_aqi(v) for v in self.pm2_5_atm]


def remap(value: float, low1: float, high1: float, low2: float, high2: float) -> float:
    return low2 + (high2 - low2) * (value - low1) / (high1 - low1)


def calculate_aqi(pm: float) -> float:
    if pm > 500:
        aqi = 500
    elif pm > 350.5:
        aqi = remap(pm, 350.5, 500.5, 400, 500)
    elif pm > 250.5:
        aqi = remap(pm, 250.5, 350.5, 300, 400)
    elif pm > 150.5:
        aqi = remap(pm, 150.5, 250.5, 200, 300)
    elif pm > 55.5:
        aqi = remap(pm, 55.5, 150.5, 150, 200)
    elif pm > 35.5:
        aqi = remap(pm, 35.5, 55.5, 100, 150)
    elif pm > 12:
        aqi = remap(pm, 12, 35.5, 50, 100)
    elif pm > 0:
        aqi = remap(pm, 0, 12, 0, 50)
    else:
        aqi = pm
    return aqi


def calculate_concencus_aqi(pm_values: List[float], max_deviations: float = 2.0) -> float:

    pm_values = np.array(pm_values).flatten()  # Flatten nested list if provided.
    mean = np.mean(pm_values)
    std = np.std(pm_values)
    distance_from_mean = abs(pm_values - mean)
    not_outlier = distance_from_mean < max_deviations * std

    log.debug(f'pm_values: {pm_values}, not_outlier: {not_outlier}')

    return np.mean(pm_values[not_outlier])
