"""Search domain Pydantic schemas."""

from typing import Any, Literal

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    type: Literal["parlor", "tournament"]
    data: dict[str, Any]