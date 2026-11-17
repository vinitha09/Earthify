from typing import Literal
from pydantic import BaseModel, Field

class ExploreRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class SonifyRequest(ExploreRequest):
    duration: int = Field(default=30, ge=8, le=30)
    factors: list[Literal[
        "temperature", "rainfall", "wind", "humidity",
    ]] = Field(default_factory=list, max_length=8)
