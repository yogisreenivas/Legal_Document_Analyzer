"""
table_detector.py - Detects and parses tabular data in PDFs using pdfplumber / PyMuPDF.
Converts extracted matrices into schema-validated DetectedTable structures.
"""

from typing import List
from pathlib import Path
from app.models.schemas import DetectedTable
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TableDetector:
    @staticmethod
    def extract_tables(file_path: Path) -> List[DetectedTable]:
        """
        Scans PDF pages for tables, headers, and row structures.
        """
        detected_tables: List[DetectedTable] = []
        table_counter = 1

        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1
                    extracted_tables = page.extract_tables()

                    for tbl_idx, raw_table in enumerate(extracted_tables):
                        if not raw_table or len(raw_table) < 2:
                            continue

                        # Clean cell whitespace and handle None values
                        clean_rows = []
                        for row in raw_table:
                            clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                            # Only keep if row has at least one non-empty value
                            if any(clean_row):
                                clean_rows.append(clean_row)

                        if len(clean_rows) < 2:
                            continue

                        headers = clean_rows[0]
                        rows = clean_rows[1:]

                        # Generate clean table ID and caption
                        t_id = f"tbl_p{page_num}_{tbl_idx + 1}"
                        caption = f"Table on Page {page_num} ({len(headers)} columns × {len(rows)} rows)"

                        detected_tables.append(DetectedTable(
                            table_id=t_id,
                            page_number=page_num,
                            caption=caption,
                            headers=headers,
                            rows=rows
                        ))
                        table_counter += 1

            logger.info(f"Table detection complete: {len(detected_tables)} table(s) found.")
        except Exception as e:
            logger.warning(f"pdfplumber table extraction encountered an issue: {e}")

        return detected_tables
