"""Shelter coordination service.

Thin wrapper around ShelterRepository for API consumption.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.repositories.shelter_repository import ShelterRepository
from backend.app.database.repositories.audit_history_repository import AuditHistoryRepository
from backend.app.database.models import Shelter

logger = logging.getLogger(__name__)


class ShelterService:
    def __init__(self, db: Session):
        self.db = db
        self.shelter_repo = ShelterRepository(db)
        self.audit_repo = AuditHistoryRepository(db)

    def get_all_shelters(self, skip: int = 0, limit: int = 100) -> list[Shelter]:
        return self.shelter_repo.get_all(skip=skip, limit=limit)

    def get_shelter(self, shelter_id: UUID) -> Optional[Shelter]:
        return self.shelter_repo.get_by_id(shelter_id)

    def create_shelter(
        self,
        name: str,
        address: str = None,
        capacity: int = 0,
        current_occupancy: int = 0,
        facilities: dict = None,
        contact_phone: str = None,
        operated_by: UUID = None,
        latitude: float = None,
        longitude: float = None,
        status: str = "open",
    ) -> Shelter:
        if current_occupancy < 0:
            raise ValueError("current_occupancy cannot be negative")
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        if current_occupancy > capacity:
            raise ValueError(
                f"current_occupancy ({current_occupancy}) cannot exceed capacity ({capacity})"
            )
        if status == "open":
            if capacity <= 0:
                raise ValueError("Shelter with zero capacity cannot be assigned 'open' status")
            if current_occupancy >= capacity:
                raise ValueError(
                    f"Cannot set status to 'open' when occupancy ({current_occupancy}) is greater than or equal to capacity ({capacity})"
                )

        location_wkt = None
        if latitude is not None and longitude is not None:
            location_wkt = f"SRID=4326;POINT({longitude} {latitude})"

        shelter = self.shelter_repo.create(
            name=name,
            address=address,
            capacity=capacity,
            current_occupancy=current_occupancy,
            facilities=facilities or {},
            contact_phone=contact_phone,
            status=status,
            operated_by=operated_by,
            location=location_wkt,
        )

        self.audit_repo.log(
            entity_type="shelter",
            entity_id=shelter.id,
            action="created",
            new_value={
                "name": name,
                "address": address,
                "capacity": capacity,
                "current_occupancy": current_occupancy,
                "status": status,
            },
        )

        logger.info(f"Shelter created: {shelter.id} (name={name})")
        return shelter

    def update_shelter(self, shelter_id: UUID, **kwargs) -> Optional[Shelter]:
        old_shelter = self.shelter_repo.get_by_id(shelter_id)
        if old_shelter is None:
            return None

        old_value = {
            "name": old_shelter.name,
            "address": old_shelter.address,
            "capacity": old_shelter.capacity,
            "current_occupancy": old_shelter.current_occupancy,
            "status": old_shelter.status,
            "contact_phone": old_shelter.contact_phone,
        }

        capacity_changed = "capacity" in kwargs and kwargs["capacity"] is not None
        occupancy_changed = "current_occupancy" in kwargs and kwargs["current_occupancy"] is not None

        if "capacity" in kwargs and kwargs["capacity"] is None:
            kwargs.pop("capacity")
        if "current_occupancy" in kwargs and kwargs["current_occupancy"] is None:
            kwargs.pop("current_occupancy")

        new_capacity = kwargs.get("capacity", old_shelter.capacity)
        new_occupancy = kwargs.get("current_occupancy", old_shelter.current_occupancy)

        if capacity_changed or occupancy_changed:
            if new_occupancy < 0:
                raise ValueError("current_occupancy cannot be negative")
            if new_capacity < 0:
                raise ValueError("capacity cannot be negative")
            if new_occupancy > new_capacity:
                raise ValueError(
                    f"current_occupancy ({new_occupancy}) cannot exceed capacity ({new_capacity})"
                )

        has_explicit_status = "status" in kwargs and kwargs["status"] is not None
        if has_explicit_status:
            explicit_status = kwargs["status"]
            if explicit_status == "open":
                if new_capacity <= 0:
                    raise ValueError("Shelter with zero capacity cannot be assigned 'open' status")
                if new_occupancy >= new_capacity:
                    raise ValueError(
                        f"Cannot set status to 'open' when occupancy ({new_occupancy}) is greater than or equal to capacity ({new_capacity})"
                    )
        else:
            kwargs.pop("status", None)
            # Automatic status management when status is not explicitly set in payload
            if capacity_changed or occupancy_changed:
                if old_shelter.status == "closed":
                    # Preserve closed status during ordinary occupancy/capacity updates
                    pass
                elif new_occupancy >= new_capacity:
                    # Occupancy reaches or exceeds capacity without an explicit status -> full
                    kwargs["status"] = "full"
                elif new_occupancy < new_capacity:
                    if old_shelter.status == "full":
                        # Reopen only if previous occupancy was at or above previous capacity.
                        # Preserves 'full' when it represents a manual administrative hold (old_occupancy < old_capacity).
                        if old_shelter.current_occupancy >= old_shelter.capacity and new_capacity > 0:
                            kwargs["status"] = "open"

        shelter = self.shelter_repo.update(shelter_id, **kwargs)
        if shelter:
            new_value = {
                "name": shelter.name,
                "address": shelter.address,
                "capacity": shelter.capacity,
                "current_occupancy": shelter.current_occupancy,
                "status": shelter.status,
                "contact_phone": shelter.contact_phone,
            }

            self.audit_repo.log(
                entity_type="shelter",
                entity_id=shelter.id,
                action="updated",
                old_value=old_value,
                new_value=new_value,
            )

            logger.info(f"Shelter updated: {shelter_id}")
        return shelter
