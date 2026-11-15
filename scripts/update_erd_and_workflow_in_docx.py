import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import sys

sys.stdout.reconfigure(encoding='utf-8')

DOCX_PATH = 'docs/Báo cáo SOA.docx'
doc = docx.Document(DOCX_PATH)

def format_run(run, font_name='Times New Roman', size_pt=13, bold=False, italic=False):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic

# Find 3.3 ERD Diagram and 3.4 Workflow Diagram
erd_heading_idx = None
wf_heading_idx = None

for i, p in enumerate(doc.paragraphs):
    if p.style.name == 'Heading 2' and p.text.strip() == 'ERD Diagram':
        erd_heading_idx = i
    elif p.style.name == 'Heading 2' and p.text.strip() == 'Workflow Diagram':
        wf_heading_idx = i

print(f'Found ERD Heading at {erd_heading_idx}, Workflow Heading at {wf_heading_idx}')

# 1. Update ERD description paragraph (erd_heading_idx + 1)
p_erd_desc = doc.paragraphs[erd_heading_idx + 1]
p_erd_desc.text = ''
r_desc = p_erd_desc.add_run(
    'Thiết kế dữ liệu của hệ thống được thể hiện qua hai góc nhìn: Sơ đồ thực thể nghiệp vụ tổng thể (Hình 3.3a) '
    'và Sơ đồ phân rã cơ sở dữ liệu vật lý chuẩn SOA Database-per-Service (Hình 3.3b). '
    'Hệ thống vận hành trên 5 cơ sở dữ liệu PostgreSQL độc lập: auth_db (bảng users), user_db (bảng user_profiles, transaction_histories), '
    'tuition_db (bảng students, tuition_fees), payment_db (bảng transactions) và otp_db (bảng otp_codes). '
    'Chỉ các bảng nằm trong cùng một phân hệ mới thiết lập khóa ngoại vật lý (Internal Foreign Key), '
    'trong khi liên kết giữa các phân hệ sử dụng định danh tham chiếu logic (Logical Reference) đồng bộ qua REST API và Saga Orchestrator.'
)
format_run(r_desc, 'Times New Roman', 13, False, False)
p_erd_desc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p_erd_desc.paragraph_format.line_spacing = 1.15
p_erd_desc.paragraph_format.space_after = Pt(6)

# 2. Update Figure 3.3a caption (erd_heading_idx + 3)
p_cap_33a = doc.paragraphs[erd_heading_idx + 3]
p_cap_33a.text = ''
r_cap_33a = p_cap_33a.add_run('Hình 3.3a: Sơ đồ Quan hệ Thực thể Nghiệp vụ (Conceptual Domain ERD)')
format_run(r_cap_33a, 'Times New Roman', 12, False, True)
p_cap_33a.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_cap_33a.paragraph_format.space_after = Pt(8)

# 3. Insert Figure 3.3b (SOA Distributed ERD) and its caption right before Workflow Diagram heading
p_wf_heading = doc.paragraphs[wf_heading_idx]

# Check if Hình 3.3b caption is already inserted
already_has_33b = any(p.text.strip().startswith('Hình 3.3b:') for p in doc.paragraphs)
if not already_has_33b:
    p_img_33b = p_wf_heading.insert_paragraph_before('')
    p_img_33b.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img_33b.paragraph_format.space_before = Pt(4)
    p_img_33b.paragraph_format.space_after = Pt(3)
    run_img_33b = p_img_33b.add_run()
    run_img_33b.add_picture('docs/images/so_do_erd_soa.jpg', width=Inches(5.8))

    p_cap_33b = p_wf_heading.insert_paragraph_before('')
    p_cap_33b.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_33b.paragraph_format.space_after = Pt(10)
    r_cap_33b = p_cap_33b.add_run('Hình 3.3b: Sơ đồ Cơ sở dữ liệu Phân tán Chuẩn SOA (Database-per-Service Physical ERD)')
    format_run(r_cap_33b, 'Times New Roman', 12, False, True)
    print('Inserted Hình 3.3b (SOA Distributed ERD) before Workflow Diagram.')

# 4. Update Figure 3.4 (Workflow Diagram) with the new Archify Workflow Diagram
# Re-locate Workflow Diagram heading index after insertion
for i, p in enumerate(doc.paragraphs):
    if p.style.name == 'Heading 2' and p.text.strip() == 'Workflow Diagram':
        wf_heading_idx = i
        break

p_wf_img = doc.paragraphs[wf_heading_idx + 2]
p_wf_img.text = ''  # clears old inline picture run
p_wf_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_wf_img.paragraph_format.space_before = Pt(4)
p_wf_img.paragraph_format.space_after = Pt(3)
run_wf_img = p_wf_img.add_run()
run_wf_img.add_picture('docs/images/so_do_workflow_new.jpg', width=Inches(5.8))
print('Updated Hình 3.4 with Archify Workflow Diagram.')

doc.save(DOCX_PATH)
print('Saved updated DOCX successfully.')
