import json
import logging

from datetime import datetime, timedelta

import numpy as np


log = logging.getLogger()


class Sensor():
    """Represents a sensor device."""
    def __init__(self, name: str, sensor_str: str, api_url_tmpl: str, sensor_ttl_min: int = 10):
        """Initializes the sensor with the given parameters.

        Args:
            name (str): The name of the sensor.
            sensor_str (str): The sensor string (ID).
            api_url_tmpl (str): The API URL template for the sensor.
            sensor_ttl_min (int): The time-to-live for sensor data in minutes.

        """
        self.name = name
        self.id = int(sensor_str.strip())
        self._data_dict = None
        self.sensor_ttl_min = sensor_ttl_min

        self._api_url_tmpl = api_url_tmpl

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return (
            f'<Sensor, name: {self.name}, id: {self.id}, '
            f'data time stamp: {self.data_time_stamp.strftime("%Y-%m-%d %H:%M:%S")}, '
            f'pm2.5 AQI: {self.us_epa_pm2_5_aqi}, '
            f'temperature: {self.temperature}, '
            f'humidity: {self.humidity}, '
            f'pressure: {self.pressure}, '
            f'location: lat {self.location[0]}, lon {self.location[1]}, alt {self.location[2]}>'
        )

    def update_data(self, json_str: str):
        """Updates the sensor data from a JSON string.

        Args:
            json_str (str): The JSON string containing the sensor data.

        """
        self._data_dict = json.loads(json_str)

    def _ttl_expired(self):
        if self.data_time_stamp is not None:
            if datetime.now() - self.data_time_stamp > timedelta(minutes=self.sensor_ttl_min):
                log.warning(f'Sensor {self.name} data TTL expired.')
                self._data_dict = None

    @property
    def api_url(self) -> str:
        return self._api_url_tmpl.format(sensor_id=self.id)

    @property
    def data_time_stamp(self) -> datetime:
        """Returns the data time stamp."""
        if self._data_dict is not None:
            return datetime.fromtimestamp(
                float(self._data_dict['data_time_stamp'])
            )
        return datetime.fromtimestamp(0)

    @property
    def location(self) -> tuple[float, float, int]:
        """Returns the location of the sensor as (latitude, longitude, altitude)."""
        self._ttl_expired()
        if self._data_dict is not None:
            latitude = float(self._data_dict['sensor']['latitude'])
            longitude = float(self._data_dict['sensor']['longitude'])
            altitude = int(self._data_dict['sensor']['altitude'])
            return (latitude, longitude, altitude)
        return (0.0, 0.0, 0)

    @property
    def temperature(self, unit: str = 'C') -> float | None:
        """Returns the temperature in the specified unit.

        Args:
            unit (str): The unit to convert the temperature to ('C' or 'F').

        Returns:
            float | None: The temperature in the specified unit, or None if not available.

        """
        self._ttl_expired()
        if self._data_dict is not None:
            temp = float(self._data_dict['sensor']['temperature'])
            if unit == 'F':
                return temp
            elif unit == 'C':
                return (temp - 32) * 5/9
            else:
                raise ValueError(f'Unknown temperature unit: "{unit}"')
        return None

    @property
    def humidity(self) -> float | None:
        """Returns the humidity level in %."""
        self._ttl_expired()
        if self._data_dict is not None:
            return float(self._data_dict['sensor']['humidity'])
        return None

    @property
    def pressure(self) -> float | None:
        """Returns the atmospheric pressure in hPa."""
        self._ttl_expired()
        if self._data_dict is not None:
            return float(self._data_dict['sensor']['pressure'])
        return None

    @property
    def pm2_5_atm(self) -> float | None:
        """Returns the PM2.5 atmospheric concentration in µg/m³."""
        self._ttl_expired()
        if self._data_dict is not None:
            results = float(self._data_dict['sensor']['pm2.5_atm'])
            return results

        return None

    @property
    def us_epa_pm2_5_aqi(self) -> float | None:
        """Returns the US EPA PM2.5 AQI value."""
        self._ttl_expired()
        if self.pm2_5_atm is None:
            return None
        else:
            return calculate_aqi(self.pm2_5_atm)

    def data2dict(self) -> dict:
        return {
            'name': self.name,
            'id': self.id,
            'data_timestamp': self.data_time_stamp.isoformat() if self.data_time_stamp else None,
            'location': {
                'latitude': self.location[0],
                'longitude': self.location[1],
                'altitude': self.location[2]
            },
            'measurements': {
                'pm2_5_atm': self.pm2_5_atm,
                'us_epa_pm2_5_aqi': self.us_epa_pm2_5_aqi,
                'temperature_c': self.temperature,
                'temperature_f': self.temperature if self.temperature is None else (self.temperature * 9/5 + 32),
                'humidity': self.humidity,
                'pressure': self.pressure
            },
            'api_url': self.api_url
        }


