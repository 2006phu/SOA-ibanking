import os
from PIL import Image, ImageDraw, ImageFont

def draw_sequence_diagram():
    W, H = 1240, 1260
    img = Image.new("RGBA", (W, H), "#111111")
    draw = ImageDraw.Draw(img)

    # 1. Grid background
    grid_size = 20
    for x in range(0, W, grid_size):
        draw.line([(x, 0), (x, H)], fill="#181818", width=1)
    for y in range(0, H, grid_size):
        draw.line([(0, y), (W, y)], fill="#181818", width=1)

    # Load fonts
    try:
        font_part = ImageFont.truetype("arialbd.ttf", 13)
        font_msg = ImageFont.truetype("arial.ttf", 12)
        font_msg_bold = ImageFont.truetype("arialbd.ttf", 12)
        font_note = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font_part = ImageFont.load_default()
        font_msg = ImageFont.load_default()
        font_msg_bold = ImageFont.load_default()
        font_note = ImageFont.load_default()

    # Danh sách 8 thành phần tham gia (Participants)
    participants = [
        {"name": "Client (React)", "x": 80},
        {"name": "API Gateway", "x": 230},
        {"name": "Payment Service", "x": 400},
        {"name": "User Service", "x": 570},
        {"name": "Tuition Service", "x": 730},
        {"name": "OTP Service", "x": 880},
        {"name": "RabbitMQ", "x": 1010},
        {"name": "Notification", "x": 1140},
    ]

    part_w, part_h = 120, 38
    top_y = 35
    bottom_y = H - 55

    # Vẽ Participants ở trên và dưới, cùng đường lifeline
    for p in participants:
        px = p["x"]
        # Lifeline (đường đứt nét)
        for ly in range(top_y + part_h, bottom_y, 10):
            draw.line([(px, ly), (px, min(ly + 5, bottom_y))], fill="#444444", width=1)

        # Hộp ở trên
        draw.rounded_rectangle([px - part_w // 2, top_y, px + part_w // 2, top_y + part_h], radius=6, fill="#0a0a0a", outline="#ffffff", width=1)
        bbox = font_part.getbbox(p["name"])
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((px - tw // 2, top_y + (part_h - th) // 2 - 2), p["name"], fill="#ffffff", font=font_part)

        # Hộp ở dưới
        draw.rounded_rectangle([px - part_w // 2, bottom_y, px + part_w // 2, bottom_y + part_h], radius=6, fill="#0a0a0a", outline="#ffffff", width=1)
        draw.text((px - tw // 2, bottom_y + (part_h - th) // 2 - 2), p["name"], fill="#ffffff", font=font_part)

    # Hàm vẽ mũi tên đồng bộ (Sync Request: nét liền có đầu mũi tên)
    def draw_msg(x1, x2, y, label, is_response=False, is_bold=False):
        f = font_msg_bold if is_bold else font_msg
        color = "#ffffff" if not is_response else "#aaaaaa"
        
        if is_response:
            step = 6
            start_x, end_x = min(x1, x2), max(x1, x2)
            for sx in range(start_x, end_x, step * 2):
                draw.line([(sx, y), (min(sx + step, end_x), y)], fill=color, width=1)
        else:
            draw.line([(x1, y), (x2, y)], fill=color, width=1)

        arrow_size = 5
        if x2 > x1:
            draw.polygon([(x2, y), (x2 - arrow_size * 1.5, y - arrow_size), (x2 - arrow_size * 1.5, y + arrow_size)], fill=color)
        else:
            draw.polygon([(x2, y), (x2 + arrow_size * 1.5, y - arrow_size), (x2 + arrow_size * 1.5, y + arrow_size)], fill=color)

        bbox = f.getbbox(label)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        text_x = min(x1, x2) + abs(x2 - x1) // 2 - tw // 2
        draw.text((text_x, y - th - 5), label, fill=color, font=f)

    # ==========================
    # CÁC BƯỚC TUẦN TỰ (STEPS)
    # ==========================
    p_map = {p["name"]: p["x"] for p in participants}
    c_x = p_map["Client (React)"]
    gw_x = p_map["API Gateway"]
    pay_x = p_map["Payment Service"]
    u_x = p_map["User Service"]
    t_x = p_map["Tuition Service"]
    otp_x = p_map["OTP Service"]
    mq_x = p_map["RabbitMQ"]
    notif_x = p_map["Notification"]

    # GIAI ĐOẠN 1: KHỞI TẠO THANH TOÁN (INITIATE)
    y = 115
    draw_msg(c_x, gw_x, y, "1. POST /payments/initiate (MSSV, fee_id)")
    y += 42
    draw_msg(gw_x, pay_x, y, "Forward + X-Correlation-ID")
    y += 42
    draw_msg(pay_x, t_x, y, "2. GET /tuition/fee/{id} (Check UNPAID)")
    y += 36
    draw_msg(t_x, pay_x, y, "Return Fee Info", is_response=True)
    y += 42
    draw_msg(pay_x, u_x, y, "3. GET /users/{id}/balance")
    y += 36
    draw_msg(u_x, pay_x, y, "Return Balance", is_response=True)
    y += 42
    draw_msg(pay_x, c_x, y, "4. 201 Created (Transaction PENDING)", is_response=True)

    # GIAI ĐOẠN 2: XÁC NHẬN & TẠO OTP (CONFIRM)
    y += 55
    draw_msg(c_x, gw_x, y, "5. POST /payments/{id}/confirm")
    y += 42
    draw_msg(gw_x, pay_x, y, "Forward Confirm")
    y += 42
    draw_msg(pay_x, otp_x, y, "6. POST /otp/generate (tx_id, email)")
    y += 42
    draw_msg(otp_x, mq_x, y, "7. Publish event 'otp_email'")
    y += 42
    draw_msg(mq_x, notif_x, y, "8. Consume event & Send Email via SMTP")
    y += 42
    draw_msg(otp_x, pay_x, y, "OTP generated", is_response=True)
    y += 36
    draw_msg(pay_x, c_x, y, "9. 200 OK (Status: OTP_SENT)", is_response=True)

    # GIAI ĐOẠN 3: XÁC THỰC OTP
    y += 55
    draw_msg(c_x, gw_x, y, "10. POST /payments/{id}/verify-otp {otp_code}")
    y += 42
    draw_msg(gw_x, pay_x, y, "Forward Verify")
    y += 42
    draw_msg(pay_x, otp_x, y, "11. POST /otp/verify")
    y += 36
    draw_msg(otp_x, pay_x, y, "Valid = True", is_response=True)

    # GIAI ĐOẠN 4: CRITICAL SECTION - SAGA TRANSACTION & LOCKING
    y += 50
    box_top = y - 12
    box_h = 180
    box_left = pay_x - 60
    box_right = t_x + 50
    draw.rounded_rectangle([box_left, box_top, box_right, box_top + box_h], radius=8, fill="#191919", outline="#00ffcc", width=1)
    draw.text((box_left + 15, box_top + 8), "CRITICAL SECTION: SAGA ORCHESTRATION & PESSIMISTIC LOCK", fill="#00ffcc", font=font_note)

    y += 38
    draw_msg(pay_x, u_x, y, "12. PUT /balance/deduct (SELECT FOR UPDATE)", is_bold=True)
    y += 36
    draw_msg(u_x, pay_x, y, "Deducted Success", is_response=True)
    y += 42
    draw_msg(pay_x, t_x, y, "13. PUT /tuition/pay (SELECT FOR UPDATE)", is_bold=True)
    y += 36
    draw_msg(t_x, pay_x, y, "Marked PAID Success", is_response=True)

    # GIAI ĐOẠN 5: THÀNH CÔNG & GỬI BIÊN LAI
    y += 65
    draw_msg(pay_x, mq_x, y, "14. Publish event 'payment_success'")
    y += 42
    draw_msg(mq_x, notif_x, y, "15. Consume & Send Receipt Email")
    y += 45
    draw_msg(pay_x, c_x, y, "16. 200 SUCCESS (Thanh toán hoàn tất)", is_response=True, is_bold=True)

    out_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "diagrams", "so_do_sequence.jpg"
    )
    img_rgb = img.convert("RGB")
    img_rgb.save(out_file, quality=95)

if __name__ == "__main__":
    draw_sequence_diagram()
