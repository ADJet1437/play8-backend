from typing import Literal, Optional

from pydantic import BaseModel, EmailStr


class WaitingListRequest(BaseModel):
    email: EmailStr
    plan: Literal["week", "month"]
    message: Optional[str] = None


class WaitingListResponse(BaseModel):
    message: str
