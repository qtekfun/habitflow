import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class LogCreate(BaseModel):
    habit_id: uuid.UUID
    log_date: date
    note: str | None = None


class LogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    habit_id: uuid.UUID
    user_id: uuid.UUID
    log_date: date
    completed: bool
    note: str | None


class StatsResponse(BaseModel):
    total_days: int
    completed_days: int
    completion_rate: float
    weekly_average: float
