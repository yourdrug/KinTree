from enum import Enum


class Environment(Enum):
    """
    Environment: Enum, containing environments.
    """

    PRODUCTION = "PROD"
    TESTING = "TEST"
    DEVELOPMENT = "DEV"


class DatabaseNodeRole(Enum):
    """
    DatabaseNodeRole: Enum, containing database node roles.
    """

    MASTER = "MASTER"
    SLAVE = "SLAVE"


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
