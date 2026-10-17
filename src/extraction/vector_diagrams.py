"""Vector and raster diagram extraction and 2D bounding box generation."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any
import fitz  # PyMuPDF


@dataclass(frozen=True)
class DiagramAsset:
    asset_id: str
    source_file_id: str
    page_number: int
    bounding_box: list[int]  # [ymin, xmin, ymax, xmax] in 0..1000 scale
    diagram_type: str        # "RASTER" | "VECTOR_DRAWING"
    image_bytes: bytes


def normalize_bbox(rect: fitz.Rect, page_rect: fitz.Rect) -> list[int]:
    """Normalize PyMuPDF Rect to [ymin, xmin, ymax, xmax] scaled 0 to 1000."""
    p_w = max(1.0, float(page_rect.width))
    p_h = max(1.0, float(page_rect.height))
    ymin = max(0, min(1000, int((rect.y0 / p_h) * 1000)))
    xmin = max(0, min(1000, int((rect.x0 / p_w) * 1000)))
    ymax = max(0, min(1000, int((rect.y1 / p_h) * 1000)))
    xmax = max(0, min(1000, int((rect.x1 / p_w) * 1000)))
    return [ymin, xmin, ymax, xmax]


def cluster_drawings(page: fitz.Page, min_dim: float = 40.0) -> list[fitz.Rect]:
    """Group connected vector paths into unified diagram bounding boxes, ignoring borders/rules."""
    page_rect = page.rect
    drawings = page.get_drawings()
    if not drawings:
        return []

    candidate_rects: list[fitz.Rect] = []
    for d in drawings:
        r = d.get("rect")
        if not r:
            continue
        rect = fitz.Rect(r)
        # Filter out full page borders or full width dividing lines
        if rect.width >= page_rect.width * 0.95 and rect.height < 10.0:
            continue
        if rect.height >= page_rect.height * 0.95 and rect.width < 10.0:
            continue
        if rect.width < 15.0 and rect.height < 15.0:
            continue
        candidate_rects.append(rect)

    if not candidate_rects:
        return []

    # Merge overlapping or touching rectangles within 12pt tolerance
    clusters: list[fitz.Rect] = []
    tolerance = 12.0
    for rect in candidate_rects:
        merged = False
        expanded = fitz.Rect(rect.x0 - tolerance, rect.y0 - tolerance, rect.x1 + tolerance, rect.y1 + tolerance)
        for i, existing in enumerate(clusters):
            if existing.intersects(expanded):
                clusters[i] = existing | rect
                merged = True
                break
        if not merged:
            clusters.append(rect)

    # Filter clusters by minimum dimensions to ensure they are substantive diagrams
    return [c for c in clusters if c.width >= min_dim and c.height >= min_dim]


def extract_page_diagrams(
    document: fitz.Document,
    page_number: int,
    source_file_id: str,
    dpi: int = 300,
) -> list[DiagramAsset]:
    """Extract both embedded raster images and clustered vector drawing paths with bounding boxes."""
    page = document[page_number]
    page_rect = page.rect
    diagrams: list[DiagramAsset] = []
    seen_bboxes: list[fitz.Rect] = []

    # 1. Raster image extraction
    for img_idx, img_info in enumerate(page.get_images(full=True), start=1):
        try:
            xref = img_info[0]
            extracted = document.extract_image(xref)
            w, h = extracted.get("width", 0), extracted.get("height", 0)
            if w >= 64 and h >= 64:
                # Find image placement rect on page if available
                img_rects = page.get_image_rects(xref)
                rect = img_rects[0] if img_rects else fitz.Rect(0, 0, page_rect.width, page_rect.height)
                bbox = normalize_bbox(rect, page_rect)
                asset_id = f"{source_file_id}_p{page_number+1:04}_raster_{img_idx:02}"
                diagrams.append(
                    DiagramAsset(
                        asset_id=asset_id,
                        source_file_id=source_file_id,
                        page_number=page_number + 1,
                        bounding_box=bbox,
                        diagram_type="RASTER",
                        image_bytes=extracted["image"],
                    )
                )
                seen_bboxes.append(rect)
        except Exception:
            continue

    # 2. Vector drawing extraction & rasterization
    vector_clusters = cluster_drawings(page)
    for v_idx, cluster in enumerate(vector_clusters, start=1):
        # Skip if vector cluster completely overlaps an already extracted raster image
        if any(cluster.intersects(r) and (cluster & r).get_area() > 0.8 * cluster.get_area() for r in seen_bboxes):
            continue

        try:
            clip_rect = cluster & page_rect
            if clip_rect.is_empty or clip_rect.width < 30 or clip_rect.height < 30:
                continue
            pix = page.get_pixmap(clip=clip_rect, dpi=dpi, alpha=False)
            img_bytes = pix.tobytes("png")
            bbox = normalize_bbox(clip_rect, page_rect)
            asset_id = f"{source_file_id}_p{page_number+1:04}_vector_{v_idx:02}"
            diagrams.append(
                DiagramAsset(
                    asset_id=asset_id,
                    source_file_id=source_file_id,
                    page_number=page_number + 1,
                    bounding_box=bbox,
                    diagram_type="VECTOR_DRAWING",
                    image_bytes=img_bytes,
                )
            )
            seen_bboxes.append(clip_rect)
        except Exception:
            continue

    return diagrams
