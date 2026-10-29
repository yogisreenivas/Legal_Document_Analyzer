"""
extractor.py - High-precision PDF text extraction, OCR fallback, and page rendering.
Uses PyMuPDF (fitz) for fast vector extraction and coordinate mapping.
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
import pymupdf as fitz
from PIL import Image
import io

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExtractedPage:
    def __init__(
        self,
        page_number: int,
        text: str,
        blocks: List[Dict[str, Any]],
        is_ocr: bool = False,
        width: float = 0.0,
        height: float = 0.0,
        raster_path: str = ""
    ):
        self.page_number = page_number
        self.text = text
        self.blocks = blocks  # List of {bbox: [x0, y0, x1, y1], text: str}
        self.is_ocr = is_ocr
        self.width = width
        self.height = height
        self.raster_path = raster_path


class PDFExtractor:
    def __init__(self, tesseract_cmd: str = None):
        self.tesseract_cmd = tesseract_cmd or settings.TESSERACT_CMD

    def extract_document(self, file_path: Path, document_id: str) -> Tuple[List[ExtractedPage], Dict[str, Any]]:
        """
        Extracts all pages from the PDF file:
        - Text and coordinate blocks
        - OCR fallback if page has minimal native text
        - High-resolution page raster for viewer thumbnails
        """
        logger.info(f"Extracting PDF: {file_path.name} (doc_id: {document_id})")

        doc = fitz.open(file_path)
        page_count = len(doc)
        pages: List[ExtractedPage] = []
        scanned_count = 0
        ocr_applied = False
        quality_notes = []

        pages_storage_dir = settings.PAGES_DIR / document_id
        pages_storage_dir.mkdir(parents=True, exist_ok=True)

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]
            rect = page.rect
            width, height = rect.width, rect.height

            # Render page image to disk for thumbnail & fallback viewing
            pix = page.get_pixmap(dpi=150)
            raster_file = pages_storage_dir / f"page_{page_num}.png"
            pix.save(str(raster_file))

            # 1. Native text extraction
            raw_text = page.get_text("text").strip()
            
            # 2. Extract block coordinates (x0, y0, x1, y1, text, block_no)
            blocks_data = []
            page_dict = page.get_text("blocks")
            for b in page_dict:
                # b format: (x0, y0, x1, y1, text, block_no, block_type)
                if len(b) >= 5 and b[4].strip():
                    blocks_data.append({
                        "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)],
                        "text": b[4].strip()
                    })

            is_ocr_page = False
            # Check if text is sparse (indicative of scanned / image-based page)
            if len(raw_text) < settings.MIN_TEXT_CHARS_PER_PAGE:
                logger.info(f"Page {page_num} text length ({len(raw_text)}) below threshold. Attempting OCR fallback...")
                scanned_count += 1
                ocr_text = self._try_ocr(pix)
                if ocr_text and len(ocr_text) > len(raw_text):
                    raw_text = ocr_text
                    is_ocr_page = True
                    ocr_applied = True
                    blocks_data = [{
                        "bbox": [0, 0, width, height],
                        "text": ocr_text
                    }]

            pages.append(ExtractedPage(
                page_number=page_num,
                text=raw_text,
                blocks=blocks_data,
                is_ocr=is_ocr_page,
                width=width,
                height=height,
                raster_path=str(raster_file)
            ))

        doc.close()

        # Compile quality diagnostics
        is_primarily_scanned = (scanned_count / page_count) > 0.5 if page_count > 0 else False
        confidence = 0.75 if ocr_applied else 0.98

        if is_primarily_scanned:
            quality_notes.append("Scanned image PDF detected. Processed using OCR rasterization.")
        else:
            quality_notes.append("High quality vector digital PDF. Native text and coordinates extracted.")

        if ocr_applied and not is_primarily_scanned:
            quality_notes.append(f"Mixed format document: {scanned_count} page(s) required OCR fallback.")

        audit = {
            "page_count": page_count,
            "is_scanned": is_primarily_scanned,
            "ocr_applied": ocr_applied,
            "confidence_score": confidence,
            "quality_notes": quality_notes
        }

        logger.info(f"Extraction complete for {document_id}: {page_count} pages processed.")
        return pages, audit

    def _try_ocr(self, pix: fitz.Pixmap) -> str:
        """Fallback to Tesseract OCR when native text is missing."""
        try:
            import pytesseract
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.warning(f"Tesseract OCR fallback unavailable or encountered error: {e}")
            return ""
