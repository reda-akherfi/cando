# app/models/tag.py
from dataclasses import dataclass

@dataclass
class Tag:
    id: int
    name: str
    linked_type: str  # 'project' or 'task'
    linked_id: int
