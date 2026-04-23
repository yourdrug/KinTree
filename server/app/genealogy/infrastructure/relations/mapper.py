from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.spouse import SpouseRelation, create_spouse_relation
from genealogy.infrastructure.db.models.parent_child import ParentChild as ORMParentChild
from genealogy.infrastructure.db.models.spouse import Spouse as ORMSpouse


def parent_child_to_domain(orm: ORMParentChild) -> ParentChildRelation:
    return ParentChildRelation(
        parent_id=orm.parent_id,
        child_id=orm.child_id,
        relation_type=orm.relation_type,
    )


def parent_child_to_persistence(entity: ParentChildRelation) -> dict:
    return {
        "parent_id": entity.parent_id,
        "child_id": entity.child_id,
        "relation_type": entity.relation_type,
    }


def spouse_to_domain(orm: ORMSpouse) -> SpouseRelation:
    return create_spouse_relation(
        person_a_id=orm.first_person_id,
        person_b_id=orm.second_person_id,
        marriage_status=orm.marriage_status,
        marriage_year=orm.marriage_year,
        marriage_month=orm.marriage_month,
        marriage_day=orm.marriage_day,
        marriage_place=orm.marriage_place,
        marriage_date_raw=orm.marriage_date_raw,
        divorce_year=orm.divorce_year,
        divorce_month=orm.divorce_month,
        divorce_day=orm.divorce_day,
        divorce_date_raw=orm.divorce_date_raw,
    )


def spouse_to_persistence(entity: SpouseRelation) -> dict:
    return {
        "first_person_id": entity.first_person_id,
        "second_person_id": entity.second_person_id,
        "marriage_status": entity.marriage_status,
        "marriage_year": entity.marriage_year,
        "marriage_month": entity.marriage_month,
        "marriage_day": entity.marriage_day,
        "marriage_place": entity.marriage_place,
        "marriage_date_raw": entity.marriage_date_raw,
        "divorce_year": entity.divorce_year,
        "divorce_month": entity.divorce_month,
        "divorce_day": entity.divorce_day,
        "divorce_date_raw": entity.divorce_date_raw,
    }
