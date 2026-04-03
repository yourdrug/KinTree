from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import (
    exists,
    func,
    select,
)
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from domain.models.basemodel import BaseModel


class BaseRepository:
    """
    BaseRepository: Abstract base repository providing common database operations.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        """
        __init__: Initializes the repository with a database session.

        Args:
            session (AsyncSession): SQLAlchemy async session instance.
        """

        self.session: AsyncSession = session

    async def get_object_id_by_field(
        self,
        model: type[BaseModel],
        field_name: str,
        field_value: str,
    ) -> Optional[str]:
        """
        get_object_id_by_field: Return object id by any field. Value must be unique and not null.

        Args:
            field_name (str): Name of the field to filter by.
            field_value (str): Value of the field to match.

        Returns:
            Optional[str]: Target object id or None.
        """

        if field_value is None:
            return None

        statement: Select = select(model.id).where(getattr(model, field_name) == field_value)
        result: Result = await self.session.execute(statement)
        object_id: Optional[str] = result.scalar()

        return object_id

    async def get_object_by_field(
        self,
        model: type[BaseModel],
        field_name: str,
        field_value: str,
    ) -> Optional[BaseModel]:
        """
        get_object_by_field: Return object by any field. Value must be unique and not null.

        Args:
            field_name (str): Name of the field to filter by.
            field_value (str): Value of the field to match.

        Returns:
            Optional[BaseModel]: Target object or None.
        """

        if field_value is None:
            return None

        statement: Select = select(model).where(getattr(model, field_name) == field_value)
        result: Result = await self.session.execute(statement)
        object: Optional[BaseModel] = result.scalar()

        return object

    async def check_object_exists(
        self,
        object_id: str,
        model: type[BaseModel],
    ) -> bool:
        """
        check_object_exists: Generic method to check object existence.

        Args:
            object_id: ID of the object to check.
            model: SQLAlchemy model class.

        Returns:
            True if object exists, False otherwise.
        """

        statement: Select = select(exists().where(model.id == object_id))
        result = await self.session.execute(statement)

        return result.scalar() or False

    async def get_object_count(
        self,
        model: type[BaseModel],
        filter: Optional[Filter],
        authenticated_account: Optional[dict],
        distinct: bool = False,
    ) -> int:
        """
        get_object_count: Generic method to get object count.

        Args:
            model (type[BaseModel]): SQLAlchemy model class.
            filter (Optional[Filter]): SQLAlchemy filter.
            scope (Optional[ScopeName]): Scope of the object.
            authenticated_account (Optional[dict]): Authenticated account data.

        Returns:
            int: Number of entities.
        """

        statement: Select

        if distinct:
            statement = select(func.count(func.distinct(model.id))).select_from(model)
        else:
            statement = select(func.count(model.id)).select_from(model)

        statement = await self._apply_filter(statement, filter)

        result: Result = await self.session.execute(statement)
        total: int = result.scalar_one()

        return total


    async def _apply_filter(
        self,
        statement: Select,
        filter: Optional[Filter],
    ) -> Select:
        """
        _apply_filter: Abstract method for applying filter to the statement.
        """

        raise NotImplementedError

    async def _apply_sort(
        self,
        statement: Select,
        filter: Optional[Filter],
    ) -> Select:
        """
        _apply_sort: Abstract method for applying sort to the statement.
        """

        raise NotImplementedError