import os
from PIL import Image, ImageDraw, ImageFont

def draw_usecase():
    W, H = 1100, 800
    img = Image.new("RGBA", (W, H), "#FAFAFA")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 28)
        font_main = ImageFont.truetype("arialbd.ttf", 16)
        font_sub = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font_title = ImageFont.load_default()
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Title
    draw.text((W//2 - 200, 30), "USE CASE DIAGRAM: iBanking Tuition Payment", font=font_title, fill="#111111")

    # System Boundary (Rectangle)
    sys_x1, sys_y1 = 300, 100
    sys_x2, sys_y2 = 800, 750
    draw.rectangle([sys_x1, sys_y1, sys_x2, sys_y2], outline="#333333", width=2)
    draw.text((sys_x1 + 150, sys_y1 + 20), "iBanking System (Microservices)", font=font_title, fill="#333333")

    # Use cases
    usecases = [
        {"id": 1, "text": "1. Login & Authenticate", "y": 180},
        {"id": 2, "text": "2. View Account Balance", "y": 270},
        {"id": 3, "text": "3. Query Tuition (by Student ID)", "y": 360},
        {"id": 4, "text": "4. Initiate Payment", "y": 450},
        {"id": 5, "text": "5. Receive & Verify OTP", "y": 540},
        {"id": 6, "text": "6. View Transaction History", "y": 630}
    ]

    uc_w = 340
    uc_h = 60
    uc_x = sys_x1 + (sys_x2 - sys_x1)//2

    for uc in usecases:
        x1 = uc_x - uc_w//2
        y1 = uc["y"]
        x2 = uc_x + uc_w//2
        y2 = uc["y"] + uc_h
        draw.ellipse([x1, y1, x2, y2], fill="#FFFFFF", outline="#111111", width=2)
        # Center text
        text_w = len(uc["text"]) * 8 # Approximate
        draw.text((x1 + uc_w//2 - text_w, y1 + 20), uc["text"], font=font_main, fill="#111111")

    # Actor (Stickman)
    actor_x = 150
    actor_y = 350
    # Head
    draw.ellipse([actor_x-20, actor_y-40, actor_x+20, actor_y], outline="#111111", width=3)
    # Body
    draw.line([(actor_x, actor_y), (actor_x, actor_y+60)], fill="#111111", width=3)
    # Arms
    draw.line([(actor_x-30, actor_y+20), (actor_x+30, actor_y+20)], fill="#111111", width=3)
    # Legs
    draw.line([(actor_x, actor_y+60), (actor_x-25, actor_y+110)], fill="#111111", width=3)
    draw.line([(actor_x, actor_y+60), (actor_x+25, actor_y+110)], fill="#111111", width=3)
    draw.text((actor_x-60, actor_y+120), "Student / Parent", font=font_main, fill="#111111")

    # Connect Actor to Usecases
    for uc in usecases:
        draw.line([(actor_x+40, actor_y+30), (uc_x - uc_w//2 - 10, uc["y"] + uc_h//2)], fill="#555555", width=2)

    # External Systems
    ext_x = 880
    
    # Email SMTP
    draw.rectangle([ext_x, 480, ext_x+180, 560], fill="#F0F0F0", outline="#111111", width=2)
    draw.text((ext_x+30, 500), "Email System\n(Gmail SMTP)", font=font_main, fill="#111111")
    
    # RabbitMQ
    draw.rectangle([ext_x, 300, ext_x+180, 380], fill="#F0F0F0", outline="#111111", width=2)
    draw.text((ext_x+30, 320), "Message Broker\n(RabbitMQ)", font=font_main, fill="#111111")

    # Connect Usecase 5 to RabbitMQ & Email
    # Initiate Payment -> RabbitMQ
    draw.line([(uc_x + uc_w//2 + 10, 480), (ext_x-10, 340)], fill="#555555", width=2) # UC4 to MQ
    # Verify OTP -> MQ -> Email
    draw.line([(uc_x + uc_w//2 + 10, 570), (ext_x-10, 520)], fill="#555555", width=2) # UC5 to Email (simplified)

    # Save
    os.makedirs('docs/diagrams', exist_ok=True)
    img.save('docs/diagrams/so_do_usecase.jpg', quality=95)

if __name__ == "__main__":
    draw_usecase()
