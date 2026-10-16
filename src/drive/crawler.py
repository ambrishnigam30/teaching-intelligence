from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol

FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"

class DriveClient(Protocol):
    def list_children(self, parent_id: str) -> list[dict[str, Any]]: ...
    def download(self, file_id: str) -> bytes: ...

@dataclass(frozen=True)
class DriveNode:
    file_id: str
    name: str
    mime_type: str
    source_root_id: str
    virtual_path: str
    content_hash: str | None = None

class DriveCrawler:
    def __init__(self, client: DriveClient): self.client = client

    def crawl(self, roots: list[str]) -> list[DriveNode]:
        result: list[DriveNode] = []
        seen_edges: set[tuple[str, str]] = set()
        def visit(parent: str, root: str, path: str):
            for item in self.client.list_children(parent):
                target = item.get("shortcutDetails", {}).get("targetId") if item["mimeType"] == SHORTCUT_MIME else item["id"]
                target_mime = item.get("shortcutDetails", {}).get("targetMimeType") if item["mimeType"] == SHORTCUT_MIME else item["mimeType"]
                edge = (parent, target)
                if edge in seen_edges: continue
                seen_edges.add(edge)
                name = item.get("name", target)
                child_path = f"{path}/{name}"
                if target_mime == FOLDER_MIME:
                    visit(target, root, child_path)
                else:
                    blob = self.client.download(target)
                    result.append(DriveNode(target, name, target_mime, root, child_path, sha256(blob).hexdigest()))
        for root in roots: visit(root, root, root)
        return result

    @staticmethod
    def google_client(service: Any) -> DriveClient:
        class GoogleAdapter:
            def list_children(self, parent_id: str) -> list[dict[str, Any]]:
                files, token = [], None
                while True:
                    page = service.files().list(q=f"'{parent_id}' in parents and trashed = false", pageToken=token, fields="nextPageToken,files(id,name,mimeType,shortcutDetails,md5Checksum)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                    files.extend(page.get("files", [])); token = page.get("nextPageToken")
                    if not token: return files
            def download(self, file_id: str) -> bytes:
                from googleapiclient.http import MediaIoBaseDownload
                from io import BytesIO
                output = BytesIO(); request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
                downloader = MediaIoBaseDownload(output, request); done = False
                while not done: _, done = downloader.next_chunk()
                return output.getvalue()
        return GoogleAdapter()