def remap(value: float, low1: float, high1: float, low2: float, high2: float) -> float:
    """
    Remaps a value from one range to another.

    Args:
        value (float): The value to remap.
        low1 (float): The lower bound of the original range.
        high1 (float): The upper bound of the original range.
        low2 (float): The lower bound of the target range.
        high2 (float): The upper bound of the target range.

    Returns:
        float: The remapped value.

    """
    return low2 + (high2 - low2) * (value - low1) / (high1 - low1)


def calculate_aqi(pm: float) -> float:
    """Calculates the AQI (Air Quality Index) for a given PM2.5 concentration.

    Args:
        pm (float): The PM2.5 concentration in µg/m³.

    Returns:
        float: The calculated AQI value.

    """
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


def get_aqi_status(aqi: float) -> str:
    """Get AQI status description based on value.

    Args:
        aqi (float): The AQI value to evaluate.

    Returns:
        str: The AQI status description.

    """
    if aqi is None:
        return 'Unknown'
    elif aqi <= 50:
        return 'Good'
    elif aqi <= 100:
        return 'Moderate'
    elif aqi <= 150:
        return 'Unhealthy for Sensitive Groups'
    elif aqi <= 200:
        return 'Unhealthy'
    elif aqi <= 300:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'


def calculate_consensus(values: list[float]) -> float:
    """Calculates the consensus AQI from a list of PM2.5 values.

    Args:
        pm_values (list[float]): The list of PM2.5 values.
        max_deviations (float): The maximum number of standard deviations to consider for outlier removal.

    Returns:
        float: The calculated consensus AQI.

    """
    if not values:
        return 0.0

    if len(values) == 1:
        return values[0]

    values_array = np.array(values).flatten()

    # Select method
    if len(values_array) <= 3:
        method = 'median'
    elif len(values_array) <= 6:
        method = 'iqr'
    else:
        method = 'modified_z'

    # Apply selected method
    if method == 'median':  # For very small samples, just use median
        result = float(np.median(values_array))
        log.debug(f'values: {values_array}, using median: {result}')
        return result

    elif method == 'iqr':  # IQR method for small-medium samples
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        not_outlier = (values_array >= lower_bound) & (values_array <= upper_bound)

    else:  # method == 'modified_z'  # Modified Z-score method for larger samples
        median = np.median(values_array)
        mad = np.median(np.abs(values_array - median))
        if mad == 0:
            return float(median)

        modified_z_scores = 0.6745 * (values_array - median) / mad
        not_outlier = np.abs(modified_z_scores) < 3.5

    # If all values are outliers, return median
    if not np.any(not_outlier):
        result = float(np.median(values_array))
        log.debug(f'pm_values: {values_array}, all outliers, using median: {result}')
        return result

    result = float(np.mean(values_array[not_outlier]))
    log.debug(f'pm_values: {values_array}, method: {method}, not_outlier: {not_outlier}, result: {result}')
    return result
