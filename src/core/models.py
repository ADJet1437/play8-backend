from pydantic import BaseModel
from typing import List, TypeVar, Generic

T = TypeVar('T')

class PagedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    limit: int
    offset: int

class DeleteResponse(BaseModel):
    status: str
    id: str

