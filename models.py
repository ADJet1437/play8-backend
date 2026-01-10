from pydantic import BaseModel
from typing import Optional, List, TypeVar, Generic

T = TypeVar('T')

class PagedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    limit: int
    offset: int

class DeleteResponse(BaseModel):
    status: str
    id: str

class BookingBase(BaseModel):
    user_id: str
    machine_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    user_id: Optional[str] = None
    machine_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None

class Booking(BookingBase):
    id: str

class MachineBase(BaseModel):
    name: str
    location: str
    status: str

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class Machine(MachineBase):
    id: str
