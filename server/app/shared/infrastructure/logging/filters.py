"""
filters.py: File, containing logging filters.
"""

import logging


class ExceptionFilter(logging.Filter):
    """
    ExceptionFilter: Filter for excluding exceptions from logging.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        filter: Filter log records to exclude exceptions.

        Args:
            record (logging.LogRecord): Log record to filter.

        Returns:
            bool: True if the record should be filtered out, False otherwise.
        """

        return not (record.exc_info and record.levelno >= logging.ERROR)


class LevelThresholdFilter(logging.Filter):
    """
    LevelThresholdFilter: Filter for excluding log records below a certain level.
    """

    def __init__(self, max_level: int) -> None:
        """
        __init__: Initialize the filter with a maximum level.

        Args:
            max_level (int): Maximum level to include in the filter.
        """

        super().__init__()

        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        """
        filter: Filter log records to exclude those below a certain level.

        Args:
            record (logging.LogRecord): Log record to filter.

        Returns:
            bool: True if the record should be filtered out, False otherwise.
        """

        return record.levelno < self.max_level


class LevelMinFilter(logging.Filter):
    """
    LevelMinFilter: Filter for excluding log records above or equal to a certain level.
    """

    def __init__(self, min_level: int) -> None:
        """
        __init__: Initialize the filter with a minimum level.

        Args:
            min_level (int): Minimum level to include in the filter.
        """

        super().__init__()

        self.min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        """
        filter: Filter log records to exclude those above or equal to a certain level.

        Args:
            record (logging.LogRecord): Log record to filter.

        Returns:
            bool: True if the record should be filtered out, False otherwise.
        """

        return record.levelno >= self.min_level
