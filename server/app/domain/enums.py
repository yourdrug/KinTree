from enum import Enum


class PersonGender(Enum):
    """
    PersonGender: Enum, containing genders of persons.
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
