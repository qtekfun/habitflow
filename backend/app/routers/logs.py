"""
Logs router — /api/v1/logs
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.log import LogCreate, LogRead, StatsResponse
from app.services import habit_service, log_service
from app.services.log_service import DuplicateLogError

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.post("", response_model=LogRead, status_code=status.HTTP_201_CREATED)
async def checkin(
    body: LogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = await habit_service.get_habit(
        db=db, habit_id=body.habit_id, user_id=current_user.id
    )
    if habit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        )

    try:
        return await log_service.checkin(
            db=db,
            habit=habit,
            user=current_user,
            log_date=body.log_date,
            note=body.note,
        )
    except DuplicateLogError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def undo_checkin(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = await log_service.get_log(db=db, log_id=log_id, user_id=current_user.id)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Log not found"
        )
    await log_service.undo_checkin(db=db, log=log)


@router.get("/today")
async def today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await log_service.get_today_status(
        db=db, user_id=current_user.id, today=date.today()
    )


@router.get("/stats", response_model=StatsResponse)
async def stats(
    habit_id: uuid.UUID,
    from_date: date,
    to_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = await habit_service.get_habit(
        db=db, habit_id=habit_id, user_id=current_user.id
    )
    if habit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        )
    return await log_service.get_stats(
        db=db, habit=habit, from_date=from_date, to_date=to_date
    )
