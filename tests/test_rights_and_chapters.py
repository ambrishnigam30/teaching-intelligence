from src.config.rights import FOUNDER_LICENSED_COMMERCIAL, UNKNOWN, RightsRegistry
from src.corpus.chapter_mapper import ChapterMapper, ChapterPriority, SPINE

def test_founder_roots_are_commercial_and_external_is_unknown():
    registry = RightsRegistry.load()
    assert len(registry.roots) == 13
    root = next(iter(registry.roots))
    assert registry.status_for("file", root) == FOUNDER_LICENSED_COMMERCIAL
    assert registry.status_for("web-file", None, "https://example.org/book") == UNKNOWN

def test_spine_has_82_chapters_and_priority_is_explicit():
    mapper = ChapterMapper()
    assert len(SPINE) == 82
    assert mapper.priority("shm") == ChapterPriority.TIER_0
    assert mapper.priority("chemical_bonding") == ChapterPriority.TIER_0
    assert mapper.priority("kinematics") == ChapterPriority.TIER_1
    assert mapper.priority("ray_optics") == ChapterPriority.TIER_2
    assert mapper.priority("solid_state") == ChapterPriority.TIER_3
    assert mapper.map_text("Allen Simple Harmonic Motion module") == ["shm"]
    assert mapper.map_text("Resonance Rotational Mechanics RBD sheet") == ["rotational_mechanics"]
    assert mapper.map_text("GOC and Reaction Mechanism notes") == ["general_organic_chemistry"]
