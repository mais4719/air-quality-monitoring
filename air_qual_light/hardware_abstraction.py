import logging

from abc import ABC, abstractmethod
from configparser import ConfigParser
from typing import Any

from air_qual_light import RASPBERRY_PI_HARDWARE


log = logging.getLogger(__name__)


class BoardInterface(ABC):
    """Abstract interface for board pin access."""

    @abstractmethod
    def get_pin(self, pin_name: str) -> Any:
        """Get a pin object for the given pin name."""
        pass


class SimulatedLEDStrip():
    """Simulated LED strip implementation for development and testing."""

    def __init__(
            self,
            pin: Any,
            num_pixels: int,
            brightness: float = 1.0,
            auto_write: bool = False,
            pixel_order: str = 'GRB'
    ):
        """Initialize simulated LED strip.

        Args:
            pin: Pin object (ignored in mock)
            num_pixels: Number of LEDs in the strip
            brightness: Brightness level (0.0 to 1.0)
            auto_write: Whether to automatically update on changes
            pixel_order: Color order (e.g., 'GRB', 'RGB')

        """
        self.num_pixels = num_pixels
        self.brightness = brightness
        self.auto_write = auto_write
        self.pixel_order = pixel_order
        self._pixels = [(0, 0, 0)] * num_pixels

        log.debug(f'SimulatedLEDStrip initialized: {num_pixels} pixels, '
                 f'brightness={brightness}, order={pixel_order}')

    def __setitem__(self, index: int, value: tuple[int, int, int]) -> None:
        """Set the color of a specific LED.

        Args:
            index (int): The index of the LED to set.
            value (tuple[int, int, int]): The RGB color value to set.

        """
        if 0 <= index < self.num_pixels:
            r, g, b = value[:3]
            adjusted_value = (int(r * self.brightness), int(g * self.brightness), int(b * self.brightness))
            self._pixels[index] = adjusted_value
            log.debug(f"Set pixel {index} to {adjusted_value}")

            if self.auto_write:
                self.show()
        else:
            log.warning(f'Invalid pixel index {index}, valid range: 0-{self.num_pixels-1}')

    def show(self) -> None:
        """Update the LED strip to show the current colors."""
        log.debug(f'SimulatedLEDStrip.show() called - displaying {len(self._pixels)} pixels')

    def fill(self, color: tuple[int, int, int]) -> None:
        """Fill all LEDs with the same color.

        Args:
            color (tuple[int, int, int]): The RGB color value to fill with.

        """
        adjusted_color = tuple(int(c * self.brightness) for c in color)
        self._pixels = [adjusted_color] * self.num_pixels
        log.debug(f'Filled all {self.num_pixels} pixels with {adjusted_color}')

        if self.auto_write:
            self.show()


class SimulatedBoard(BoardInterface):
    """Simulated board implementation for development and testing."""

    def __init__(self):
        """Initialize simulated board with common pin names."""
        self._pins = {
            'D18': 'mock_pin_18',
            'D19': 'mock_pin_19',
            'D21': 'mock_pin_21',
        }
        log.debug(f'SimulatedBoard initialized with pins: {", ".join(self._pins.keys())}')

    def get_pin(self, pin_name: str) -> str:
        """Get a simulated pin object for the given pin name."""
        if pin_name in self._pins:
            log.debug(f'Returning simulated pin for {pin_name}')
            return self._pins[pin_name]
        else:
            log.warning(f'Unknown pin name: {pin_name}')
            return pin_name


class RealBoard(BoardInterface):
    """Real Raspberry Pi board implementation."""

    def __init__(self):
        """Initialize real board interface."""
        try:
            import board
            self._board = board
            log.debug('RealBoard initialized successfully')
        except ImportError as e:
            log.error(f'Failed to import board module: {e}')
            raise

    def get_pin(self, pin_name: str) -> Any:
        """Get a real pin object for the given pin name."""
        try:
            pin = getattr(self._board, pin_name)
            log.debug(f'Got pin {pin_name}: {pin}')
            return pin
        except AttributeError:
            log.error(f'Pin {pin_name} not found on board')
            raise


def create_led_strip(config: ConfigParser) -> Any:
    """Factory function to create the appropriate LED strip implementation.

    Args:
        config: Configuration parser with neopixel settings

    Returns:
        Any: Either a real NeoPixel or SimulatedLEDStrip instance (both implement LEDInterface methods)

    """
    neopixel_config = config['neopixel']

    num_pixels = int(neopixel_config['number_of_leds'])
    brightness = float(neopixel_config['light_intensity'])
    pin_name = neopixel_config['board_connection']

    if RASPBERRY_PI_HARDWARE:
        try:
            from neopixel import NeoPixel, GRB

            # Create real board and get pin
            board_interface = RealBoard()
            # Create real NeoPixel instance
            led_strip = NeoPixel(
                board_interface.get_pin(pin_name),
                num_pixels,
                brightness=brightness,
                auto_write=False,
                pixel_order=GRB
            )

            log.info(f'Created real NeoPixel strip: {num_pixels} pixels on pin {pin_name}')
            return led_strip

        except (ImportError, AttributeError) as e:
            log.warning(f'Failed to create real NeoPixel strip: {e}, falling back to simulated')

    # Falling back to simulated implementation
    board_interface = SimulatedBoard()

    led_strip = SimulatedLEDStrip(
        board_interface.get_pin(pin_name),
        num_pixels,
        brightness=brightness,
        auto_write=False,
        pixel_order='GRB'
    )

    log.info(f'Created simulated LED strip: {num_pixels} pixels')
    return led_strip
