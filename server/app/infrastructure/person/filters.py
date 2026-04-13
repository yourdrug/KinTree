from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from infrastructure.db.models.person import Person


class PersonFilter(Filter):
    """
    Filter class for Person entities.

    Supports:
        - Exact match:        family_id, gender
        - Case-insensitive:   first_name__ilike, last_name__ilike
        - Numeric range:      birth_year__gte, birth_year__lte
                              death_year__gte, death_year__lte
        - Ordering:           order_by (prefix with "-" for desc, e.g. "-last_name")
    """

    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    gender: str | None = None
    birth_year: int | None = None
    death_year: int | None = None

    order_by: list[str] | None = None

    class Constants(Filter.Constants):
        model = Person
        ordering_field_name = "order_by"
