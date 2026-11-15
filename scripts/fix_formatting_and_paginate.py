import docx
from docx.shared import Pt, Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re
import os
import shutil
import subprocess

def set_run_font(run, name="Times New Roman", size_pt=None, bold=None, italic=None):
    run.font.name = name
    if size_pt is not None:
        run.font.size = Pt(size_pt)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic

def clean_paragraph_heading(p, new_text, font_size):
    p.text = new_text
    for r in p.runs:
        set_run_font(r, name="Times New Roman", size_pt=font_size, bold=True)

def disable_numbering(p):
    pPr = p._p.get_or_add_pPr()
    numPr = pPr.find(qn('w:numPr'))
    if numPr is None:
        numPr = OxmlElement('w:numPr')
        pPr.append(numPr)
    else:
        numPr.clear()
    
    ilvl = OxmlElement('w:ilvl')
    ilvl.set(qn('w:val'), '0')
    numPr.append(ilvl)
    
    numId = OxmlElement('w:numId')
    numId.set(qn('w:val'), '0')
    numPr.append(numId)

def process_document():
    doc_path = "docs/Báo cáo SOA.docx"
    print(f"Loading {doc_path}...")
    doc = docx.Document(doc_path)
    
    # 1. Front Matter Page Breaks
    for i, p in enumerate(doc.paragraphs[:100]):
        txt = p.text.strip()
        if txt == "LỜI CẢM ƠN":
            p.paragraph_format.page_break_before = True
            print(f"Set page_break_before on Lời cảm ơn (P{i})")
        elif "CÔNG TRÌNH ĐƯỢC HOÀN THÀNH" in txt:
            p.paragraph_format.page_break_before = True
            print(f"Set page_break_before on Lời cam đoan (P{i})")
        elif txt == "MỤC LỤC":
            p.paragraph_format.page_break_before = True
            print(f"Set page_break_before on Mục lục (P{i})")

    # 2. Fix Headings
    h1_count = 0
    h2_count = 0
    h3_count = 0
    
    for i, p in enumerate(doc.paragraphs):
        # We only care about headings after the TOC (index > 75)
        if i < 75:
            continue
            
        style = p.style.name
        txt = p.text.strip()
        
        if style == "Heading 1":
            p.paragraph_format.page_break_before = True
            if "TÀI LIỆU THAM KHẢO" in txt:
                clean_paragraph_heading(p, "TÀI LIỆU THAM KHẢO", font_size=16)
                disable_numbering(p)
                print(f"P{i} [Heading 1 - Unnumbered]: TÀI LIỆU THAM KHẢO (page_break=True)")
            else:
                # Strip 'CHƯƠNG X. ' prefix if present
                clean_txt = re.sub(r'^CHƯƠNG\s+\d+\.\s*', '', txt, flags=re.IGNORECASE)
                clean_paragraph_heading(p, clean_txt, font_size=16)
                h1_count += 1
                print(f"P{i} [Heading 1]: '{clean_txt}' (page_break=True)")
                
        elif style == "Heading 2":
            # Strip 'X.Y ' prefix if present
            clean_txt = re.sub(r'^\d+\.\d+\s*', '', txt)
            clean_paragraph_heading(p, clean_txt, font_size=14)
            h2_count += 1
            print(f"P{i} [Heading 2]: '{clean_txt}'")
            
        elif style == "Heading 3":
            # Strip 'X.Y.Z ' prefix if present
            clean_txt = re.sub(r'^\d+\.\d+\.\d+\s*', '', txt)
            clean_paragraph_heading(p, clean_txt, font_size=13)
            h3_count += 1
            print(f"P{i} [Heading 3]: '{clean_txt}'")

    print(f"Processed: {h1_count} Heading 1, {h2_count} Heading 2, {h3_count} Heading 3.")
    doc.save(doc_path)
    print(f"Saved initial fixes to {doc_path}")

if __name__ == "__main__":
    process_document()
