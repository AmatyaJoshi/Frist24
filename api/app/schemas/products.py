from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    lifecycle_status: str = Field(default="active", pattern="^(active|discontinued)$")
    placed_on_market_at: date | None = None


class SbomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    format: str
    spec_version: str | None
    filename: str | None
    sha256: str
    component_count: int
    uploaded_at: datetime


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    sku: str
    name: str
    description: str | None
    lifecycle_status: str
    placed_on_market_at: date | None
    created_at: datetime
    sboms: list[SbomOut] = []
    component_count: int = 0
    open_incidents: int = 0


class ComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    version: str | None
    purl: str | None
    ecosystem: str | None
    cpe: str | None
    supplier: str | None


class SbomUploadResult(BaseModel):
    sbom: SbomOut
    created: bool
    message: str
