from pydantic import BaseModel


class BookingBase(BaseModel):
    machine_id: str
    start_time: str
    end_time: str | None = None
    status: str


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    user_id: str | None = None
    machine_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    status: str | None = None


class BookingResponse(BaseModel):
    id: str
    user_id: str
    machine_id: str
    start_time: str
    end_time: str | None = None
    status: str


class Booking(BookingResponse):
    pass
