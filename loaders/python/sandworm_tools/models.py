from typing import Any
from pydantic import BaseModel


class ToolOption(BaseModel):
    label: str
    value: str


class ToolInput(BaseModel):
    key: str
    label: str
    type: str
    required: bool = False
    default: Any = None
    description: str | None = None
    placeholder: str | None = None
    options: list[ToolOption] | None = None
    min: float | None = None
    max: float | None = None


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
