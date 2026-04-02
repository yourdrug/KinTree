"""
dataclasses.py: File, containing dataclasses for common app.
"""


from dataclasses import dataclass


@dataclass
class DatabaseURL:
    """
    DatabaseURL: Dataclass for database URL.
    """

    user: str
    password: str
    host: str
    port: str
    db_name: str

    def __str__(
        self,
    ) -> str:
        """
        __str__: Returns string representation of the database URL.

        Returns:
            str: Database URL
        """

        return (
            f'postgresql+psycopg://{self.user}:{self.password}'
            f'@{self.host}:{self.port}/{self.db_name}'
        )

    @property
    def url(
        self,
    ) -> str:
        """
        url: Returns string representation of the database URL.

        Returns:
            str: Database URL
        """

        return str(self)
