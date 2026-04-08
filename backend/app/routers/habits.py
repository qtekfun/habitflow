"""
Habits router — /api/v1/habits
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.habit import HabitCreate, HabitDetail, HabitRead, HabitUpdate
from app.services import habit_service

router = APIRouter(prefix="/api/v1/habits", tags=["habits"])


@router.get("", response_model=list[HabitRead])
async def list_habits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await habit_service.list_habits(db=db, user_id=current_user.id)


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
async def create_habit(
    body: HabitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await habit_service.create_habit(
        db=db,
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        frequency=body.frequency,
        target_days=body.target_days,
        color=body.color,
        icon=body.icon,
        notify_time=body.notify_time,
    )


@router.get("/{habit_id}", response_model=HabitDetail)
async def get_habit(
    habit_id: uuid.UUID,
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
    current_streak = await habit_service.calculate_streak(
        db=db, habit=habit, user_timezone=current_user.timezone
    )
    longest_streak = await habit_service.calculate_longest_streak(db=db, habit=habit)
    return HabitDetail(
        **HabitRead.model_validate(habit).model_dump(),
        current_streak=current_streak,
        longest_streak=longest_streak,
    )


@router.patch("/{habit_id}", response_model=HabitRead)
async def update_habit(
    habit_id: uuid.UUID,
    body: HabitUpdate,
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
    return await habit_service.update_habit(
        db=db,
        habit=habit,
        **{k: v for k, v in body.model_dump().items() if v is not None},
    )


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(
    habit_id: uuid.UUID,
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
    await habit_service.delete_habit(db=db, habit=habit)
