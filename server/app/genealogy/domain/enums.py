from enum import Enum


class PersonGender(Enum):
    """
    PersonGender: Enum, containing genders of person.
    """

    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"


class RelationType(Enum):
    """
    RelationType: Enum, containing type of relations.
    """

    BIOLOGICAL = "BIOLOGICAL"
    ADOPTED = "ADOPTED"
    STEP = "STEP"


class MarriageStatus(Enum):
    """Текущий статус брака."""

    MARRIED = "MARRIED"  # в браке
    DIVORCED = "DIVORCED"  # в разводе
    WIDOWED = "WIDOWED"  # вдовец/вдова
