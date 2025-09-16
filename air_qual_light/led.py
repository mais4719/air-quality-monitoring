import logging

from configparser import ConfigParser
from time import sleep
from typing import Tuple

from air_qual_light.hardware_abstraction import create_led_strip


log = logging.getLogger()


class Led():
    """Represents a LED strip."""
    def __init__(self, config: ConfigParser, color_order: str = 'GRB'):
        """Initializes the LED strip with the given configuration and color order.

        Args:
            config (ConfigParser): The configuration parser containing LED settings.
            color_order (str): The color order for the LED strip (default is GRB).

        """
        # Setup Neopixel using hardware abstraction
        neopixel_config = config['neopixel']
        self.number_of_leds = int(neopixel_config['number_of_leds'])
        self.use_half = neopixel_config.getboolean('use_half')

        # Create LED strip using factory function
        self.pixels = create_led_strip(config)

        # Load AQI color and levels
        self.levels = []
        for k, v in config.items():
            if k.startswith('level_'):

                level_str = k[6:]
                level_rgb, level_th = v.strip().split('|')

                level_rgb = tuple([int(v) for v in level_rgb.split(',')])
                level_th = int(level_th)

                self.levels.append((level_th, level_str, level_rgb))

        self.levels.sort()

        self.__do_odd = 0

    def set_light(self, pm2_5_aqi: float):

        for level_th, level_str, level_rgb in self.levels:
            if pm2_5_aqi < level_th:
                log.info(f'Setting new light level to: {level_str} for pm2.5 AQI: {pm2_5_aqi}')
                self.set_rgb(level_rgb)
                break

    def set_rgb(self, rgb: Tuple[int, int, int]):

        log.debug(f'Update LED with RGB: {rgb}')
        for idx in range(self.number_of_leds):
            if idx % 2 == 0 + self.__do_odd or not self.use_half:
                self.pixels[idx] = rgb
            else:
                self.pixels[idx] = (0, 0, 0)

        self.__do_odd = 0 if self.__do_odd == 1 else 1
        self.pixels.show()

    def working_light(self, loops: int = 5):
        """Display a working/loading animation on the LED strip.

        Args:
            loops: Number of animation cycles to run
        """
        for _ in range(loops):
            # Calculate step size for animation based on actual number of LEDs
            step_size = max(1, self.number_of_leds // 8)

            for i in range(self.number_of_leds):
                for idx in range(self.number_of_leds):
                    if idx % step_size == i % step_size:
                        self.pixels[idx] = (100, 100, 100)
                    else:
                        self.pixels[idx] = (0, 0, 10)
                self.pixels.show()
                sleep(0.2)

        self.off()

    def off(self):
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
