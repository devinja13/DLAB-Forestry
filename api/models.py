from pydantic import BaseModel
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime
from dataclasses import dataclass, field


class TreeType(str, Enum):
    gal3 = "3gal"
    gal5 = "5gal"
    gal10 = "10gal"


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"
    cancelled = "cancelled"


# --- Request ---

class RegionBbox(BaseModel):
    west: float   # lng min
    south: float  # lat min
    east: float   # lng max
    north: float  # lat max

class OptimizeRequest(BaseModel):
    budget: float
    tree_types: list[TreeType]
    region: RegionBbox


# --- Result ---

class CellResult(BaseModel):
    lng: float
    lat: float
    bbox: list[float]        # [west, south, east, north]
    trees_3gal: int
    trees_5gal: int
    trees_10gal: int
    total_trees: int
    total_cost: float
    cooling_delta: float     # degrees C reduction
    canopy_gain: float       # fractional canopy increase
    imperviousness: float    # 0.0–1.0

class OptimizeSummary(BaseModel):
    status: str              # "optimal", "time_limit", etc.
    runtime_s: float
    total_cells: int
    total_trees: int
    budget_used: float
    budget_remaining: float
    total_cooling_delta: float
    trees_by_type: dict[str, int]

class OptimizeResult(BaseModel):
    summary: OptimizeSummary
    cells: list[CellResult]


# --- Job ---

@dataclass
class Job:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.pending
    created_at: datetime = field(default_factory=datetime.utcnow)
    progress: int = 0          # 0–100
    result: Optional[OptimizeResult] = None
    error: Optional[str] = None


# --- API responses ---

class SubmitResponse(BaseModel):
    job_id: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    result: Optional[OptimizeResult] = None
    error: Optional[str] = None
