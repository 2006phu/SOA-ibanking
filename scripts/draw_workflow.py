import os
from PIL import Image, ImageDraw, ImageFont

def draw_workflow():
    # Kích thước ảnh
    width = 1200
    height = 1600
    bg_color = (250, 250, 250)
    box_color = (255, 255, 255)
    text_color = (20, 20, 20)
    accent_color = (0, 150, 136)
    arrow_color = (100, 100, 100)
    
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Cố gắng load font, nếu không có thì dùng default
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 40)
        font_main = ImageFont.truetype("arialbd.ttf", 24)
        font_sub = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_title = ImageFont.load_default()
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Vẽ tiêu đề
    title = "PAYMENT OPERATION WORKFLOW"
    draw.text((width//2 - 250, 40), title, font=font_title, fill=accent_color)
    
    # Định nghĩa các bước
    steps = [
        {"actor": "FRONTEND", "action": "Khởi tạo thanh toán học phí", "desc": "Gửi MSSV và Mã Học Phí"},
        {"actor": "API GATEWAY", "action": "Xác thực & Forward Request", "desc": "Check JWT & X-Correlation-ID"},
        {"actor": "PAYMENT SERVICE", "action": "Validate Điều kiện", "desc": "Check User Balance >= Amount\nCheck Tuition == UNPAID"},
        {"actor": "OTP SERVICE", "action": "Tạo mã OTP", "desc": "Lưu DB & Publish event 'otp_email'"},
        {"actor": "NOTIFICATION SERVICE", "action": "Gửi Email OTP", "desc": "Gửi mã qua SMTP đến sinh viên"},
        {"actor": "FRONTEND", "action": "Nhập & Gửi OTP", "desc": "User nhập mã OTP gồm 6 chữ số"},
        {"actor": "OTP SERVICE", "action": "Xác thực OTP", "desc": "Check hợp lệ & thời hạn (5 phút)"},
        {"actor": "USER SERVICE", "action": "Trừ tiền (Execution 1)", "desc": "SELECT ... FOR UPDATE\nTrừ số dư tài khoản"},
        {"actor": "TUITION SERVICE", "action": "Cập nhật học phí (Execution 2)", "desc": "SELECT ... FOR UPDATE\nĐổi trạng thái thành PAID"},
        {"actor": "PAYMENT SERVICE", "action": "Hoàn tất Giao dịch", "desc": "Lưu lịch sử & Publish event 'payment_success'"},
        {"actor": "NOTIFICATION SERVICE", "action": "Gửi Email Biên lai", "desc": "Gửi hóa đơn điện tử cho user"}
    ]

    box_w = 400
    box_h = 100
    start_y = 150
    spacing = 130
    
    center_x = width // 2
    
    def draw_arrow(x, y1, y2):
        # Vẽ line
        draw.line([(x, y1), (x, y2)], fill=arrow_color, width=4)
        # Vẽ đầu mũi tên
        draw.polygon([
            (x - 8, y2 - 12),
            (x + 8, y2 - 12),
            (x, y2)
        ], fill=arrow_color)

    for i, step in enumerate(steps):
        # Tính toán toạ độ
        x1 = center_x - box_w // 2
        y1 = start_y + i * spacing
        x2 = center_x + box_w // 2
        y2 = y1 + box_h
        
        # Vẽ Box
        draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=box_color, outline=accent_color, width=2)
        
        # Vẽ chữ
        draw.text((x1 + 20, y1 + 10), step["actor"], font=font_sub, fill=(60, 60, 60))
        draw.text((x1 + 20, y1 + 35), step["action"], font=font_main, fill=text_color)
        draw.text((x1 + 20, y1 + 65), step["desc"], font=font_sub, fill=(100, 100, 100))
        
        # Mũi tên nối với bước tiếp theo
        if i < len(steps) - 1:
            draw_arrow(center_x, y2, y2 + spacing - box_h)
            
    # Vẽ Legend / Chú thích
    draw.rounded_rectangle([50, 50, 350, 150], radius=10, fill=(240, 240, 240), outline=(180, 180, 180), width=1)
    draw.text((70, 70), "Chú thích (Legend):", font=font_main, fill=text_color)
    draw.text((70, 110), "Các bước xử lý tuần tự của hệ thống", font=font_sub, fill=(180, 180, 180))

    # Lưu ảnh
    os.makedirs('docs/diagrams', exist_ok=True)
    img.save('docs/diagrams/so_do_workflow.jpg', quality=95)
    print("Đã tạo thành công docs/diagrams/so_do_workflow.jpg")

if __name__ == "__main__":
    draw_workflow()
