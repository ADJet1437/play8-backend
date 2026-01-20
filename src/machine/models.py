from pydantic import BaseModel


class MachineBase(BaseModel):
    name: str
    location: str
    status: str


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    status: str | None = None


class Machine(MachineBase):
    id: str
