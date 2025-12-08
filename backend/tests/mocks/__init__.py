"""
Mock objects for testing external services and hardware.

These mocks provide consistent, controllable replacements for
external dependencies like APIs, GPIO, and SPI devices.
"""

from .external_apis import MockGeminiClient, MockImmichClient, MockRequestsSession
from .hardware import MockGPIO, MockSPI, MockWaveshareEPD

__all__ = [
    "MockRequestsSession",
    "MockImmichClient",
    "MockGeminiClient",
    "MockGPIO",
    "MockSPI",
    "MockWaveshareEPD",
]
