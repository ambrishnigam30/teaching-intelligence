from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Protocol

FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
PDF_MIME = "application/pdf"


class DriveClient(Protocol):
    def list_children(self, parent_id: str) -> list[dict[str, Any]]: ...
    def download(self, file_id: str) -> bytes: ...
    def download_to(self, file_id: str, destination: Path) -> None: ...


@dataclass(frozen=True)
class CrawlStats:
    folders: int = 0
    shortcuts: int = 0
    files: int = 0
    pdfs: int = 0


@dataclass(frozen=True)
class DriveNode:
    file_id: str
    name: str
    mime_type: str
    source_root_id: str
    virtual_path: str
    content_hash: str | None = None
    size_bytes: int | None = None


class DriveCrawler:
    def __init__(self, client: DriveClient): self.client = client

    def crawl(self, roots: list[str]) -> list[DriveNode]:
        return self.crawl_with_stats(roots)[0]

    def crawl_with_stats(self, roots: list[str]) -> tuple[list[DriveNode], CrawlStats]:
        result: list[DriveNode] = []
        seen_targets: set[str] = set()
        folders = shortcuts = files = pdfs = 0

        def visit(parent: str, root: str, path: str) -> None:
            nonlocal folders, shortcuts, files, pdfs
            for item in self.client.list_children(parent):
                is_shortcut = item.get("mimeType") == SHORTCUT_MIME
                target = item.get("shortcutDetails", {}).get("targetId") if is_shortcut else item["id"]
                target_mime = item.get("shortcutDetails", {}).get("targetMimeType") if is_shortcut else item["mimeType"]
                if not target: continue
                if is_shortcut: shortcuts += 1
                name = item.get("name", target)
                child_path = f"{path}/{name}"
                if target_mime == FOLDER_MIME:
                    if target in seen_targets: continue
                    seen_targets.add(target); folders += 1
                    visit(target, root, child_path)
                else:
                    files += 1; pdfs += target_mime == PDF_MIME
                    result.append(DriveNode(target, name, target_mime, root, child_path, item.get("md5Checksum"), int(item["size"]) if item.get("size") else None))
        for root in roots:
            seen_targets.add(root)
            visit(root, root, root)
        return result, CrawlStats(folders, shortcuts, files, pdfs)

    @staticmethod
    def google_client(service: Any) -> DriveClient:
        class GoogleAdapter:
            def list_children(self, parent_id: str) -> list[dict[str, Any]]:
                files, token = [], None
                while True:
                    page = service.files().list(q=f"'{parent_id}' in parents and trashed = false", pageToken=token, pageSize=1000, fields="nextPageToken,files(id,name,mimeType,shortcutDetails,md5Checksum,size)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                    files.extend(page.get("files", [])); token = page.get("nextPageToken")
                    if not token: return files
            def download(self, file_id: str) -> bytes:
                output = BytesIO(); self.download_to(file_id, output); return output.getvalue()
            def download_to(self, file_id: str, destination: Path | BytesIO) -> None:
                from googleapiclient.http import MediaIoBaseDownload
                output = destination.open("wb") if isinstance(destination, Path) else destination
                try:
                    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
                    downloader = MediaIoBaseDownload(output, request); done = False
                    while not done: _, done = downloader.next_chunk()
                finally:
                    if isinstance(destination, Path): output.close()
        return GoogleAdapter()

    def download_verified(self, node: DriveNode, destination: Path) -> str:
        self.client.download_to(node.file_id, destination)
        if not destination.exists() or destination.stat().st_size == 0: raise RuntimeError(f"Drive download was empty: {node.file_id}")
        return sha256(destination.read_bytes()).hexdigest()
