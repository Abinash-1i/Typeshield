from typing import List, Optional

from pydantic import BaseModel, Field, validator


class BehaviourData(BaseModel):
    dwell_times: List[float] = Field(default_factory=list)
    flight_times: List[float] = Field(default_factory=list)
    total_time: float
    error_count: int = 0
    device_type: str = "fine"

    @validator("total_time")
    def validate_total_time(cls, v: float) -> float:
        if v < 0:
            raise ValueError("total_time must be non-negative")
        return v

    @validator("dwell_times", "flight_times", each_item=True)
    def validate_timing_values(cls, v: float) -> float:
        if v < 0:
            raise ValueError("timing values must be non-negative")
        return v


class RegisterRequest(BaseModel):
    username: str
    password: str
    behaviour: BehaviourData


class LoginRequest(BaseModel):
    username: str
    password: str
    behaviour: BehaviourData


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}
