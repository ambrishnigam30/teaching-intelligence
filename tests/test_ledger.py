import pytest
from src.corpus.ledger import CorpusLedger, WorkItem
from src.models.contracts import AssuranceGate

def test_queue_finishes_tier_one_chapters_before_tier_two():
    ledger = CorpusLedger([
        WorkItem("optics", ["ray_optics"]),
        WorkItem("bonding-theory", ["chemical_bonding"]),
        WorkItem("bonding-exercise", ["chemical_bonding"]),
    ])
    assert [x.file_id for x in ledger.next_batch(3)][:2] == ["bonding-exercise", "bonding-theory"]

def test_gates_are_monotonic_and_quarantine_blocks_promotion():
    ledger = CorpusLedger([WorkItem("a", ["shm"])])
    ledger.transition("a", AssuranceGate.SOURCE_READY)
    with pytest.raises(ValueError): ledger.transition("a", AssuranceGate.KNOWLEDGE_READY)
    ledger.quarantine("a")
    with pytest.raises(ValueError): ledger.transition("a", AssuranceGate.EVIDENCE_READY)


def test_deterministic_sharding_partitions_without_overlap():
    items = [WorkItem(f"pdf_{i}", ["ray_optics"]) for i in range(60)]
    ledger = CorpusLedger(items)

    shard_count = 3
    shards: dict[int, list[str]] = {}
    for idx in range(shard_count):
        batch = ledger.next_batch(100, shard_index=idx, shard_count=shard_count)
        shards[idx] = [item.file_id for item in batch]

    # 1. Shards must be disjoint (zero overlap)
    set0, set1, set2 = set(shards[0]), set(shards[1]), set(shards[2])
    assert set0.isdisjoint(set1)
    assert set1.isdisjoint(set2)
    assert set0.isdisjoint(set2)

    # 2. Union must cover all 60 items
    all_sharded = set0 | set1 | set2
    assert len(all_sharded) == 60
    assert all_sharded == {f"pdf_{i}" for i in range(60)}


def test_next_batch_status_ranking_and_exclude_ids():
    item_quota = WorkItem("doc-quota", ["ray_optics"], status="PENDING_QUOTA")
    item_pending = WorkItem("doc-pending", ["ray_optics"], status="PENDING")
    item_partial = WorkItem("doc-partial", ["ray_optics"], status="PARTIAL")
    ledger = CorpusLedger([item_quota, item_pending, item_partial])

    # Rank priority: PARTIAL -> PENDING -> PENDING_QUOTA
    batch = ledger.next_batch(3)
    assert [x.file_id for x in batch] == ["doc-partial", "doc-pending", "doc-quota"]

    # Exclude IDs filter
    batch_excluded = ledger.next_batch(3, exclude_ids={"doc-partial", "doc-pending"})
    assert [x.file_id for x in batch_excluded] == ["doc-quota"]

