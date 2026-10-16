from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Iterable

from src.corpus.chapter_mapper import ChapterMapper
from src.models.contracts import AssuranceGate

@dataclass
class WorkItem:
    file_id: str
    chapters: list[str]
    gate: int = int(AssuranceGate.DISCOVERED)
    status: str = "PENDING"
    attempts: int = 0
    virtual_paths: list[str] = field(default_factory=list)
    name: str = ""
    mime_type: str = "application/pdf"
    source_root_id: str = ""
    completed_pages: int = 0
    total_pages: int | None = None
    last_error: str | None = None

class CorpusLedger:
    def __init__(self, items: Iterable[WorkItem] = (), mapper: ChapterMapper | None = None):
        self.mapper = mapper or ChapterMapper()
        self.items = {item.file_id: item for item in items}

    def upsert(self, item: WorkItem) -> None:
        previous = self.items.get(item.file_id)
        if previous:
            item.gate = max(item.gate, previous.gate)
            item.status = previous.status
            item.attempts = previous.attempts
            item.completed_pages = previous.completed_pages
            item.total_pages = previous.total_pages
            item.last_error = previous.last_error
        self.items[item.file_id] = item

    def next_batch(self, limit: int) -> list[WorkItem]:
        candidates = [i for i in self.items.values() if i.status in {"PENDING", "PARTIAL", "PENDING_QUOTA"}]
        incomplete = {c for i in candidates for c in i.chapters}
        def key(item: WorkItem):
            chapter_key = self.mapper.work_key([c for c in item.chapters if c in incomplete])
            return (chapter_key, item.gate, item.file_id)
        return sorted(candidates, key=key)[:limit]

    def transition(self, file_id: str, target: AssuranceGate, status: str = "PENDING") -> WorkItem:
        item = self.items[file_id]
        if item.status == "QUARANTINED":
            raise ValueError("quarantined work cannot be promoted")
        if int(target) < item.gate or int(target) > item.gate + 1:
            raise ValueError("assurance gates must advance exactly one step")
        item.gate, item.status = int(target), status
        return item

    def quarantine(self, file_id: str) -> WorkItem:
        item = self.items[file_id]
        item.status = "QUARANTINED"
        return item

    def to_json(self) -> str:
        return json.dumps({"schema_version": 1, "items": [asdict(x) for x in self.items.values()]}, indent=2, sort_keys=True)

    @classmethod
    def from_path(cls, path: Path, mapper: ChapterMapper | None = None) -> "CorpusLedger":
        if not path.exists(): return cls(mapper=mapper)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls((WorkItem(**item) for item in data["items"]), mapper)
