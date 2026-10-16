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
