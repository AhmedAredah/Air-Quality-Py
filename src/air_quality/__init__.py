"""air_quality package init.

Exposes package version and minimal convenience symbols.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .module import DashboardPayload

__version__ = "0.1.0"


def hello() -> str:
    return "Hello from air-quality!"


__all__ = ["__version__", "hello"]

# DashboardPayload is available for type hints via:
# from air_quality.module import DashboardPayload
