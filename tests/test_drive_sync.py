from src.config.rights import RightsRegistry
from src.drive.crawler import DriveCrawler
from src.drive.sync import discover_sources, work_items_for

class FakeDrive:
    def list_children(self, parent):
        return [{"id": "x", "name": "Allen Chemical Bonding Theory.pdf", "mimeType": "application/pdf"}] if parent == "1NhWXMQI5Kw421TGEsYCHXvPhmjRhS8lU" else []
    def download(self, file_id): return b"same"

def test_discovery_grants_registered_root_rights_and_maps_work():
    sources = discover_sources(DriveCrawler(FakeDrive()), RightsRegistry.load())
    source = next(s for s in sources if s.file_id == "x")
    assert source.rights_status == "FOUNDER_LICENSED_COMMERCIAL"
    assert source.archetype == "ALLEN_THEORY"
    assert source.chapters == ["chemical_bonding"]
    assert work_items_for(sources)[0].chapters == ["chemical_bonding"]
