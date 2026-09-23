import os
from PIL import Image, ImageDraw, ImageFont

def create_architecture_diagram():
    # Kích thước ảnh chất lượng cao (2x resolution so với ảnh gốc)
    W, H = 800, 1280
    img = Image.new("RGBA", (W, H), "#111111")
    draw = ImageDraw.Draw(img)

    # 1. Vẽ lưới nền (Grid Pattern)
    grid_size = 20
    for x in range(0, W, grid_size):
        draw.line([(x, 0), (x, H)], fill="#1a1a1a", width=1)
    for y in range(0, H, grid_size):
        draw.line([(0, y), (W, y)], fill="#1a1a1a", width=1)

    # Load font
    try:
        font_layer = ImageFont.truetype("arial.ttf", 15)
        font_node = ImageFont.truetype("arial.ttf", 14)
        font_node_bold = ImageFont.truetype("arialbd.ttf", 14)
    except Exception:
        font_layer = ImageFont.load_default()
        font_node = ImageFont.load_default()
        font_node_bold = ImageFont.load_default()

    def draw_rounded_rect(xy, fill="#181818", outline="#444444", radius=14, width=1):
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

    def draw_node_box(x, y, w, h, text, subtext=None):
        draw_rounded_rect([x, y, x + w, y + h], fill="#0a0a0a", outline="#ffffff", radius=8, width=1)
        if subtext:
            bbox1 = font_node.getbbox(text)
            tw1, th1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
            bbox2 = font_node.getbbox(subtext)
            tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
            total_h = th1 + th2 + 6
            start_y = y + (h - total_h) // 2
            draw.text((x + (w - tw1) // 2, start_y), text, fill="#ffffff", font=font_node)
            draw.text((x + (w - tw2) // 2, start_y + th1 + 6), subtext, fill="#ffffff", font=font_node)
        else:
            bbox = font_node.getbbox(text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((x + (w - tw) // 2, y + (h - th) // 2 - 2), text, fill="#ffffff", font=font_node)

    def draw_cylinder(x, y, w, h, text):
        ry = 10
        # 1. Vẽ nền bên trong cylinder (fill)
        draw.rectangle([x, y + ry, x + w, y + h - ry], fill="#0a0a0a")
        draw.pieslice([x, y + h - 2 * ry, x + w, y + h], start=0, end=180, fill="#0a0a0a")
        draw.ellipse([x, y, x + w, y + 2 * ry], fill="#0a0a0a")

        # 2. Vẽ viền trắng
        draw.line([(x, y + ry), (x, y + h - ry)], fill="#ffffff", width=1)
        draw.line([(x + w, y + ry), (x + w, y + h - ry)], fill="#ffffff", width=1)
        draw.arc([x, y + h - 2 * ry, x + w, y + h], start=0, end=180, fill="#ffffff", width=1)
        draw.ellipse([x, y, x + w, y + 2 * ry], outline="#ffffff", width=1)

        # 3. Vẽ text ở giữa
        bbox = font_node.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x + (w - tw) // 2, y + (h - th) // 2 + 2), text, fill="#ffffff", font=font_node)

    def draw_arrow_down(x, y1, y2):
        draw.line([(x, y1), (x, y2)], fill="#ffffff", width=2)
        arrow_size = 6
        draw.polygon([(x, y2), (x - arrow_size, y2 - arrow_size * 1.5), (x + arrow_size, y2 - arrow_size * 1.5)], fill="#ffffff")

    def draw_arrow_right(x1, x2, y):
        draw.line([(x1, y), (x2, y)], fill="#ffffff", width=1)
        arrow_size = 4
        draw.polygon([(x2, y), (x2 - arrow_size * 1.5, y - arrow_size), (x2 - arrow_size * 1.5, y + arrow_size)], fill="#ffffff")

    # ==========================
    # 1. LAYER 1: Web Application (UI)
    # ==========================
    L1_y, L1_h = 30, 90
    draw_rounded_rect([40, L1_y, 760, L1_y + L1_h], radius=16)
    draw.text((70, L1_y + 36), "Web Application (UI)", fill="#ffffff", font=font_layer)
    draw_node_box(260, L1_y + 20, 260, 50, "Web Application (React /", "Angular / Vue)")

    # Mũi tên L1 -> L2
    draw_arrow_down(400, L1_y + L1_h, L1_y + L1_h + 35)

    # ==========================
    # 2. LAYER 2: Gateway Layer
    # ==========================
    L2_y, L2_h = L1_y + L1_h + 35, 80
    draw_rounded_rect([40, L2_y, 760, L2_y + L2_h], radius=16)
    draw.text((70, L2_y + 30), "Gateway Layer", fill="#ffffff", font=font_layer)
    draw_node_box(260, L2_y + 18, 260, 44, "API Gateway")

    # Mũi tên L2 -> L3
    draw_arrow_down(400, L2_y + L2_h, L2_y + L2_h + 35)

    # ==========================
    # 3. LAYER 3: Core Microservices Layer
    # ==========================
    L3_y, L3_h = L2_y + L2_h + 35, 500
    draw_rounded_rect([40, L3_y, 760, L3_y + L3_h], radius=20)
    draw.text((70, L3_y + 235), "Core Microservices Layer", fill="#ffffff", font=font_layer)

    # Danh sách 6 Microservices:
    services = [
        ("Auth Service", "Auth_DB"),
        ("User Service", "User_DB"),
        ("Tuition Service", "Tuition_DB"),
        ("Payment Service", "Payment_DB"),
        ("OTP Service", "OTP_DB"),
        ("Notification Service", None),
    ]

    svc_x = 260
    svc_w = 230
    svc_h = 44
    db_x = 580
    db_w = 110
    db_h = 56
    gap_y = 74
    start_svc_y = L3_y + 30

    for i, (svc_name, db_name) in enumerate(services):
        curr_y = start_svc_y + i * gap_y
        draw_node_box(svc_x, curr_y, svc_w, svc_h, svc_name)
        if db_name:
            draw_cylinder(db_x, curr_y - 6, db_w, db_h, db_name)
            draw_arrow_right(svc_x + svc_w, db_x, curr_y + svc_h // 2)

    # Mũi tên L3 -> L4
    draw_arrow_down(400, L3_y + L3_h, L3_y + L3_h + 35)

    # ==========================
    # 4. LAYER 4: Infrastructure Layer
    # ==========================
    L4_y, L4_h = L3_y + L3_h + 35, 150
    draw_rounded_rect([40, L4_y, 760, L4_y + L4_h], radius=16)
    draw.text((70, L4_y + 62), "Infrastructure Layer", fill="#ffffff", font=font_layer)

    draw_node_box(260, L4_y + 22, 260, 44, "RabbitMQ Message Broker")
    draw_node_box(260, L4_y + 82, 260, 44, "Hệ thống Email TDTU (SMTP)")

    # Crop ảnh vừa vặn
    final_h = L4_y + L4_h + 35
    img_cropped = img.crop((0, 0, W, final_h))

    # Lưu ảnh ra thư mục diagrams
    out_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "diagrams", "so_do_kien_truc.jpg"
    )
    img_rgb = img_cropped.convert("RGB")
    img_rgb.save(out_file, quality=95)

if __name__ == "__main__":
    create_architecture_diagram()
