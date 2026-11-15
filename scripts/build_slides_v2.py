"""
Build the upgraded 15-slide midterm presentation deck (docs/Slide_SOA_v2.pptx)
from docs/presentation_backup.pptx (preserving TDTU branding, layout green bar,
and Slide 1/2 metadata while adding REST API, OTP Security, Concurrency,
Testing/Deployment, Demo Plan, and Rubric Coverage slides).

Usage:
    python scripts/build_slides_v2.py
"""

from __future__ import annotations

import os
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
BACKUP_PPTX = ROOT / "docs" / "presentation_backup.pptx"
OUT_PPTX = ROOT / "docs" / "Slide_SOA_v2.pptx"
LOGO_TMP = Path(os.environ.get("TEMP", "/tmp")) / "tdtu_header_logo.png"

# Colors matching TDTU green bar (#387A23) & clean executive palette
GREEN_DARK = RGBColor(0x38, 0x7A, 0x23)
GREEN_SOFT = RGBColor(0xEC, 0xF5, 0xE9)
GREEN_BORDER = RGBColor(0x95, 0xC4, 0x82)

NAVY = RGBColor(0x0F, 0x2C, 0x59)
BLUE = RGBColor(0x1D, 0x4E, 0xD8)
BLUE_SOFT = RGBColor(0xEF, 0xF6, 0xFF)
BLUE_BORDER = RGBColor(0x93, 0xC5, 0xFD)

AMBER = RGBColor(0xB4, 0x53, 0x09)
AMBER_SOFT = RGBColor(0xFF, 0xF7, 0xED)
AMBER_BORDER = RGBColor(0xFD, 0xBA, 0x74)

RED_DARK = RGBColor(0x99, 0x1B, 0x1B)
RED_SOFT = RGBColor(0xFE, 0xF2, 0xF2)
RED_BORDER = RGBColor(0xFC, 0xA5, 0xA5)

TEXT_DARK = RGBColor(0x1E, 0x29, 0x3B)
TEXT_MUTED = RGBColor(0x47, 0x55, 0x69)
CARD_BG = RGBColor(0xF8, 0xFA, 0xFC)
CARD_BORDER = RGBColor(0xCB, 0xD5, 0xE1)
CODE_BG = RGBColor(0x0F, 0x17, 0x2A)
CODE_FG = RGBColor(0xE2, 0xE8, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT_SANS = "Arial"
FONT_MONO = "Consolas"


# ---------------------------------------------------------------------------
# Low-level XML & layout helpers
# ---------------------------------------------------------------------------
def clear_slide_shapes(slide) -> None:
    """Remove ALL shapes including Google Slides <mc:AlternateContent> blocks."""
    sp_tree = slide._element.cSld.spTree
    keep = {qn("p:nvGrpSpPr"), qn("p:grpSpPr")}
    for child in list(sp_tree):
        if child.tag not in keep:
            sp_tree.remove(child)


def add_textbox(slide, left, top, width, height, word_wrap=True, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = word_wrap
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.06)
    tf.margin_right = Inches(0.06)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    return tf


def add_card(
    slide,
    left,
    top,
    width,
    height,
    fill_color=CARD_BG,
    border_color=CARD_BORDER,
    border_pt=1.0,
    rounded=True,
):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shape_type, left, top, width, height)
    if rounded and hasattr(sh, "adjustments") and len(sh.adjustments) > 0:
        sh.adjustments[0] = 0.04
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill_color
    sh.line.color.rgb = border_color
    sh.line.width = Pt(border_pt)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Inches(0.14)
    tf.margin_right = Inches(0.14)
    tf.margin_top = Inches(0.10)
    tf.margin_bottom = Inches(0.08)
    return sh


def add_run(para, text, size=14, bold=False, italic=False, color=TEXT_DARK, font_name=FONT_SANS):
    run = para.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return run


