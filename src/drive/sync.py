from __future__ import annotations

from collections import defaultdict
from src.config.rights import RightsRegistry
from src.corpus.chapter_mapper import ChapterMapper
from src.corpus.classifier import classify_file
from src.corpus.ledger import WorkItem
from src.drive.crawler import DriveCrawler, DriveNode
from src.models.contracts import SourceFile

def discover_sources(crawler: DriveCrawler, registry: RightsRegistry | None = None, mapper: ChapterMapper | None = None) -> list[SourceFile]:
    registry, mapper = registry or RightsRegistry.load(), mapper or ChapterMapper()
    grouped: dict[str, list[DriveNode]] = defaultdict(list)
    for node in crawler.crawl(list(registry.roots)):
        grouped[node.content_hash or node.file_id].append(node)
    sources = []
    for nodes in grouped.values():
        canonical = nodes[0]
        sources.append(SourceFile(
            file_id=canonical.file_id, name=canonical.name, source_root_id=canonical.source_root_id,
            virtual_paths=sorted(node.virtual_path for node in nodes), sha256=canonical.content_hash,
            rights_status=registry.status_for(canonical.file_id, canonical.source_root_id),
            archetype=classify_file(canonical.name, canonical.virtual_path),
            chapters=mapper.map_text(" ".join([canonical.name, *[node.virtual_path for node in nodes]])),
        ))
    return sources

def work_items_for(sources: list[SourceFile]) -> list[WorkItem]:
    return [WorkItem(file_id=s.file_id, chapters=s.chapters, virtual_paths=s.virtual_paths) for s in sources if s.rights_status != "UNKNOWN"]
