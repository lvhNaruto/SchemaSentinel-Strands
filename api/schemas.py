"""Pydantic request/response schemas for the SchemaSentinel API layer."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    mode: str = Field(default="preset", description='"preset" or "custom"')
    topics: List[str] = Field(default_factory=list)
    query: Optional[str] = None


class TestPayloadRequest(BaseModel):
    payload: Any = Field(..., description="Arbitrary JSON payload to heal or quarantine")


class RunResponse(BaseModel):
    accepted: bool
    detail: str


class ResetRequest(BaseModel):
    clear_warehouse: bool = True