def add_para(
    tf,
    segments,
    space_after=5,
    space_before=0,
    line_spacing=1.15,
    align=PP_ALIGN.LEFT,
    first=False,
):
    """Add a paragraph built from a list of (text, kwargs) tuples."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after)
    p.space_before = Pt(space_before)
    p.line_spacing = line_spacing
    for seg in segments:
        if isinstance(seg, str):
            add_run(p, seg)
        else:
            txt, kw = seg
            add_run(p, txt, **kw)
    return p


def add_bullets(tf, items, size=14, space_after=5, start_fresh=False):
    """
    items: list of either string or list of (text, kwargs) tuples.
    Prepends a crisp bullet '• ' cleanly without broken Word list indents.
    """
    for idx, item in enumerate(items):
        is_first = start_fresh and idx == 0
        if isinstance(item, str):
            segs = [("• ", {"size": size, "bold": True, "color": GREEN_DARK}), (item, {"size": size})]
        else:
            segs = [("• ", {"size": size, "bold": True, "color": GREEN_DARK})] + list(item)
        add_para(tf, segs, space_after=space_after, first=is_first)


def add_picture_fit(slide, img_path: Path, left, top, max_width, max_height, border=True):
    """Insert image preserving aspect ratio centered inside (left, top, max_width, max_height)."""
    with Image.open(img_path) as im:
        iw, ih = im.size
    ratio = iw / ih
    box_ratio = max_width / max_height
    if ratio >= box_ratio:
        w = max_width
        h = int(max_width / ratio)
    else:
        h = max_height
        w = int(max_height * ratio)
    x = int(left + (max_width - w) / 2)
    y = int(top + (max_height - h) / 2)
    if border:
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x - 18000, y - 18000, w + 36000, h + 36000)
        bg.fill.solid()
        bg.fill.fore_color.rgb = WHITE
        bg.line.color.rgb = CARD_BORDER
        bg.line.width = Pt(1.0)
    return slide.shapes.add_picture(str(img_path), x, y, w, h)


def style_table(table, col_widths, header_bg=NAVY, font_size=11.5, row_pad_tb=0.05):
    for i, w in enumerate(col_widths):
        table.columns[i].width = w
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(row_pad_tb)
            cell.margin_bottom = Inches(row_pad_tb)
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = header_bg
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = WHITE
            else:
                cell.fill.fore_color.rgb = CARD_BG


def set_cell_text(cell, segments, size=11.5, align=PP_ALIGN.LEFT, default_color=TEXT_DARK):
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    for seg in segments:
        if isinstance(seg, str):
            add_run(p, seg, size=size, color=default_color)
        else:
            txt, kw = seg
            kw_merged = {"size": size, "color": default_color, **kw}
            add_run(p, txt, **kw_merged)


def setup_content_slide(slide, title_text: str, slide_num: int, section_tag: str = ""):
    """Reset slide shapes and place TDTU logo, title, section pill (optional), and slide number."""
    clear_slide_shapes(slide)
    # TDTU logo top-left (exact coordinates from template)
    slide.shapes.add_picture(str(LOGO_TMP), -1, 524541, 1266895, 763500)

    # Slide title
    tf_title = add_textbox(slide, 1320000, 520000, 7680000, 780000, anchor=MSO_ANCHOR.MIDDLE)
    tf_title.margin_top = Inches(0)
    tf_title.margin_bottom = Inches(0)
    p = tf_title.paragraphs[0]
    if section_tag:
        add_run(p, f"{section_tag} | ", size=16.5, bold=True, color=GREEN_DARK)
    add_run(p, title_text, size=20.5, bold=True, color=NAVY)

    # Slide number bottom-right
    tf_num = add_textbox(slide, 8450000, 6240000, 560000, 460000, anchor=MSO_ANCHOR.MIDDLE)
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    add_run(p_num, str(slide_num), size=12, bold=True, color=TEXT_MUTED)


# ---------------------------------------------------------------------------
# Individual slide builders
# ---------------------------------------------------------------------------
def upgrade_slide_1(slide):
    """Keep existing Title slide branding and insert project topic cleanly."""
    # Add topic subtitle cleanly in the empty band between (504070) and MIDTERM PRESENTATION
    tf = add_textbox(slide, Inches(0.6), Inches(3.68), Inches(8.8), Inches(0.65), anchor=MSO_ANCHOR.MIDDLE)
    add_para(
        tf,
        [("Online Tuition Payment System (iBanking) — Microservices SOA", {"size": 19, "bold": True, "color": GREEN_DARK})],
        align=PP_ALIGN.CENTER,
        space_after=0,
        first=True,
    )


def upgrade_slide_2(slide):
    """Keep existing Team Members slide and polish role descriptions."""
    for sh in slide.shapes:
        if sh.shape_type == 19:  # TABLE
            t = sh.table
            updates = {
                (1, 3): "System Design, API Gateway & 6 Microservices, React UI, Testing, Docker",
                (2, 3): "System Analysis, UML & ERD Diagrams, Technical Report, Concurrency Testing",
            }
            for (r, c), text in updates.items():
                cell = t.cell(r, c)
                p = cell.text_frame.paragraphs[0]
                p.text = text
                for run in p.runs:
                    run.font.name = FONT_SANS
                    run.font.size = Pt(14)


def build_slide_3_overview(slide):
    setup_content_slide(slide, "System Overview & Use Case Diagram", 3, "1. Overview")

    # Left summary card
    sh = add_card(slide, Inches(0.28), Inches(1.82), Inches(3.90), Inches(4.86), fill_color=WHITE)
    tf = sh.text_frame
    add_para(tf, [("Problem Context", {"size": 15.5, "bold": True, "color": NAVY})], space_after=3, first=True)
    add_para(
        tf,
        [("TDTU online tuition payment via React 18 SPA routed through an API Gateway.", {"size": 14})],
        space_after=7,
    )
    add_para(tf, [("Actors & External Systems", {"size": 15.5, "bold": True, "color": NAVY})], space_after=3)
    add_bullets(
        tf,
        [
            [("Student / Parent: ", {"bold": True}), ("Auth, lookup, pay & OTP", {"size": 14})],
            [("RabbitMQ & Gmail: ", {"bold": True}), ("Async email notifications", {"size": 14})],
        ],
        size=14,
        space_after=4,
    )
    add_para(tf, [("6 Core Use Cases", {"size": 15.5, "bold": True, "color": NAVY})], space_after=3, space_before=4)
    add_bullets(
        tf,
        [
            "1. Login & JWT Authentication",
            "2. View Real-Time Account Balance",
            "3. Search Tuition Fee by MSSV",
            "4. Initiate Payment (Idempotent)",
            "5. Receive & Verify 6-Digit OTP",
            "6. View History & E-Receipt",
        ],
        size=14,
        space_after=2,
    )

    add_picture_fit(slide, ROOT / "docs" / "images" / "hinh_3_1_use_case.png", Inches(4.32), Inches(1.82), Inches(5.40), Inches(4.86))


def build_slide_4_architecture(slide):
    setup_content_slide(slide, "Microservices Architecture & API Gateway", 4, "2. Design")

    sh = add_card(slide, Inches(0.28), Inches(1.82), Inches(4.50), Inches(4.86), fill_color=WHITE)
    tf = sh.text_frame
    add_para(tf, [("Layered SOA Topology", {"size": 15.5, "bold": True, "color": NAVY})], space_after=4, first=True)
    add_bullets(
        tf,
        [
            [("Client: ", {"bold": True, "color": NAVY}), ("React 18 + Tailwind CSS SPA", {"size": 14})],
            [("API Gateway (:8000): ", {"bold": True, "color": NAVY}), ("Single entry, JWT verify, ", {"size": 14}), ("X-Correlation-ID", {"size": 13, "font_name": FONT_MONO, "color": BLUE}), (" tracing", {"size": 14})],
            [("6 Microservices: ", {"bold": True, "color": NAVY}), ("Stateless FastAPI services", {"size": 14})],
            [("Database-per-Service: ", {"bold": True, "color": NAVY}), ("5 isolated PostgreSQL 16 DBs (no shared tables)", {"size": 14})],
            [("Async & External: ", {"bold": True, "color": NAVY}), ("RabbitMQ 3.13 + Gmail SMTP", {"size": 14})],
        ],
        size=14,
        space_after=4,
    )
    add_para(tf, [("Why Microservices?", {"size": 15.5, "bold": True, "color": GREEN_DARK})], space_after=3, space_before=4)
    add_bullets(
        tf,
        [
            "Independent scaling of Payment & OTP",
            "Clear domain & data ownership",
            "Fault isolation: SMTP never blocks checkout",
        ],
        size=14,
        space_after=2,
    )

    add_picture_fit(slide, ROOT / "docs" / "diagrams" / "so_do_kien_truc.jpg", Inches(4.92), Inches(1.82), Inches(4.80), Inches(4.86))


def build_slide_5_services(slide):
    setup_content_slide(slide, "Service Decomposition & Data Ownership", 5, "2. Design")

    rows = [
        ("Service / Port", "Owned Data Store", "Core Responsibility & Design Rationale"),
        ("api-gateway :8000", "Stateless (HTTP proxy)", "Single entry point, validates HS256 JWT, injects X-User-ID & X-Correlation-ID"),
        ("auth-service :8001", "auth_db (PostgreSQL)", "Credential storage (bcrypt), JWT issuance & /me identity verification"),
        ("user-service :8002", "user_db (PostgreSQL)", "Payer profiles, balance debit/refund (FOR UPDATE), transaction_histories"),
        ("tuition-service :8003", "tuition_db (PostgreSQL)", "Student records & UNPAID/PAID fees; atomic mark-paid lock (FOR UPDATE)"),
        ("payment-service :8004", "payment_db (PostgreSQL)", "Saga Orchestrator, Idempotency-Key guard, transaction audit state machine"),
        ("otp-service :8005", "otp_db (PostgreSQL)", "CSPRNG 6-digit OTP generation, 5m TTL, 1-time verify, 5-attempt lockout"),
        ("notification-service :8006", "Stateless Worker", "Consumes RabbitMQ (otp_email, payment_success); sends Gmail SMTP w/ retry"),
    ]
    tbl_shape = slide.shapes.add_table(len(rows), 3, Inches(0.28), Inches(1.85), Inches(9.44), Inches(4.80))
    t = tbl_shape.table
    style_table(t, [Inches(2.35), Inches(2.15), Inches(4.94)], row_pad_tb=0.06)

    for r_idx, (c1, c2, c3) in enumerate(rows):
        if r_idx == 0:
            set_cell_text(t.cell(r_idx, 0), [(c1, {"bold": True})], size=12, default_color=WHITE)
            set_cell_text(t.cell(r_idx, 1), [(c2, {"bold": True})], size=12, default_color=WHITE)
            set_cell_text(t.cell(r_idx, 2), [(c3, {"bold": True})], size=12, default_color=WHITE)
        else:
            set_cell_text(t.cell(r_idx, 0), [(c1, {"bold": True, "font_name": FONT_MONO, "color": NAVY})], size=11.5)
            set_cell_text(t.cell(r_idx, 1), [(c2, {"bold": "Stateless" not in c2, "color": GREEN_DARK if "DB" in c2.upper() or "_db" in c2 else TEXT_MUTED})], size=11.5)
            set_cell_text(t.cell(r_idx, 2), c3, size=11.5)


def build_slide_6_erd(slide):
    setup_content_slide(slide, "Database-per-Service Physical ERD", 6, "2. Design")

    sh = add_card(slide, Inches(0.28), Inches(1.85), Inches(3.25), Inches(4.80), fill_color=WHITE)
    tf = sh.text_frame
    add_para(tf, [("5 Isolated Databases", {"size": 16, "bold": True, "color": NAVY})], space_after=4, first=True)
    add_bullets(
        tf,
        [
            [("Solid Lines: ", {"bold": True, "color": BLUE}), ("Physical FKs inside ", {"size": 14}), ("user_db", {"size": 13, "font_name": FONT_MONO}), (" & ", {"size": 14}), ("tuition_db", {"size": 13, "font_name": FONT_MONO})],
            [("Dashed Lines: ", {"bold": True, "color": AMBER}), ("Logical UUID/MSSV refs across services (no cross-DB JOIN)", {"size": 14})],
        ],
        size=14,
        space_after=6,
    )
    add_para(tf, [("DB Constraints & Integrity", {"size": 16, "bold": True, "color": NAVY})], space_after=4, space_before=6)
    add_bullets(
        tf,
        [
            [("UNIQUE: ", {"bold": True, "color": GREEN_DARK}), ("username, email, mssv, idempotency_key, otp.transaction_id", {"size": 13.5})],
            [("CHECK: ", {"bold": True, "color": GREEN_DARK}), ("tuition_fees.amount > 0; balance >= amount", {"size": 13.5})],
            [("Money type: ", {"bold": True, "color": GREEN_DARK}), ("Numeric(15, 2) (zero float drift)", {"size": 13.5})],
        ],
        size=14,
        space_after=4,
    )

    add_picture_fit(slide, ROOT / "docs" / "images" / "hinh_3_3b_soa_erd.png", Inches(3.66), Inches(1.85), Inches(6.06), Inches(4.80))


def build_slide_7_api(slide):
    setup_content_slide(slide, "REST API Design & Validation Contract", 7, "2. Design")

    rows = [
        ("Method & URI (via Gateway :8000)", "Purpose", "Request / Key Headers", "HTTP Status Codes"),
        ("POST /api/auth/login", "Authenticate & issue JWT", "{ username, password }", "200 OK / 401 Invalid"),
        ("GET /api/users/me, /me/balance", "Profile & live balance", "Authorization: Bearer <jwt>", "200 OK / 401 / 404"),
        ("GET /api/tuition/{mssv}", "Lookup student & UNPAID fees", "Path: mssv", "200 OK / 404 Not Found"),
        ("POST /api/payments/initiate", "Pre-check & create PENDING tx", "Idempotency-Key + {mssv, fee_id}", "201 Created / 400 / 409"),
        ("POST /api/payments/{id}/confirm", "Trigger OTP gen & RabbitMQ email", "Bearer JWT (owner check)", "200 OTP_SENT / 403 / 400"),
        ("POST /api/payments/{id}/verify-otp", "Verify OTP & run Saga debit+pay", "{ otp_code }", "200 / 401 / 409 / 429"),
        ("GET /api/payments", "Paginated audit history", "?page=1&size=10", "200 OK / 401"),
    ]
    tbl_shape = slide.shapes.add_table(len(rows), 4, Inches(0.28), Inches(1.85), Inches(9.44), Inches(3.85))
    t = tbl_shape.table
    style_table(t, [Inches(2.85), Inches(2.35), Inches(2.35), Inches(1.89)], row_pad_tb=0.04)

    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            if r_idx == 0:
                set_cell_text(t.cell(r_idx, c_idx), [(val, {"bold": True})], size=11.5, default_color=WHITE)
            elif c_idx == 0:
                set_cell_text(t.cell(r_idx, c_idx), [(val, {"bold": True, "font_name": FONT_MONO, "color": BLUE})], size=11)
            elif c_idx == 3:
                set_cell_text(t.cell(r_idx, c_idx), [(val, {"bold": True, "color": GREEN_DARK})], size=11)
            else:
                set_cell_text(t.cell(r_idx, c_idx), val, size=11)

    # Bottom validation & Swagger banner
    sh = add_card(slide, Inches(0.28), Inches(5.82), Inches(9.44), Inches(0.84), fill_color=BLUE_SOFT, border_color=BLUE_BORDER)
    tf = sh.text_frame
    add_para(
        tf,
        [
            ("Contract Standards: ", {"size": 14, "bold": True, "color": NAVY}),
            ("Pydantic v2 schema validation auto-returns ", {"size": 14}),
            ("422 Unprocessable Entity", {"size": 14, "bold": True, "color": BLUE}),
            ("; unified JSON errors ", {"size": 14}),
            ('{"detail": "..."}', {"size": 13, "font_name": FONT_MONO, "color": NAVY}),
            ("; OpenAPI /docs on every service.", {"size": 14}),
        ],
        space_after=0,
        first=True,
    )


def build_slide_8_workflow(slide):
    setup_content_slide(slide, "End-to-End Payment Workflow", 8, "3. Solutions")

    sh = add_card(slide, Inches(0.28), Inches(1.82), Inches(3.30), Inches(4.86), fill_color=WHITE)
    tf = sh.text_frame
    add_para(tf, [("5 Execution Stages", {"size": 15.5, "bold": True, "color": NAVY})], space_after=5, first=True)
    stages = [
        ("1. Auth & JWT: ", "Gateway verifies token & sets X-User-ID."),
        ("2. Tuition Inquiry: ", "Fetch UNPAID fees by MSSV."),
        ("3. Initiate & Dedup: ", "Idempotency-Key check; verify balance & status."),
        ("4. Async OTP Email: ", "Generate 6-digit OTP; push email via RabbitMQ."),
        ("5. Saga & Receipt: ", "Verify OTP → deduct → PAID (or refund) → e-receipt."),
    ]
    for title_part, desc in stages:
        add_para(
            tf,
            [(title_part, {"size": 14, "bold": True, "color": GREEN_DARK}), (desc, {"size": 14})],
            space_after=5,
            line_spacing=1.10,
        )

    add_picture_fit(slide, ROOT / "docs" / "images" / "hinh_3_4_workflow_archify.png", Inches(3.72), Inches(1.82), Inches(6.00), Inches(4.86))


def build_slide_9_otp(slide):
    setup_content_slide(slide, "OTP Two-Factor Verification & Security", 9, "3. Solutions")

    # Left card: Generation & Binding
    sh1 = add_card(slide, Inches(0.28), Inches(1.85), Inches(4.56), Inches(4.80), fill_color=WHITE)
    tf1 = sh1.text_frame
    add_para(tf1, [("1. Generation & Transaction Binding", {"size": 16, "bold": True, "color": NAVY})], space_after=8, first=True)
    add_bullets(
        tf1,
        [
            [("CSPRNG Generator: ", {"bold": True, "color": GREEN_DARK}), ("Uses Python ", {"size": 14}), ('secrets.choice("0123456789")', {"size": 13, "font_name": FONT_MONO, "color": BLUE}), (" instead of predictable PRNG random.", {"size": 14})],
            [("1:1 Transaction Binding: ", {"bold": True, "color": GREEN_DARK}), ("otp_codes.transaction_id", {"size": 13, "font_name": FONT_MONO}), (" has UNIQUE constraint — one active OTP per payment.", {"size": 14})],
            [("Atomic Resend Lock: ", {"bold": True, "color": GREEN_DARK}), ("SELECT ... FOR UPDATE deletes prior OTP before issuing a fresh code.", {"size": 14})],
            [("Async Delivery: ", {"bold": True, "color": GREEN_DARK}), ("Published to ", {"size": 14}), ("otp_email", {"size": 13, "font_name": FONT_MONO}), (" queue and delivered via Gmail SMTP.", {"size": 14})],
        ],
        size=14,
        space_after=8,
    )

    # Right card: Verification Lifecycle & Hardening
    sh2 = add_card(slide, Inches(5.12), Inches(1.85), Inches(4.60), Inches(4.80), fill_color=GREEN_SOFT, border_color=GREEN_BORDER)
    tf2 = sh2.text_frame
    add_para(tf2, [("2. Lifecycle & Security Hardening", {"size": 16, "bold": True, "color": GREEN_DARK})], space_after=8, first=True)
    add_bullets(
        tf2,
        [
            [("5-Minute TTL: ", {"bold": True, "color": NAVY}), ("Strict UTC expiry check (expires_at <= now -> HTTP 400).", {"size": 14})],
            [("Single-Use Flag: ", {"bold": True, "color": NAVY}), ("Row locked via FOR UPDATE, verified once and marked is_used = True.", {"size": 14})],
            [("Brute-Force Lockout: ", {"bold": True, "color": NAVY}), ("Tracks failed_attempts; locks OTP at 5 wrong guesses with ", {"size": 14}), ("HTTP 429", {"size": 14, "bold": True, "color": RED_DARK}), (".", {"size": 14})],
            [("Zero Leakage: ", {"bold": True, "color": NAVY}), ("Constant-time ", {"size": 14}), ("secrets.compare_digest", {"size": 13, "font_name": FONT_MONO}), ("; OTP omitted from API & logs when ", {"size": 14}), ("OTP_DEBUG_EXPOSE=false", {"size": 12.5, "font_name": FONT_MONO}), (".", {"size": 14})],
        ],
        size=14,
        space_after=8,
    )


def build_slide_10_saga(slide):
    setup_content_slide(slide, "Saga Pattern & Distributed Transaction", 10, "3. Solutions")

    sh = add_card(slide, Inches(0.28), Inches(1.85), Inches(4.35), Inches(4.80), fill_color=WHITE)
    tf = sh.text_frame
    add_para(tf, [("Why Saga over 2PC?", {"size": 15.5, "bold": True, "color": NAVY})], space_after=3, first=True)
    add_bullets(
        tf,
        [
            "Avoids cross-DB distributed locks across 5 PostgreSQL DBs.",
            [("Model: ", {"bold": True}), ("Local ACID per DB + ", {"size": 14}), ("Eventual Consistency", {"size": 14, "bold": True, "color": BLUE}), (".", {"size": 14})],
        ],
        size=14,
        space_after=4,
    )
    add_para(tf, [("Orchestrator: PaymentService", {"size": 15.5, "bold": True, "color": NAVY})], space_after=3, space_before=4)
    add_bullets(
        tf,
        [
            [("States: ", {"bold": True}), ("PENDING → OTP_SENT → SUCCESS | FAILED | REFUNDED", {"size": 12.5, "font_name": FONT_MONO, "color": BLUE})],
            [("Step A: ", {"bold": True, "color": GREEN_DARK}), ("PUT /users/{id}/balance (deduct).", {"size": 14})],
            [("Step B: ", {"bold": True, "color": GREEN_DARK}), ("PUT /tuition/fee/{id}/pay (mark PAID).", {"size": 14})],
            [("Compensate: ", {"bold": True, "color": RED_DARK}), ("If Step B returns 409/503, immediately call refund and mark ", {"size": 14}), ("REFUNDED", {"size": 13.5, "bold": True, "color": AMBER}), (".", {"size": 14})],
        ],
        size=14,
        space_after=4,
    )

    add_picture_fit(slide, ROOT / "docs" / "diagrams" / "so_do_sequence.jpg", Inches(4.78), Inches(1.85), Inches(4.94), Inches(4.80))


def build_slide_11_concurrency(slide):
    setup_content_slide(slide, "Concurrency Control (Pessimistic Lock)", 11, "3. Solutions")

    # Scenario 1 Card
    sh1 = add_card(slide, Inches(0.28), Inches(1.85), Inches(4.60), Inches(2.40), fill_color=BLUE_SOFT, border_color=BLUE_BORDER)
    tf1 = sh1.text_frame
    add_para(tf1, [("Scenario 1: Single Account Double-Spending", {"size": 15, "bold": True, "color": NAVY})], space_after=4, first=True)
    add_bullets(
        tf1,
        [
            "1 user sends 2 concurrent payments where total > balance.",
            [("user-service", {"bold": True}), (" acquires row lock on ", {"size": 13.5}), ("user_profiles", {"size": 13, "font_name": FONT_MONO}), (".", {"size": 13.5})],
            "Tx 1 deducts; Tx 2 waits, sees insufficient funds -> 400 (FAILED). Zero negative balance.",
        ],
        size=13.5,
        space_after=3,
    )

    # Scenario 2 Card
    sh2 = add_card(slide, Inches(5.12), Inches(1.85), Inches(4.60), Inches(2.40), fill_color=AMBER_SOFT, border_color=AMBER_BORDER)
    tf2 = sh2.text_frame
    add_para(tf2, [("Scenario 2: Multi-Account Same Tuition Fee", {"size": 15, "bold": True, "color": AMBER})], space_after=4, first=True)
    add_bullets(
        tf2,
        [
            "2 users pay the same tuition_fee_id at the exact same moment.",
            [("tuition-service", {"bold": True}), (" acquires row lock on ", {"size": 13.5}), ("tuition_fees", {"size": 13, "font_name": FONT_MONO}), (".", {"size": 13.5})],
            "User 1 marks PAID (200); User 2 sees PAID -> 409 Conflict -> automatic Saga Refund!",
        ],
        size=13.5,
        space_after=3,
    )

    # Bottom Code Snippet Card (correct file attribution!)
    sh_code = add_card(slide, Inches(0.28), Inches(4.38), Inches(9.44), Inches(2.26), fill_color=CODE_BG, border_color=NAVY)
    tf_c = sh_code.text_frame
    add_para(
        tf_c,
        [("services/user-service/app/service.py & services/tuition-service/app/service.py", {"size": 12.5, "bold": True, "color": RGBColor(0x93, 0xC5, 0xFD), "font_name": FONT_MONO})],
        space_after=4,
        first=True,
    )
    code_lines = [
        "# Pessimistic row-level lock prevents dirty reads & lost updates across workers:",
        "stmt = select(UserProfile).where(UserProfile.id == user_id).with_for_update()",
        "user = (await db.execute(stmt)).scalar_one_or_none()",
        "if user.balance < amount:",
        '    raise HTTPException(status_code=400, detail="Insufficient balance")',
    ]
    for ln in code_lines:
        add_para(tf_c, [(ln, {"size": 12.5, "color": CODE_FG, "font_name": FONT_MONO})], space_after=2)


def build_slide_12_async(slide):
    setup_content_slide(slide, "Async Messaging (RabbitMQ) & Tracing", 12, "3. Solutions")

    # Flow diagram row using native shapes
    y_box = Inches(2.05)
    h_box = Inches(1.25)
    boxes = [
        (Inches(0.30), Inches(1.95), BLUE_SOFT, BLUE_BORDER, "Producers", "otp-service\npayment-service"),
        (Inches(2.63), Inches(2.50), AMBER_SOFT, AMBER_BORDER, "RabbitMQ 3.13", "otp_email\npayment_success"),
        (Inches(5.51), Inches(2.15), GREEN_SOFT, GREEN_BORDER, "Notification Worker", "notification-service\n(aio-pika consumer)"),
        (Inches(8.02), Inches(1.70), CARD_BG, CARD_BORDER, "Gmail SMTP", "aiosmtplib\nOTP + E-Receipt"),
    ]
    for x, w, fill, border, title, body in boxes:
        sh = add_card(slide, x, y_box, w, h_box, fill_color=fill, border_color=border)
        sh.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = sh.text_frame
        add_para(tf, [(title, {"size": 14, "bold": True, "color": NAVY})], align=PP_ALIGN.CENTER, space_after=3, first=True)
        add_para(tf, [(body, {"size": 12.5, "color": TEXT_DARK})], align=PP_ALIGN.CENTER, space_after=0)

    # Arrows between boxes
    for ax in [Inches(2.29), Inches(5.16), Inches(7.69)]:
        arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, ax, Inches(2.50), Inches(0.30), Inches(0.34))
        arr.fill.solid()
        arr.fill.fore_color.rgb = GREEN_DARK
        arr.line.fill.background()

    # Two feature cards below
    sh_l = add_card(slide, Inches(0.30), Inches(3.55), Inches(4.55), Inches(3.05), fill_color=WHITE)
    tf_l = sh_l.text_frame
    add_para(tf_l, [("Async Reliability & Performance", {"size": 15.5, "bold": True, "color": NAVY})], space_after=6, first=True)
    add_bullets(
        tf_l,
        [
            [("Non-blocking Checkout: ", {"bold": True, "color": GREEN_DARK}), ("Decouples 1-3s Gmail SMTP I/O so API responds cleanly without blocking users.", {"size": 14})],
            [("Exponential Backoff Retry: ", {"bold": True, "color": GREEN_DARK}), ("consumer.py retries transient failures 3 times (1s → 2s → 4s) before dead-lettering.", {"size": 14})],
            "Durable queues + persistent delivery mode preserve events across restarts.",
        ],
        size=14,
        space_after=6,
    )

    sh_r = add_card(slide, Inches(5.10), Inches(3.55), Inches(4.62), Inches(3.05), fill_color=WHITE)
    tf_r = sh_r.text_frame
    add_para(tf_r, [("Distributed Tracing & Auditability", {"size": 15.5, "bold": True, "color": NAVY})], space_after=6, first=True)
    add_bullets(
        tf_r,
        [
            [("X-Correlation-ID Propagation: ", {"bold": True, "color": BLUE}), ("Gateway assigns UUID per request and forwards it across all internal HTTP calls.", {"size": 14})],
            [("Cross-Boundary Trace: ", {"bold": True, "color": BLUE}), ("Carried inside RabbitMQ JSON payloads to Notification Worker logs.", {"size": 14})],
            "Structured JSON logs in every container allow instant tracing of any transaction.",
        ],
        size=14,
        space_after=6,
    )


def build_slide_13_demo(slide):
    setup_content_slide(slide, "Testing, Docker & 5-Min Live Demo Plan", 13, "4. Demo Plan")

    # Left card: Automated Testing & Docker
    sh_l = add_card(slide, Inches(0.28), Inches(1.85), Inches(4.58), Inches(4.80), fill_color=WHITE)
    tf_l = sh_l.text_frame
    add_para(tf_l, [("Automated Testing", {"size": 16, "bold": True, "color": NAVY})], space_after=4, first=True)
    add_bullets(
        tf_l,
        [
            [("tests/test_otp_and_saga.py: ", {"bold": True, "font_name": FONT_MONO, "size": 12.5, "color": BLUE}), ("8 pytest tests covering OTP TTL, single-use, 429 lockout, idempotency & Saga compensation.", {"size": 13.5})],
            [("test_concurrency_scenarios.py: ", {"bold": True, "font_name": FONT_MONO, "size": 12.5, "color": BLUE}), ("Live E2E assertions for both concurrency cases.", {"size": 13.5})],
        ],
        size=13.5,
        space_after=5,
    )
    add_para(tf_l, [("Docker Compose Packaging", {"size": 16, "bold": True, "color": NAVY})], space_after=4, space_before=6)
    add_bullets(
        tf_l,
        [
            "10 containers: postgres (5 DBs), rabbitmq, gateway, 6 services, React frontend.",
            "healthcheck + depends_on: service_healthy ensures deterministic boot order.",
            "1-click launch via run.py / start.bat + sample dataset in scripts/seed_data.py.",
        ],
        size=13.5,
        space_after=4,
    )

    # Right card: 5-Minute Live Demo Plan
    sh_r = add_card(slide, Inches(5.10), Inches(1.85), Inches(4.62), Inches(4.80), fill_color=GREEN_SOFT, border_color=GREEN_BORDER)
    tf_r = sh_r.text_frame
    add_para(tf_r, [("5-Minute Live Demo Sequence", {"size": 16, "bold": True, "color": GREEN_DARK})], space_after=8, first=True)
    steps = [
        ("1. Auth & Balance: ", "Login (lephu), inspect JWT & live 80,000,000 VND balance."),
        ("2. Tuition Inquiry: ", "Search MSSV 52100002 -> show UNPAID semesters -> initiate payment."),
        ("3. Email OTP & Settlement: ", "Open real Gmail inbox -> enter 6-digit OTP -> verify deducted balance, PAID badge, history & e-receipt."),
        ("4. Concurrency Proof: ", "Run python scripts/test_concurrency_scenarios.py live to prove 1/2 success in Scenario 1 (400) & Scenario 2 (409 + Refund)."),
        ("5. DB & Logs: ", "Inspect PostgreSQL rows + correlation logs."),
    ]
    for hd, desc in steps:
        add_para(tf_r, [(hd, {"size": 13.5, "bold": True, "color": NAVY}), (desc, {"size": 13.5})], space_after=6)


def build_slide_14_eval(slide):
    setup_content_slide(slide, "Trade-offs & Rubric 10/10 Coverage", 14, "5. Evaluation")

    # Left card: Honest Trade-offs & Future Work
    sh_l = add_card(slide, Inches(0.28), Inches(1.85), Inches(3.85), Inches(4.80), fill_color=WHITE)
    tf_l = sh_l.text_frame
    add_para(tf_l, [("Engineering Trade-offs", {"size": 15.5, "bold": True, "color": NAVY})], space_after=4, first=True)
    add_bullets(
        tf_l,
        [
            [("Eventual Consistency: ", {"bold": True, "color": AMBER}), ("Brief transient state while Saga deducts then marks tuition PAID.", {"size": 13.5})],
            [("Row-Lock Contention: ", {"bold": True, "color": AMBER}), ("FOR UPDATE serializes hot rows; safe & strictly consistent for banking.", {"size": 13.5})],
            [("Internal HTTP Latency: ", {"bold": True, "color": AMBER}), ("Sync REST hops add overhead; mitigate w/ gRPC.", {"size": 13.5})],
        ],
        size=13.5,
        space_after=5,
    )
    add_para(tf_l, [("Future Hardening", {"size": 15.5, "bold": True, "color": GREEN_DARK})], space_after=4, space_before=6)
    add_bullets(
        tf_l,
        [
            "Transactional Outbox Pattern for guaranteed RabbitMQ publish & Saga refund",
            "Gateway rate-limiting & OpenTelemetry tracing",
        ],
        size=13.5,
        space_after=3,
    )

    # Right table: 8 Rubric Criteria Coverage
    rows = [
        ("Rubric Criterion (10.0 pts)", "Evidence in Slide & Codebase"),
        ("1. UML & ERD (1.0)", "Use Case + Conceptual & Distributed Physical ERD (Slides 3, 6)"),
        ("2. Microservices (1.5)", "API Gateway + 6 services + RabbitMQ/SMTP + rationale (Slides 4-5)"),
        ("3. REST API (1.0)", "Full CRUD/Payment URIs, Pydantic 422, OpenAPI /docs (Slide 7)"),
        ("4. DB & Persistence (1.0)", "5 PostgreSQL DBs, Numeric(15,2), UNIQUE/CHECK, seed_data.py"),
        ("5. Payment & OTP (2.0)", "End-to-end flow + CSPRNG, 5m TTL, 1-time, 429 lockout (Slides 8-9)"),
        ("6. Concurrency (1.5)", "FOR UPDATE + Saga Refund + E2E concurrency script (Slides 10-11)"),
        ("7. UI Integration (0.5)", "React 18 SPA connected via API Gateway :8000 (Live Demo)"),
        ("8. Docs & Level 10 (1.5)", "Pytest (8 tests), Idempotency-Key, Correlation-ID, Docker Compose"),
    ]
    tbl_shape = slide.shapes.add_table(len(rows), 2, Inches(4.28), Inches(1.85), Inches(5.44), Inches(4.80))
    t = tbl_shape.table
    style_table(t, [Inches(2.05), Inches(3.39)], row_pad_tb=0.04)
    for r_idx, (c1, c2) in enumerate(rows):
        if r_idx == 0:
            set_cell_text(t.cell(r_idx, 0), [(c1, {"bold": True})], size=11, default_color=WHITE)
            set_cell_text(t.cell(r_idx, 1), [(c2, {"bold": True})], size=11, default_color=WHITE)
        else:
            set_cell_text(t.cell(r_idx, 0), [(c1, {"bold": True, "color": NAVY})], size=11)
            set_cell_text(t.cell(r_idx, 1), c2, size=11)


def build_slide_15_thanks(slide):
    setup_content_slide(slide, "", 15)
    tf = add_textbox(slide, Inches(0.8), Inches(2.50), Inches(8.4), Inches(2.60), anchor=MSO_ANCHOR.MIDDLE)
    add_para(
        tf,
        [("Thank You for Your Attention", {"size": 40, "bold": True, "color": NAVY})],
        align=PP_ALIGN.CENTER,
        space_after=14,
        first=True,
    )
    add_para(
        tf,
        [("Live System Demo  •  Automated Concurrency Test  •  Q&A Session", {"size": 18, "bold": True, "color": GREEN_DARK})],
        align=PP_ALIGN.CENTER,
        space_after=8,
    )
    add_para(
        tf,
        [("Group SOA.26-19 — Service-Oriented Architecture (504070)", {"size": 14, "italic": True, "color": TEXT_MUTED})],
        align=PP_ALIGN.CENTER,
        space_after=0,
    )


def main():
    prs = Presentation(str(BACKUP_PPTX))

    # Extract TDTU header logo bytes from Slide 2
    logo_blob = None
    for sh in prs.slides[1].shapes:
        if sh.shape_type == 13:
            logo_blob = sh.image.blob
            break
    if not logo_blob:
        raise RuntimeError("Could not locate TDTU logo on Slide 2 of presentation_backup.pptx")
    LOGO_TMP.write_bytes(logo_blob)

    # presentation_backup.pptx has 11 slides (index 0..10). Add 4 more TITLE_AND_BODY slides -> 15 total.
    body_layout = prs.slide_layouts[1]
    while len(prs.slides) < 15:
        prs.slides.add_slide(body_layout)

    slides = prs.slides
    upgrade_slide_1(slides[0])
    upgrade_slide_2(slides[1])
    build_slide_3_overview(slides[2])
    build_slide_4_architecture(slides[3])
    build_slide_5_services(slides[4])
    build_slide_6_erd(slides[5])
    build_slide_7_api(slides[6])
    build_slide_8_workflow(slides[7])
    build_slide_9_otp(slides[8])
    build_slide_10_saga(slides[9])
    build_slide_11_concurrency(slides[10])
    build_slide_12_async(slides[11])
    build_slide_13_demo(slides[12])
    build_slide_14_eval(slides[13])
    build_slide_15_thanks(slides[14])

    prs.save(str(OUT_PPTX))
    print(f"Saved {len(prs.slides)} slides to {OUT_PPTX}")


if __name__ == "__main__":
    main()
