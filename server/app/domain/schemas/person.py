from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from domain.enums import PersonGender
from domain.schemas.base import Schema


class PersonBaseSchema(Schema):
    first_name: str = Field(
        min_length=1,
        max_length=255,
        description='First name of person',
        examples=['John', 'Ivan'],
    )

    last_name: str = Field(
        min_length=1,
        max_length=255,
        description='Last name of person',
        examples=['Masla', 'Cyrus'],
    )

    gender: PersonGender = Field(
        description="Gender of the person (must match PersonGender enum)",
        examples=["MALE", "FEMALE", "UNKNOWN"],
    )

    birth_year: Optional[int] = Field(
        default=None,
        ge=0,
        le=9999,
        description="Year of birth",
        examples=[1990],
    )

    birth_month: Optional[int] = Field(
        default=None,
        ge=1,
        le=12,
        description="Month of birth (1-12)",
        examples=[5],
    )

    birth_day: Optional[int] = Field(
        default=None,
        ge=1,
        le=31,
        description="Day of birth (1-31)",
        examples=[15],
    )

    death_year: Optional[int] = Field(
        default=None,
        ge=0,
        le=9999,
        description="Year of death",
        examples=[2020],
    )

    death_month: Optional[int] = Field(
        default=None,
        ge=1,
        le=12,
        description="Month of death (1-12)",
        examples=[7],
    )

    death_day: Optional[int] = Field(
        default=None,
        ge=1,
        le=31,
        description="Day of death (1-31)",
        examples=[10],
    )

    birth_date_raw: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Original text date of birth (e.g. 'April 1970')",
        examples=["April 1970"],
    )

    death_date_raw: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Original text date of death (e.g. 'April 1970')",
        examples=["May 2020"],
    )

    family_id: str = Field(
        min_length=32,
        max_length=32,
        description='Family identificator',
        examples=['4130413fe4dc40298232322c244dcb91'],
    )

class PersonSchema(PersonBaseSchema):
    id: str = Field(
        min_length=32,
        max_length=32,
        description='Account identificator',
        examples=['4130413fe4dc40298232322c244dcb91'],
    )

    creation_date: datetime = Field(
        description='Creation date of the account',
        examples=['2023-01-01T00:00:00'],
    )


class CreatePersonSchema(PersonBaseSchema):
    """
    CreatePersonSchema: Person schema that used in request when creating person.
    """

    pass


class UpdatePersonSchema(PersonBaseSchema):
    """
    UpdatePersonSchema: Person schema that used in request when updating person.
    """

    pass


class PatchUpdatePersonSchema(PersonBaseSchema):
    """
    PatchUpdatePersonSchema: Person schema that used in patch update request.
    """

    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    gender: Optional[PersonGender] = None

    birth_year: Optional[int] = Field(None, ge=0, le=9999)
    birth_month: Optional[int] = Field(None, ge=1, le=12)
    birth_day: Optional[int] = Field(None, ge=1, le=31)

    death_year: Optional[int] = Field(None, ge=0, le=9999)
    death_month: Optional[int] = Field(None, ge=1, le=12)
    death_day: Optional[int] = Field(None, ge=1, le=31)

    birth_date_raw: Optional[str] = Field(None, max_length=255)
    death_date_raw: Optional[str] = Field(None, max_length=255)

    family_id: Optional[str] = Field(None, min_length=32, max_length=32)


class PersonIdSchema(Schema):
    """
    PersonIdSchema: Person Identificator Schema.
    """

    id: str = Field(
        min_length=32,
        max_length=32,
        description='Person identificator',
        examples=['4130413fe4dc40298232322c244dcb91'],
    )
