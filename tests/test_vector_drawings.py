"""Test PyMuPDF vector drawing clustering, bounding box normalization, and diagram asset generation."""
import fitz
from src.extraction.vector_diagrams import (
    cluster_drawings,
    extract_page_diagrams,
    normalize_bbox,
)

def test_vector_drawing_clustering_and_bounding_boxes():
    # Create an in-memory PDF document with vector drawings
    doc = fitz.open()
    page = doc.new_page(width=500, height=800)

    # Draw a physics block on an inclined plane (vector paths)
    shape = page.new_shape()
    shape.draw_line(fitz.Point(100, 400), fitz.Point(300, 200))  # Incline
    shape.draw_rect(fitz.Rect(180, 260, 240, 320))               # Block
    shape.finish(color=(0, 0, 0), width=2)
    shape.commit()

    # Draw a separate diagram (e.g. circle for pulley)
    shape2 = page.new_shape()
    shape2.draw_circle(fitz.Point(350, 180), 30)
    shape2.finish(color=(1, 0, 0), width=1.5)
    shape2.commit()

    # Cluster drawings
    clusters = cluster_drawings(page, min_dim=30.0)
    assert len(clusters) >= 1

    # Normalize bounding box
    bbox = normalize_bbox(clusters[0], page.rect)
    assert len(bbox) == 4
    ymin, xmin, ymax, xmax = bbox
    assert 0 <= ymin <= ymax <= 1000
    assert 0 <= xmin <= xmax <= 1000

    # Test full extraction
    diagrams = extract_page_diagrams(doc, 0, "test_file_id", dpi=150)
    assert len(diagrams) >= 1
    d = diagrams[0]
    assert d.source_file_id == "test_file_id"
    assert d.page_number == 1
    assert d.diagram_type == "VECTOR_DRAWING"
    assert len(d.image_bytes) > 0
    assert d.image_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # Valid PNG signature

    doc.close()
