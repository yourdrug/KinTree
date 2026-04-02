from fastapi import APIRouter
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import (
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import Insert as PgInsert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import (
    contains_eager,
    joinedload,
)
from sqlalchemy.sql import (
    Delete,
    Insert,
    Select,
    Update,
)
from sqlalchemy.sql.expression import ScalarSelect

from domain.models.account import Account
from infrastructure.common.database import database

router: APIRouter = APIRouter(prefix="/users", tags=["Пользователь"])

@router.post("/create_user/")
async def create_user() -> Response:
    asession: AsyncSession = database.get_session(master=True)
    async with asession.begin():
        data = {
            "email": "asdasdas@fsad.com",
            "is_acc_blocked": False
        }
        statement: Insert = insert(Account).values(**data).returning(Account.id)
        result: Result = await asession.execute(statement)
        account_id: str = result.scalar_one()
        return{"account_id": account_id}

@router.post("/get_user/")
async def get_user(account_id: str) -> Response:
    asession: AsyncSession = database.get_session(master=False)
    async with asession.begin():
        statement: Select = select(Account).where(Account.id == account_id)
        result: Result = await asession.execute(statement)
        account = result.scalar_one_or_none()  # извлекаем одну запись или None

        if not account:
            return {"error": "Account not found"}

        # Преобразуем в словарь вручную
        return {
            "id": account.id,
            "email": account.email,
            "is_acc_blocked": account.is_acc_blocked
        }

