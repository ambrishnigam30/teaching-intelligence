from src.drive.crawler import DriveCrawler, FOLDER_MIME, SHORTCUT_MIME

class FakeDrive:
    def list_children(self, parent):
        data = {
          "root": [{"id": "shortcut", "name": "Allen", "mimeType": SHORTCUT_MIME, "shortcutDetails": {"targetId": "folder", "targetMimeType": FOLDER_MIME}}],
          "folder": [{"id": "pdf", "name": "bonding.pdf", "mimeType": "application/pdf"}],
        }
        return data[parent]
    def download(self, file_id): return b"source-bytes"
    def download_to(self, file_id, destination): destination.write_bytes(b"source-bytes")

def test_recursive_shortcut_dereference_preserves_root_without_eager_download():
    node = DriveCrawler(FakeDrive()).crawl(["root"])[0]
    assert node.file_id == "pdf" and node.source_root_id == "root" and node.content_hash is None
    assert node.virtual_path.endswith("Allen/bonding.pdf")
