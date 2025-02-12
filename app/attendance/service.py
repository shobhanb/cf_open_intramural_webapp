from __future__ import annotations

import logging

from sqlalchemy import select

from app.athlete.models import Athlete
from app.attendance.models import Attendance
from app.database.dependencies import db_dependency

log = logging.getLogger("uvicorn.error")


async def get_athlete_attendance_data(
    db_session: db_dependency,
) -> dict[str, dict[str, bool]]:
    stmt = (
        select(Athlete.name, Athlete.id, Attendance.ordinal, Attendance.event_name)
        .join_from(
            Athlete,
            Attendance,
            Athlete.id == Attendance.athlete_id,
            isouter=True,
        )
        .order_by(Athlete.name, Attendance.ordinal)
    )
    ret = await db_session.execute(stmt)
    results = ret.mappings().all()
    attendance = {}
    for row in results:
        id_ = row.get("id")
        name = row.get("name")
        ordinal = row.get("ordinal")
        if id_ and id_ not in attendance:
            attendance[id_] = {}
        if name:
            attendance[id_]["name"] = name
        if ordinal:
            attendance[id_][ordinal] = True

    return attendance
