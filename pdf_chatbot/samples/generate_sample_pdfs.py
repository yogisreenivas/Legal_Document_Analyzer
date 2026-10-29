"""
generate_sample_pdfs.py - Generates 3 synthetic test PDFs for the test suite:
1. sample_text_contract.pdf (Text-based legal agreement)
2. sample_financial_tables.pdf (Table-heavy quarterly financial report)
3. sample_scanned_receipt.pdf (Raster-based document to test OCR / scan diagnostics)
"""

import pymupdf as fitz
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

SAMPLES_DIR = Path(__file__).resolve().parent

def create_text_contract_pdf():
    pdf_path = SAMPLES_DIR / "sample_text_contract.pdf"
    doc = fitz.open()

    # Page 1
    p1 = doc.new_page(width=595, height=842)
    p1_text = """MASTER SOFTWARE SERVICES AGREEMENT

This Master Software Services Agreement (the "Agreement") is entered into as of October 1, 2024 (the "Effective Date"), by and between:
1. Apex Global Technologies Inc., a Delaware corporation having its principal office at 500 Tech Boulevard, San Francisco, CA ("Client"), and
2. NovaCloud Systems LLC, a California limited liability company having its office at 120 Innovation Way, San Jose, CA ("Vendor").

1. SCOPE OF SERVICES
Vendor shall provide cloud architecture consulting, AI document intelligence pipeline implementation, and DevOps managed services as outlined in Statement of Work #1.

2. FEES AND PAYMENT SCHEDULE
Client shall pay Vendor a fixed monthly retainer of $24,500 USD payable net-30 days upon invoice receipt. Late payments shall incur a service charge of 1.5% per month or the maximum rate permissible by law.

3. TERM AND TERMINATION
(a) Initial Term: This Agreement shall remain in effect for twelve (12) consecutive months from the Effective Date.
(b) Termination for Convenience: Either party may terminate this Agreement without cause upon providing sixty (60) days prior written notice to the other party.
(c) Termination for Cause: In the event of a material breach, the non-breaching party may terminate immediately upon thirty (30) days notice if uncured.
"""
    p1.insert_textbox(fitz.Rect(50, 50, 545, 780), p1_text, fontsize=11, fontname="helv")

    # Page 2
    p2 = doc.new_page(width=595, height=842)
    p2_text = """4. CONFIDENTIALITY AND INTELLECTUAL PROPERTY
(a) Confidentiality: Each party agrees to preserve all proprietary and technical information disclosed hereunder for five (5) years following termination.
(b) IP Ownership: All deliverables, customized models, and documentation created specifically for Client shall be deemed Work Made for Hire and solely owned by Client.

5. LIMITATION OF LIABILITY
Except for breaches of Section 4 (Confidentiality) or willful misconduct, neither party's aggregate liability under this Agreement shall exceed the total fees paid by Client during the preceding six (6) months ($147,000 USD).

6. GOVERNING LAW AND ARBITRATION
This Agreement shall be governed by the laws of the State of California. Any dispute arising out of this Agreement shall be finally settled by binding arbitration administered by JAMS in San Francisco, California.

IN WITNESS WHEREOF, the parties hereto have executed this Agreement as of the Effective Date.

APEX GLOBAL TECHNOLOGIES INC.               NOVACLOUD SYSTEMS LLC
By: Sarah Jenkins, VP of Engineering       By: Marcus Vance, Managing Director
Date: October 1, 2024                      Date: October 1, 2024
"""
    p2.insert_textbox(fitz.Rect(50, 50, 545, 780), p2_text, fontsize=11, fontname="helv")

    doc.save(str(pdf_path))
    doc.close()
    print(f"Generated: {pdf_path}")


