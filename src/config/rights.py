from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

FOUNDER_LICENSED_COMMERCIAL = "FOUNDER_LICENSED_COMMERCIAL"
UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class RightsRegistry:
    roots: dict[str, str]
    file_overrides: dict[str, str]

    @classmethod
    def load(cls, path: Path | None = None) -> "RightsRegistry":
        path = path or Path(__file__).with_name("rights_registry.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data["roots"], data.get("file_overrides", {}))

    def status_for(self, file_id: str, source_root_id: str | None, external_url: str | None = None) -> str:
        if file_id in self.file_overrides:
            return self.file_overrides[file_id]
        if source_root_id in self.roots:
            return self.roots[source_root_id]
        return UNKNOWN
