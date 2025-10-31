"""Computer Use Data Collection - Privacy-first data collection for training AI agents."""

__version__ = "0.1.0"
__author__ = "bobcoi03"

from computeruse_datacollection.core.collector import DataCollector
from computeruse_datacollection.core.config import Config

__all__ = ["DataCollector", "Config", "__version__"]

