import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import shutil
import os
import re

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

def run_upgrade():
    file_path = "docs/Báo cáo SOA.docx"
    print(f"Loading {file_path}...")
    doc = docx.Document(file_path)

    # 1. Update Lời cảm ơn & Lời cam đoan text & page breaks
    for i, p in enumerate(doc.paragraphs[:75]):
        txt = p.text.strip()
        if txt == "LỜI CẢM ƠN":
            p.paragraph_format.page_break_before = True
        elif "CÔNG TRÌNH ĐƯỢC HOÀN THÀNH" in txt:
            p.paragraph_format.page_break_before = True
        elif txt == "MỤC LỤC":
            p.paragraph_format.page_break_before = True

        if "ngày 23 tháng 10 năm 2026" in p.text:
            p.text = "     TP. Hồ Chí Minh, ngày 24 tháng 10 năm 2026"
            for r in p.runs:
                set_run_font(r, size_pt=13)

        if "Tôi xin cam đoan đây là công trình nghiên cứu của riêng tôi" in p.text:
            p.text = (
                "Chúng tôi xin cam đoan đây là công trình nghiên cứu của nhóm và được sự hướng dẫn khoa học "
                "của thầy Dương Hữu Phúc. Các nội dung nghiên cứu, kết quả trong đề tài này là trung thực và "
                "chưa từng công bố dưới bất kỳ hình thức nào trước đây. Những số liệu trong các bảng biểu phục vụ "
                "cho việc phân tích, nhận xét, đánh giá được các tác giả thu thập từ các nguồn khác nhau có ghi rõ "
                "trong phần tài liệu tham khảo."
            )
            for r in p.runs:
                set_run_font(r, size_pt=13)

        if "Nếu phát hiện có bất kỳ sự gian lận nào tôi xin hoàn toàn chịu trách nhiệm" in p.text:
            p.text = (
                "Nếu phát hiện có bất kỳ sự gian lận nào chúng tôi xin hoàn toàn chịu trách nhiệm về nội dung Đề tài "
                "của mình. Trường Đại học Tôn Đức Thắng không liên quan đến những vi phạm tác quyền, bản quyền do "
                "chúng tôi gây ra trong quá trình thực hiện (nếu có)."
            )
            for r in p.runs:
                set_run_font(r, size_pt=13)

        if "ngày 10 tháng 10 năm 2026" in p.text:
            p.text = "TP. Hồ Chí Minh, ngày 24 tháng 10 năm 2026"
            for r in p.runs:
                set_run_font(r, size_pt=13)

    # 2. Synchronize TOC entries with actual page numbers (compact 1.15 line spacing to fit 1 page)
    exact_toc = [
        "CHƯƠNG 1. MỞ ĐẦU VÀ TỔNG QUAN ĐỀ TÀI\t1",
        "1.1 Lý do chọn đề tài\t1",
        "1.2 Mục tiêu thực hiện đề tài\t1",
        "1.3 Scope of Project\t1",
        "CHƯƠNG 2. CƠ SỞ LÝ THUYẾT\t2",
        "2.1 Microservices Architecture & API Gateway\t2",
        "2.2 Distributed Transaction\t2",
        "2.3 Concurrency Control\t2",
        "2.4 Asynchronous Communication\t2",
        "CHƯƠNG 3. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG\t4",
        "3.1 Use Case Diagram\t4",
        "3.2 Architecture Diagram\t4",
        "3.3 ERD Diagram\t5",
        "3.4 Workflow Diagram\t6",
        "3.5 Sequence Diagram\t7",
        "CHƯƠNG 4. CÀI ĐẶT VÀ TRIỂN KHAI\t9",
        "4.1 Technologies Used\t9",
        "4.2 Data Consistency & Concurrency Control\t9",
        "CHƯƠNG 5. KẾT QUẢ\t10",
        "5.1 User Interface\t10",
        "5.2 Concurrency Testing\t13",
        "5.3 Saga Rollback & Compensation\t14",
        "5.4 Technical Deliverables Evaluation\t15",
        "CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN\t17",
        "6.1 Kết luận\t17",
        "6.2 Hướng phát triển\t17",
        "TÀI LIỆU THAM KHẢO\t18",
    ]
    toc_paras = [p for p in doc.paragraphs if p.style.name in ['toc 1', 'toc 2', 'toc 3']]
    if len(toc_paras) == len(exact_toc):
        for p, txt in zip(toc_paras, exact_toc):
            p.text = txt
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.15
            for r in p.runs:
                set_run_font(r, size_pt=11.5)
        print("Synchronized TOC entries with actual page numbers.")

    # 3. Clean all Headings (strip manual prefixes to prevent duplicate numbering)
    for i, p in enumerate(doc.paragraphs):
        if i < 75:
            continue
        style = p.style.name
        txt = p.text.strip()
        if style == "Heading 1":
            p.paragraph_format.page_break_before = True
            if "TÀI LIỆU THAM KHẢO" in txt:
                clean_paragraph_heading(p, "TÀI LIỆU THAM KHẢO", font_size=16)
                disable_numbering(p)
            else:
                clean_txt = re.sub(r'^CHƯƠNG\s+\d+\.\s*', '', txt, flags=re.IGNORECASE)
                clean_paragraph_heading(p, clean_txt, font_size=16)
        elif style == "Heading 2":
            clean_txt = re.sub(r'^\d+\.\d+\s*', '', txt)
            clean_paragraph_heading(p, clean_txt, font_size=14)
        elif style == "Heading 3":
            clean_txt = re.sub(r'^\d+\.\d+\.\d+\s*', '', txt)
            clean_paragraph_heading(p, clean_txt, font_size=13)

    # 4. Check & enforce sections configuration
    # Sec 0: Cover (no page num)
    # Sec 1: Title & Lời cảm ơn (lowerRoman)
    # Sec 2: Lời cam đoan & Mục lục (lowerRoman)
    # Sec 3: Chapter 1 to References (Arabic numerals starting at 1)
    if len(doc.sections) >= 3:
        sec2_pr = doc.sections[2]._sectPr
        pg2 = sec2_pr.xpath('.//w:pgNumType')
        if pg2:
            if qn('w:start') in pg2[0].attrib:
                del pg2[0].attrib[qn('w:start')]
            pg2[0].set(qn('w:fmt'), 'lowerRoman')

    if len(doc.sections) >= 4:
        sec3_pr = doc.sections[3]._sectPr
        pg3 = sec3_pr.xpath('.//w:pgNumType')
        if pg3:
            pg3[0].set(qn('w:start'), '1')
            if qn('w:fmt') in pg3[0].attrib:
                del pg3[0].attrib[qn('w:fmt')]

    doc.save(file_path)
    print(f"✓ SUCCESSFULLY SAVED COMPLETE REPORT TO {file_path}")

if __name__ == "__main__":
    run_upgrade()
