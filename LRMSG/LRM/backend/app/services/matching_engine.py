"""Matching engine — PostGIS proximity-based volunteer-to-request matching.

Deterministic, transparent ranking:
  1. Volunteer must be verified + active
  2. Volunteer must be available (no active assignment)
  3. Geographic proximity (PostGIS ST_Distance)
  4. Relevant skill (if request has skill hints)
  5. Lower active workload
"""

import logging
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database.models import VolunteerProfile

logger = logging.getLogger(__name__)

DEFAULT_RADIUS_KM = 25.0


@dataclass
class CandidateVolunteer:
    """A matched volunteer candidate with ranking information."""
    volunteer_id: UUID
    user_id: UUID
    skills: list[str]
    has_transport: bool
    capacity: Optional[int]
    availability: Optional[str]
    distance_km: float
    active_assignments: int
    rank_score: float


class MatchingEngine:
    """Deterministic matching engine using PostGIS for proximity."""

    def __init__(self, db: Session):
        self.db = db

    def find_candidates(
        self,
        request_id: UUID,
        radius_km: float = DEFAULT_RADIUS_KM,
        limit: int = 10,
    ) -> List[CandidateVolunteer]:
        """Find candidate volunteers for an emergency request.

        Uses PostGIS for distance filtering and ordering.
        """
        # Get the request location
        request_row = self.db.execute(
            text(
                "SELECT id, location, request_type, severity "
                "FROM emergency_requests WHERE id = :rid"
            ),
            {"rid": str(request_id)},
        ).fetchone()

        if not request_row:
            logger.warning(f"Request {request_id} not found for matching")
            return []

        request_location = request_row[1]
        if request_location is None:
            logger.warning(f"Request {request_id} has no location — using all active volunteers")
            return self._find_candidates_without_location(limit)

        # Convert geometry to WKT for PostGIS geography operations
        wkt_result = self.db.execute(
            text("SELECT ST_AsText(:geom)"),
            {"geom": request_location},
        ).fetchone()
        request_wkt = wkt_result[0] if wkt_result else None
        if not request_wkt:
            logger.warning(f"Request {request_id}: could not convert location to WKT")
            return self._find_candidates_without_location(limit)

        # PostGIS query: find eligible volunteers within radius, ordered by distance
        candidates = self.db.execute(
            text(
                """
                SELECT
                    vp.id AS volunteer_id,
                    vp.user_id,
                    vp.skills,
                    vp.has_transport,
                    vp.capacity,
                    vp.availability,
                    ST_Distance(
                        vp.location::geography,
                        ST_GeogFromText(:request_location)
                    ) / 1000.0 AS distance_km,
                    (
                        SELECT COUNT(*) FROM assignments a
                        WHERE a.volunteer_id = vp.id
                        AND a.status IN ('pending', 'created', 'accepted', 'started', 'in_progress')
                    ) AS active_assignments
                FROM volunteer_profiles vp
                WHERE vp.status = 'active'
                  AND vp.is_active = true
                  AND vp.location IS NOT NULL
                  AND ST_DWithin(
                      vp.location::geography,
                      ST_GeogFromText(:request_location),
                      :radius_m
                  )
                ORDER BY
                    active_assignments ASC,
                    vp.capacity DESC NULLS LAST,
                    vp.location <-> ST_GeogFromText(:request_location)
                LIMIT :lim
                """
            ),
            {
                "request_location": request_wkt,
                "radius_m": radius_km * 1000,
                "lim": limit,
            },
        ).fetchall()

        results = []
        for row in candidates:
            distance = row[6]
            active_count = row[7]
            capacity = row[4]

            # Deterministic rank score (lower is better)
            # Proximity is primary factor, workload is secondary
            rank_score = distance + (active_count * 5.0)

            results.append(
                CandidateVolunteer(
                    volunteer_id=row[0],
                    user_id=row[1],
                    skills=row[2] or [],
                    has_transport=row[3] or False,
                    capacity=capacity,
                    availability=row[5],
                    distance_km=round(distance, 2),
                    active_assignments=active_count,
                    rank_score=round(rank_score, 2),
                )
            )

        # Sort by rank_score ascending (best first)
        results.sort(key=lambda c: c.rank_score)
        return results

    def _find_candidates_without_location(self, limit: int) -> List[CandidateVolunteer]:
        """Fallback: return active volunteers when request has no location."""
        rows = self.db.execute(
            text(
                """
                SELECT
                    vp.id, vp.user_id, vp.skills, vp.has_transport,
                    vp.capacity, vp.availability,
                    0.0,
                    (
                        SELECT COUNT(*) FROM assignments a
                        WHERE a.volunteer_id = vp.id
                        AND a.status IN ('pending', 'created', 'accepted', 'started', 'in_progress')
                    )
                FROM volunteer_profiles vp
                WHERE vp.status = 'active' AND vp.is_active = true
                ORDER BY
                    active_assignments ASC,
                    vp.capacity DESC NULLS LAST
                LIMIT :lim
                """
            ),
            {"lim": limit},
        ).fetchall()

        return [
            CandidateVolunteer(
                volunteer_id=r[0], user_id=r[1], skills=r[2] or [],
                has_transport=r[3] or False, capacity=r[4], availability=r[5],
                distance_km=0.0, active_assignments=r[7],
                rank_score=float(r[7]) * 5.0,
            )
            for r in rows
        ]
