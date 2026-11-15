import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import shutil
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def update_chapter_5():
    file_path = "docs/Báo cáo SOA.docx"
    backup_path = "docs/Báo cáo SOA_backup.docx"

    # Backup original
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")

    doc = docx.Document(file_path)

    # Locate Chapter 5 heading and Chapter 6 heading
    ch5_p = None
    ch6_p = None
    for i, p in enumerate(doc.paragraphs):
        if i > 100 and "KẾT QUẢ" in p.text and p.style.name == "Heading 1":
            ch5_p = p
        if i > 100 and "KẾT LUẬN" in p.text and p.style.name == "Heading 1":
            ch6_p = p
            break

    if ch5_p is None or ch6_p is None:
        print("Could not locate chapter bounds.")
        return

    # Remove all XML elements (paragraphs, tables) between ch5_p and ch6_p
    parent = ch5_p._p.getparent()
    elements_to_remove = []
    collecting = False
    for child in parent:
        if child == ch5_p._p:
            collecting = True
            continue
        if child == ch6_p._p:
            collecting = False
            break
        if collecting:
            elements_to_remove.append(child)

    for el in elements_to_remove:
        parent.remove(el)

    print(f"Removed {len(elements_to_remove)} old elements from Chapter 5.")

    current_p = ch5_p

    def add_para_after(ref_p, text, style_name="Normal", bold=False, italic=False, font_size=13, space_after=6, align=None):
        new_p = doc.add_paragraph(style=style_name)
        ref_p._p.addnext(new_p._p)
        run = new_p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        new_p.paragraph_format.space_after = Pt(space_after)
        new_p.paragraph_format.line_spacing = 1.3
        if align:
            new_p.alignment = align
        return new_p

    def add_table_after(ref_p, headers, rows, col_widths=None):
        table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        ref_p._p.addnext(table._tbl)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Clean academic borders (thin single black borders, no color fill)
        tblPr = table._tbl.tblPr
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>
            </w:tblBorders>
        ''')
        tblPr.append(borders)

        # Style table headers - NO COLOR (trắng/không màu, chữ đen in đậm)
        hdr_cells = table.rows[0].cells
        for col_idx, title in enumerate(headers):
            hdr_cells[col_idx].text = title
            set_cell_margins(hdr_cells[col_idx], 120, 120, 150, 150)
            p = hdr_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)

        # Style data rows - NO COLOR (trắng/không màu, chữ đen)
        for row_idx, row_data in enumerate(rows):
            row_cells = table.rows[row_idx + 1].cells
            for col_idx, cell_value in enumerate(row_data):
                row_cells[col_idx].text = str(cell_value)
                set_cell_margins(row_cells[col_idx], 100, 100, 150, 150)
                p = row_cells[col_idx].paragraphs[0]
                if col_idx in (0, len(row_data) - 1):
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(11)
                    r.font.color.rgb = RGBColor(0, 0, 0)

        # Create an empty paragraph after the table for spacing and as next insertion anchor
        dummy_p = doc.add_paragraph(style="Normal")
        table._tbl.addnext(dummy_p._p)
        dummy_p.paragraph_format.space_after = Pt(6)
        return dummy_p

    # Build Chapter 5 Content sequentially:
    # -------------------------------------------------------------
    p = current_p

    intro_text = (
        "Hệ thống iBanking TDTU đã được triển khai hoàn chỉnh và kiểm thử thực tế. "
        "Nội dung chương này tổng hợp kết quả hoạt động của giao diện ứng dụng, dữ liệu kiểm thử tải tương tranh, "
        "cơ chế bù trừ giao dịch phân tán Saga, cùng bảng đối soát các yêu cầu kỹ thuật của đề tài."
    )
    p = add_para_after(p, intro_text, style_name="Normal", font_size=13, space_after=8)

    # 5.1 Giao diện người dùng
    p = add_para_after(p, "5.1 Giao diện người dùng", style_name="Heading 2", bold=True, font_size=14, space_after=6)
    
    ui_intro = (
        "Ứng dụng web được xây dựng bằng React.js, tổ chức theo các chức năng chính của hệ thống ngân hàng trực tuyến:"
    )
    p = add_para_after(p, ui_intro, font_size=13, space_after=6)

    # 5.1.1 Login
    p = add_para_after(p, "5.1.1 Màn hình Đăng nhập", style_name="Heading 3", bold=True, font_size=13, space_after=4)
    login_desc = (
        "Màn hình đăng nhập chuyển tiếp thông tin xác thực qua API Gateway để nhận JWT token. "
        "Giao diện tích hợp các nút chọn nhanh tài khoản thử nghiệm (sinh viên, phụ huynh) "
        "nhằm hỗ trợ kiểm thử trực tiếp mà không cần nhập dữ liệu thủ công."
    )
    p = add_para_after(p, login_desc, font_size=13, space_after=4)
    p = add_para_after(p, "[Hình 5.1: Màn hình đăng nhập hệ thống iBanking TDTU]", bold=True, italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # 5.1.2 Dashboard
    p = add_para_after(p, "5.1.2 Bảng điều khiển tài khoản (Dashboard)", style_name="Heading 3", bold=True, font_size=13, space_after=4)
    dash_desc = (
        "Màn hình Dashboard hiển thị thông tin thẻ tài khoản, số dư khả dụng, "
        "trạng thái đồng bộ dữ liệu từ User Service và lối tắt dẫn trực tiếp đến chức năng nộp học phí."
    )
    p = add_para_after(p, dash_desc, font_size=13, space_after=4)
    p = add_para_after(p, "[Hình 5.2: Bảng điều khiển tài khoản và số dư người dùng]", bold=True, italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # 5.1.3 Tuition Payment Wizard
    p = add_para_after(p, "5.1.3 Quy trình nộp học phí", style_name="Heading 3", bold=True, font_size=13, space_after=4)
    pay_desc = (
        "Chức năng nộp học phí được chia thành 4 bước tuần tự:\n"
        "- Bước 1 (Tra cứu): Nhập mã số sinh viên (MSSV) để truy vấn danh sách các khoản học phí chưa thanh toán từ Tuition Service.\n"
        "- Bước 2 (Xác nhận): Kiểm tra chi tiết khoản phí cần nộp và đối chiếu với số dư tài khoản của người dùng.\n"
        "- Bước 3 (Xác thực OTP): Nhập mã OTP 6 chữ số gửi qua email, kèm bộ đếm thời gian hiệu lực 5 phút.\n"
        "- Bước 4 (Biên lai điện tử): Hệ thống thông báo kết quả và hiển thị biên lai sau khi hoàn tất giao dịch."
    )
    p = add_para_after(p, pay_desc, font_size=13, space_after=4)
    p = add_para_after(p, "[Hình 5.3: Màn hình tra cứu và xác nhận thông tin học phí]", bold=True, italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    p = add_para_after(p, "[Hình 5.4: Màn hình xác thực giao dịch bằng mã OTP]", bold=True, italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # 5.1.4 Email OTP
    p = add_para_after(p, "5.1.4 Email thông báo và lịch sử giao dịch", style_name="Heading 3", bold=True, font_size=13, space_after=4)
    email_desc = (
        "Notification Worker nhận thông điệp qua hàng đợi RabbitMQ và sử dụng giao thức SMTP (Gmail) "
        "để chuyển mã OTP cũng như thư xác nhận thanh toán đến địa chỉ email của người dùng. "
        "Sau khi hoàn tất, giao dịch được lưu lại trên màn hình Lịch sử giao dịch."
    )
    p = add_para_after(p, email_desc, font_size=13, space_after=4)
    p = add_para_after(p, "[Hình 5.5: Email chứa mã xác thực OTP gửi qua giao thức SMTP]", bold=True, italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    p = add_para_after(p, "[Hình 5.6: Biên lai thanh toán và màn hình lịch sử giao dịch]", bold=True, italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # 5.2 Concurrency Evidence
    p = add_para_after(p, "5.2 Kết quả kiểm thử xử lý tương tranh", style_name="Heading 2", bold=True, font_size=14, space_after=6)
    conc_desc = (
        "Nhóm sử dụng kịch bản kiểm thử tự động (tệp scripts/test_concurrency_scenarios.py) để kiểm tra "
        "tính toàn vẹn dữ liệu khi có nhiều yêu cầu gửi đến đồng thời. Kết quả thực nghiệm được tổng hợp trong Bảng 5.1."
    )
    p = add_para_after(p, conc_desc, font_size=13, space_after=6)

    # Table of concurrency tests
    conc_headers = ["STT", "Kịch bản kiểm thử", "Số luồng đồng thời", "Kết quả thực tế", "Đánh giá tính toàn vẹn"]
    conc_rows = [
        [
            "1",
            "Một tài khoản gửi hai yêu cầu thanh toán cùng lúc (Double-spending)",
            "2 luồng song song",
            "Giao dịch đầu tiên thành công (200 OK).\nGiao dịch thứ hai bị từ chối do không đủ số dư (400 Bad Request).",
            "Đạt\n(Số dư không bị trừ âm)"
        ],
        [
            "2",
            "Hai tài khoản cùng thanh toán cho một khoản học phí",
            "2 luồng song song",
            "Giao dịch 1 gạch nợ thành công (PAID).\nGiao dịch 2 nhận phản hồi lỗi (409 Conflict: Already paid).",
            "Đạt\n(Học phí chỉ ghi nhận một lần)"
        ],
        [
            "3",
            "Gửi lặp lại yêu cầu tạo giao dịch từ giao diện trong thời gian ngắn",
            "5 yêu cầu liên tiếp",
            "Hệ thống lọc các yêu cầu trùng lặp nhờ Idempotency Key, chỉ khởi tạo duy nhất 1 giao dịch.",
            "Đạt\n(Đảm bảo tính lũy đẳng)"
        ]
    ]
    p = add_table_after(p, conc_headers, conc_rows)
    p = add_para_after(p, "Bảng 5.1: Kết quả kiểm thử tương tranh và tính toàn vẹn dữ liệu", italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    # 5.3 Saga Rollback Evidence
    p = add_para_after(p, "5.3 Cơ chế bù trừ trong giao dịch phân tán (Saga Rollback)", style_name="Heading 2", bold=True, font_size=14, space_after=6)
    saga_desc = (
        "Trong mô hình Database-per-service, khi một bước trong tiến trình thanh toán gặp sự cố, hệ thống thực hiện bù trừ theo quy trình:\n"
        "- Kịch bản kiểm thử: User Service trừ tiền trong tài khoản người dùng thành công, nhưng yêu cầu thanh toán sang Tuition Service bị từ chối vì khoản học phí đã được gạch nợ trước đó (mã lỗi 409 Conflict).\n"
        "- Xử lý bù trừ: Payment Orchestrator ghi nhận mã lỗi 409 và gửi yêu cầu hoàn tiền (operation: refund) đến User Service để hoàn lại số dư tương ứng.\n"
        "- Kết quả: Giao dịch được chuyển sang trạng thái REFUNDED, số dư tài khoản người dùng phục hồi nguyên trạng và hệ thống lưu lại nhật ký đối soát."
    )
    p = add_para_after(p, saga_desc, font_size=13, space_after=8)

    # 5.4 Deliverables Checklist Table
    p = add_para_after(p, "5.4 Đánh giá mức độ hoàn thành yêu cầu đồ án", style_name="Heading 2", bold=True, font_size=14, space_after=6)
    
    deliv_headers = ["STT", "Yêu cầu kỹ thuật đồ án", "Hiện thực trong hệ thống", "Kết quả"]
    deliv_rows = [
        ["1", "Kiến trúc Microservices độc lập", "6 dịch vụ (Auth, User, Tuition, Payment, OTP, Notification) cùng 1 Gateway", "Đạt"],
        ["2", "Database-per-Service", "5 cơ sở dữ liệu PostgreSQL riêng biệt, không sử dụng ràng buộc khóa ngoại chéo giữa các dịch vụ", "Đạt"],
        ["3", "Giao dịch phân tán (Distributed Transaction)", "Điều phối qua Payment Orchestrator kèm cơ chế bù trừ (refund) tự động khi có bước thất bại", "Đạt"],
        ["4", "Kiểm soát tương tranh (Concurrency Control)", "Khóa bi quan (SELECT ... FOR UPDATE) tại tầng cơ sở dữ liệu để ngăn ngừa xung đột", "Đạt"],
        ["5", "Giao tiếp bất đồng bộ qua Message Queue", "Hàng đợi thông điệp RabbitMQ (otp_email, payment_success) và gửi thông báo qua Gmail SMTP", "Đạt"],
        ["6", "Container hóa và triển khai", "Đóng gói toàn bộ dịch vụ bằng Docker Compose kèm kịch bản chạy tự động (start.bat / start.sh)", "Đạt"],
        ["7", "Giao diện người dùng", "Giao diện React.js với quy trình 4 bước, cập nhật số dư và hiển thị biên lai điện tử", "Đạt"]
    ]
    p = add_table_after(p, deliv_headers, deliv_rows)
    p = add_para_after(p, "Bảng 5.2: Bảng đối soát mức độ hoàn thành các tiêu chí kỹ thuật đồ án", italic=True, font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    output_path = file_path
    try:
        doc.save(output_path)
        print(f"Successfully updated Chapter 5 in {output_path}")
    except PermissionError:
        output_path = "docs/Báo cáo SOA_updated.docx"
        doc.save(output_path)
        print(f"Permission denied on original (file is open in Word). Saved updated version to {output_path}")


if __name__ == "__main__":
    update_chapter_5()
