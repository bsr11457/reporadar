from pydantic import BaseModel, Field
from typing import List

class FileInfo(BaseModel):
    path: str
    language: str
    bytes: int
    lines: int
    has_docstring: bool = False

class ProjectSummary(BaseModel):
    file_count: int
    python_files: int
    languages: dict
    dependencies: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    has_tests: bool
    documentation_coverage: float
    large_files: List[str] = Field(default_factory=list)
