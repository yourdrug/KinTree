from domain.entities.family import Family as DomainFamily

from infrastructure.db.models.family import Family as ORMFamily


class FamilyMapper:
    def to_domain(self, model: ORMFamily) -> DomainFamily:
        return DomainFamily(
            id=model.id,
            name=model.name,
            owner_id=model.owner_id,
            description=model.description,
            origin_place=model.origin_place,
            founded_year=model.founded_year,
            ended_year=model.ended_year,
        )

    def to_persistence(self, entity: DomainFamily) -> dict:
        return {
            "id": entity.id,
            "name": entity.name,
            "owner_id": entity.owner_id,
            "description": entity.description,
            "origin_place": entity.origin_place,
            "founded_year": entity.founded_year,
            "ended_year": entity.ended_year,
        }
