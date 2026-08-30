from typing import Any
from pydantic import BaseModel


class ToolInput(BaseModel):
    key: str
    label: str
    type: str
    required: bool = False
    default: Any = None


class ToolReturn(BaseModel):
    name: str
    type: str


class Tool(BaseModel):
    tool_id: str
    g1: str
    g2: str | None = None
    g3: str | None = None
    g4: str | None = None
    g5: str | None = None
    description: str
    scope: str = "generic"
    returns: list[ToolReturn] = []
    inputs: list[ToolInput] = []


class Category(BaseModel):
    category_id: str
    name: str
    description: str
