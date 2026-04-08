import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict


class HabitCreate(BaseModel):
    name: str
    description: str | None = None
    color: str = "#6366f1"
    icon: str = "check"
    frequency: str = "daily"
    target_days: list[int] = [1, 2, 3, 4, 5, 6, 7]
    notify_time: time | None = None


class HabitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    color: str
    icon: str
    frequency: str
    target_days: list[int]
    notify_time: time | None
    is_active: bool
    sort_order: int


class HabitDetail(HabitRead):
    """Single-habit response that includes computed streak fields."""

    current_streak: int
    longest_streak: int


class HabitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    frequency: str | None = None
    target_days: list[int] | None = None
    notify_time: time | None = None
    is_active: bool | None = None
