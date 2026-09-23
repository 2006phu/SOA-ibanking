import os
from PIL import Image, ImageDraw, ImageFont

def draw_erd():
    W, H = 1000, 850
    img = Image.new("RGBA", (W, H), "#111111")
    draw = ImageDraw.Draw(img)

    # 1. Grid background
    grid_size = 20
    for x in range(0, W, grid_size):
        draw.line([(x, 0), (x, H)], fill="#181818", width=1)
    for y in range(0, H, grid_size):
        draw.line([(0, y), (W, y)], fill="#181818", width=1)

    # Load font
    try:
        font_header = ImageFont.truetype("arialbd.ttf", 15)
        font_field = ImageFont.truetype("arial.ttf", 13)
        font_pk = ImageFont.truetype("arialbd.ttf", 13)
    except Exception:
        font_header = ImageFont.load_default()
        font_field = ImageFont.load_default()
        font_pk = ImageFont.load_default()

    def draw_entity(x, y, w, header_title, fields):
        row_h = 30
        h = 36 + len(fields) * row_h
        # Khung viền ngoài
        draw.rectangle([x, y, x + w, y + h], fill="#0a0a0a", outline="#ffffff", width=1)
        
        # Header nhỏ hình icon bảng
        draw.rectangle([x + 10, y + 11, x + 20, y + 21], outline="#aaaaaa", width=1)
        draw.line([(x + 10, y + 15), (x + 20, y + 15)], fill="#aaaaaa", width=1)
        
        # Tiêu đề Header
        bbox_h = font_header.getbbox(header_title)
        tw_h, th_h = bbox_h[2] - bbox_h[0], bbox_h[3] - bbox_h[1]
        draw.text((x + (w - tw_h) // 2, y + (36 - th_h) // 2 - 2), header_title, fill="#ffffff", font=font_header)
        
        # Đường kẻ ngang ngăn Header
        draw.line([(x, y + 36), (x + w, y + 36)], fill="#ffffff", width=1)

        # Các dòng field
        field_y_centers = []
        for i, (field_name, is_pk) in enumerate(fields):
            curr_y = y + 36 + i * row_h
            if i > 0:
                draw.line([(x, curr_y), (x + w, curr_y)], fill="#333333", width=1)
            
            f_font = font_pk if is_pk else font_field
            bbox_f = f_font.getbbox(field_name)
            tw_f, th_f = bbox_f[2] - bbox_f[0], bbox_f[3] - bbox_f[1]
            text_x = x + (w - tw_f) // 2
            text_y = curr_y + (row_h - th_f) // 2 - 2
            draw.text((text_x, text_y), field_name, fill="#ffffff", font=f_font)
            
            # Gạch chân nếu là PK
            if is_pk:
                underline_y = curr_y + row_h - 6
                draw.line([(text_x, underline_y), (text_x + tw_f, underline_y)], fill="#ffffff", width=1)
            
            field_y_centers.append(curr_y + row_h // 2)

        return {"x": x, "y": y, "w": w, "h": h, "rows": field_y_centers}

    # Định nghĩa các thực thể và vị trí
    # 1. User
    user_fields = [
        ("user_id", True),
        ("username", False),
        ("password", False),
        ("full_name", False),
        ("phone", False),
        ("email", False),
        ("balance", False)
    ]
    u = draw_entity(60, 220, 180, "User", user_fields)

    # 2. Transaction
    tx_fields = [
        ("transaction_id", True),
        ("user_id", False),
        ("fee_id", False),
        ("mssv", False),
        ("amount", False),
        ("transaction_date", False),
        ("status", False)
    ]
    tx = draw_entity(370, 310, 190, "Transaction", tx_fields)

    # 3. OTP
    otp_fields = [
        ("otp_id", True),
        ("transaction_id", False),
        ("code", False),
        ("expires_time", False),
        ("is_used", False)
    ]
    otp = draw_entity(700, 60, 190, "OTP", otp_fields)

    # 4. Student
    student_fields = [
        ("mssv", True),
        ("student_name", False),
        ("program", False)
    ]
    stu = draw_entity(700, 310, 190, "Student", student_fields)

    # 5. TuitionFee
    fee_fields = [
        ("fee_id", True),
        ("mssv", False),
        ("semester", False),
        ("amount", False),
        ("status", False)
    ]
    fee = draw_entity(700, 520, 190, "TuitionFee", fee_fields)

    # Hàm vẽ ký hiệu Crow's foot (chân quạ - Many) và Crossbar (One)
    def draw_crow_foot_at_left_edge(x, y):
        # Mở rộng về bên phải (chạm vào mép trái của entity)
        draw.line([(x + 10, y - 6), (x, y)], fill="#ffffff", width=1)
        draw.line([(x + 10, y + 6), (x, y)], fill="#ffffff", width=1)
        draw.line([(x + 10, y), (x, y)], fill="#ffffff", width=1)

    def draw_crow_foot_at_right_edge(x, y):
        # Mở rộng về bên trái (chạm vào mép phải của entity)
        draw.line([(x - 10, y - 6), (x, y)], fill="#ffffff", width=1)
        draw.line([(x - 10, y + 6), (x, y)], fill="#ffffff", width=1)
        draw.line([(x - 10, y), (x, y)], fill="#ffffff", width=1)

    def draw_crossbar_v(x, y):
        # Vạch đứng biểu thị "1" (One)
        draw.line([(x, y - 6), (x, y + 6)], fill="#ffffff", width=1)

    # ========================================================
    # VẼ CÁC ĐƯỜNG LIÊN KẾT (RELATIONSHIPS)
    # ========================================================

    # 1. User (1) ----< Transaction (N)
    u_pt = (u["x"] + u["w"], u["rows"][0]) # user_id
    tx_pt_user = (tx["x"], tx["rows"][1])  # user_id
    mid_x1 = 300
    draw.line([u_pt, (mid_x1, u_pt[1]), (mid_x1, tx_pt_user[1]), tx_pt_user], fill="#ffffff", width=1)
    draw_crossbar_v(u_pt[0] + 8, u_pt[1])
    draw_crow_foot_at_left_edge(tx_pt_user[0], tx_pt_user[1])

    # 2. Transaction (1) ---- (1) OTP
    tx_pt_otp = (tx["x"] + tx["w"], tx["rows"][0]) # transaction_id
    otp_pt = (otp["x"], otp["rows"][1])            # transaction_id
    mid_x2 = 600  # Riêng biệt, không trùng mid_x3
    draw.line([tx_pt_otp, (mid_x2, tx_pt_otp[1]), (mid_x2, otp_pt[1]), otp_pt], fill="#ffffff", width=1)
    draw_crossbar_v(tx_pt_otp[0] + 8, tx_pt_otp[1])
    draw_crossbar_v(otp_pt[0] - 8, otp_pt[1])

    # 3. Student (1) ----< TuitionFee (N)
    stu_pt = (stu["x"] + stu["w"], stu["rows"][0]) # mssv
    fee_pt_stu = (fee["x"] + fee["w"], fee["rows"][1]) # mssv
    out_x = 930
    draw.line([stu_pt, (out_x, stu_pt[1]), (out_x, fee_pt_stu[1]), fee_pt_stu], fill="#ffffff", width=1)
    draw_crossbar_v(stu_pt[0] + 8, stu_pt[1])
    draw_crow_foot_at_right_edge(fee_pt_stu[0], fee_pt_stu[1])

    # 4. TuitionFee (1) ----< Transaction (N) [LIÊN KẾT CHUẨN XÁC VỚI FEE_ID]
    tx_pt_fee = (tx["x"] + tx["w"], tx["rows"][2]) # fee_id
    fee_pt = (fee["x"], fee["rows"][0])           # fee_id
    mid_x3 = 650  # Cách xa mid_x2 (600) để không dính nhau
    draw.line([tx_pt_fee, (mid_x3, tx_pt_fee[1]), (mid_x3, fee_pt[1]), fee_pt], fill="#ffffff", width=1)
    draw_crow_foot_at_right_edge(tx_pt_fee[0], tx_pt_fee[1])
    draw_crossbar_v(fee_pt[0] - 8, fee_pt[1])

    # Lưu ảnh ra so_do_erd.jpg
    out_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "diagrams", "so_do_erd.jpg"
    )
    img_rgb = img.convert("RGB")
    img_rgb.save(out_file, quality=95)

if __name__ == "__main__":
    draw_erd()
