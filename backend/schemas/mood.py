from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date

class MoodLogCreate(BaseModel):
    mood_score: int = Field(ge=1, le=5)
    notes: Optional[str] = Field(default=None, max_length=2000)

class MoodLogResponse(BaseModel):
    id: int
    date: date
    mood_score: int
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