def create_financial_tables_pdf():
    pdf_path = SAMPLES_DIR / "sample_financial_tables.pdf"
    doc = fitz.open()

    p1 = doc.new_page(width=595, height=842)
    header_text = """Q3 2024 CONSOLIDATED FINANCIAL PERFORMANCE REPORT
NovaCloud Systems Inc. — Investor Relations Statement
Published: November 15, 2024

Table 1: Quarterly Revenue Breakdown by Segment (in $ Millions)
-----------------------------------------------------------------------------------------
Segment                Q1 2024    Q2 2024    Q3 2024    YoY Growth (%)
-----------------------------------------------------------------------------------------
Enterprise Cloud       $42.5      $48.2      $56.4      +32.7%
AI Solutions           $18.1      $24.6      $35.8      +97.8%
Consulting & Support   $12.3      $13.1      $14.2      +15.4%
Hardware Systems       $8.4       $7.9       $7.1       -15.5%
-----------------------------------------------------------------------------------------
Total Consolidated     $81.3      $93.8      $113.5     +39.6%
-----------------------------------------------------------------------------------------

Key Highlights:
- Gross Profit Margin expanded to 68.4% in Q3 compared to 62.1% in Q3 2023.
- Operating Income reached $31.8 Million, reflecting strong operating leverage.
- Free Cash Flow for the nine months ended September 30, 2024 stood at $58.2 Million.
"""
    p1.insert_textbox(fitz.Rect(50, 50, 545, 780), header_text, fontsize=10, fontname="courier")

    p2 = doc.new_page(width=595, height=842)
    p2_text = """Table 2: Condensed Balance Sheet Summary as of September 30, 2024
-----------------------------------------------------------------------------------------
Assets & Liabilities (in Millions)    Sep 30, 2024    Dec 31, 2023
-----------------------------------------------------------------------------------------
Cash and Cash Equivalents             $142.6          $95.4
Short-term Marketable Securities       $65.0           $40.0
Accounts Receivable (Net)              $48.3           $39.1
Property and Equipment (Net)           $88.4           $76.2
Total Assets                           $344.3          $250.7

Current Liabilities                    $46.2           $38.5
Long-term Debt                         $50.0           $50.0
Total Stockholders' Equity             $248.1          $162.2
-----------------------------------------------------------------------------------------

Forward-Looking Guidance:
The Company expects full-year fiscal 2024 revenue between $440M and $450M with an adjusted EBITDA margin of approximately 28.5%.
"""
    p2.insert_textbox(fitz.Rect(50, 50, 545, 780), p2_text, fontsize=10, fontname="courier")

    doc.save(str(pdf_path))
    doc.close()
    print(f"Generated: {pdf_path}")


def create_scanned_receipt_pdf():
    """Generates an image-raster PDF that tests OCR and scanner detection diagnostics."""
    pdf_path = SAMPLES_DIR / "sample_scanned_receipt.pdf"
    
    # Create an image using PIL
    img = Image.new("RGB", (800, 1100), color=(250, 248, 240))
    d = ImageDraw.Draw(img)

    # Draw receipt lines
    d.text((80, 80), "OFFICIAL COMMERCIAL INVOICE & RECEIPT", fill=(30, 30, 30))
    d.text((80, 120), "Invoice #: INV-998240-2024", fill=(50, 50, 50))
    d.text((80, 150), "Date: October 12, 2024", fill=(50, 50, 50))
    d.text((80, 180), "Merchant: Global Logistics & Supply Hub", fill=(50, 50, 50))
    d.text((80, 210), "Ship To: Horizon Analytics, 42 Harbor Rd, Seattle WA", fill=(50, 50, 50))

    d.line([(80, 260), (720, 260)], fill=(120, 120, 120), width=2)
    d.text((80, 280), "Item Description             Qty    Unit Price    Total", fill=(20, 20, 20))
    d.line([(80, 310), (720, 310)], fill=(150, 150, 150), width=1)
    d.text((80, 330), "GPU Server Cluster Rack      1      $32,000.00    $32,000.00", fill=(40, 40, 40))
    d.text((80, 360), "100Gbps Fiber Network Switch 2      $4,500.00     $9,000.00", fill=(40, 40, 40))
    d.text((80, 390), "Installation & Cabling Pack  1      $1,850.00     $1,850.00", fill=(40, 40, 40))
    d.line([(80, 430), (720, 430)], fill=(120, 120, 120), width=2)
    d.text((80, 460), "Subtotal: $42,850.00", fill=(20, 20, 20))
    d.text((80, 490), "State Tax (8.5%): $3,642.25", fill=(20, 20, 20))
    d.text((80, 520), "Total Paid via Wire: $46,492.25 USD", fill=(10, 10, 10))
    d.text((80, 580), "Status: PAID IN FULL - TRANSACTION VERIFIED", fill=(0, 120, 0))

    # Convert to PDF
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(0, 0, 595, 842), stream=img_bytes.getvalue())
    doc.save(str(pdf_path))
    doc.close()
    print(f"Generated: {pdf_path}")


if __name__ == "__main__":
    create_text_contract_pdf()
    create_financial_tables_pdf()
    create_scanned_receipt_pdf()
