"""
ID Card Generator — matches exact NIT Entity Card template.
CR80 size: 85.6mm × 54mm at 300 DPI → 1011 × 638 px
"""

import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from django.conf import settings
from django.utils import timezone

# ── Dimensions ────────────────────────────────────────────────────────────────
DPI        = 300
MM_TO_PX   = DPI / 25.4
CARD_W_MM  = 85.6
CARD_H_MM  = 54.0
W          = int(CARD_W_MM * MM_TO_PX)   # 1011
H          = int(CARD_H_MM * MM_TO_PX)   # 638

# ── Brand colours ─────────────────────────────────────────────────────────────
RED        = (185, 28,  28)
YELLOW     = (234, 179,  8)
YELLOW_BG  = (253, 224, 71)
WHITE      = (255, 255, 255)
DARK       = (30,  30,  30)
NIT_WM     = (210, 215, 230)


def _font(size, bold=False):
    candidates = (
        ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
         '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
         'C:/Windows/Fonts/arialbd.ttf',
         'C:/Windows/Fonts/calibrib.ttf']
        if bold else
        ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
         'C:/Windows/Fonts/arial.ttf',
         'C:/Windows/Fonts/calibri.ttf']
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _tw(draw, text, font):
    try:
        bb = draw.textbbox((0, 0), text, font=font)
        return bb[2] - bb[0]
    except Exception:
        return len(text) * 10


def _make_qr(data, px):
    qr = qrcode.QRCode(version=1, box_size=4, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    return img.resize((px, px), Image.LANCZOS)


def generate_id_card_png(req):
    img  = Image.new('RGB', (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # 1 ── Red header bar
    HDR_H = int(H * 0.185)
    draw.rectangle([(0, 0), (W, HDR_H)], fill=RED)

    PHOTO_RIGHT = int(W * 0.31)
    title_font  = _font(int(HDR_H * 0.58), bold=True)
    title_cx    = PHOTO_RIGHT + (W - PHOTO_RIGHT) // 2
    draw.text((title_cx, HDR_H // 2), "ENTITY CARD",
              fill=YELLOW, font=title_font, anchor="mm")

    # 2 ── Yellow footer bar
    FTR_H = int(H * 0.235)
    FTR_Y = H - FTR_H
    draw.rectangle([(0, FTR_Y), (W, H)], fill=YELLOW_BG)

    af = _font(int(FTR_H * 0.155))
    pad = int(W * 0.018)
    lg  = int(FTR_H * 0.178)
    for i, line in enumerate([
        "204, Durga Bhavani Plaza,",
        "Ameerpet, Hyderabad - 500016.",
        "Ph.040 2374 6666",
        "info@nareshit.com",
        "www.nareshit.com",
    ]):
        draw.text((pad, FTR_Y + int(FTR_H * 0.08) + i * lg),
                  line, fill=DARK, font=af)

    # Naresh i branding right side
    bx = int(W * 0.50)
    by = FTR_Y + int(FTR_H * 0.08)
    br = int(FTR_H * 0.17)
    bcx = bx + br
    bcy = by + br + int(FTR_H * 0.04)
    draw.ellipse([(bcx-br, bcy-br), (bcx+br, bcy+br)], fill=RED)
    draw.text((bcx, bcy), "NiT", fill=WHITE,
              font=_font(br, bold=True), anchor="mm")

    ntx = bcx + br + int(W * 0.008)
    draw.text((ntx, by + int(FTR_H * 0.02)),
              "NARESH i", fill=RED,
              font=_font(int(FTR_H * 0.27), bold=True))
    draw.text((ntx + int(W * 0.022),
               by + int(FTR_H * 0.02) + int(FTR_H * 0.28)),
              "technologies", fill=DARK,
              font=_font(int(FTR_H * 0.17)))
    std = "SOFTWARE TRAINING & DEVELOPMENT"
    sf  = _font(int(FTR_H * 0.125), bold=True)
    sx  = ntx
    sy  = by + int(FTR_H * 0.02) + int(FTR_H * 0.28) + int(FTR_H * 0.20)
    stw = _tw(draw, std, sf)
    spx = int(W * 0.010)
    spy = int(FTR_H * 0.04)
    draw.rounded_rectangle(
        [(sx-spx, sy-spy), (sx+stw+spx, sy+int(FTR_H*0.155))],
        radius=4, fill=DARK)
    draw.text((sx, sy), std, fill=WHITE, font=sf)

    # 3 ── NIT watermark tiled across body
    BODY_TOP = HDR_H
    BODY_BTM = FTR_Y
    wf = _font(int(H * 0.052), bold=True)
    cols, rows = 6, 4
    cstep = (W - PHOTO_RIGHT) // cols
    rstep = (BODY_BTM - BODY_TOP) // rows
    for r in range(rows):
        for c in range(cols):
            draw.text(
                (PHOTO_RIGHT + c*cstep + cstep//2,
                 BODY_TOP    + r*rstep + rstep//2),
                "NIT", fill=NIT_WM, font=wf, anchor="mm")
    wf2 = _font(int(H * 0.045), bold=True)
    for r in range(3):
        draw.text((PHOTO_RIGHT//2,
                   BODY_TOP + r*(BODY_BTM-BODY_TOP)//3
                   + (BODY_BTM-BODY_TOP)//6),
                  "NIT", fill=NIT_WM, font=wf2, anchor="mm")

    # 4 ── Photo box
    PP  = int(W * 0.022)
    PL  = PP
    PT  = HDR_H + PP
    PR  = int(W * 0.285)
    PB  = FTR_Y - PP
    BRD = 4
    draw.rectangle([(PL-BRD, PT-BRD), (PR+BRD, PB+BRD)], fill=RED)
    draw.rectangle([(PL, PT), (PR, PB)], fill=WHITE)

    ph_w = PR - PL
    ph_h = PB - PT
    if req.student_photo:
        try:
            ph_path = os.path.join(settings.MEDIA_ROOT, str(req.student_photo))
            if os.path.exists(ph_path):
                ph = Image.open(ph_path).convert('RGB')
                sw, sh = ph.size
                sr = sw / sh
                dr = ph_w / ph_h
                if sr > dr:
                    nw = int(sh * dr)
                    ph = ph.crop(((sw-nw)//2, 0, (sw-nw)//2+nw, sh))
                else:
                    nh = int(sw / dr)
                    ph = ph.crop((0, (sh-nh)//2, sw, (sh-nh)//2+nh))
                ph = ph.resize((ph_w, ph_h), Image.LANCZOS)
                img.paste(ph, (PL, PT))
        except Exception:
            pass

    # 5 ── Info fields
    FX  = int(W * 0.315)
    FW  = W - FX - int(W * 0.02)
    lf  = _font(int(H * 0.060))
    vf  = _font(int(H * 0.054))
    LC  = (80, 80, 80)
    BODY_H = BODY_BTM - BODY_TOP

    def field(label, value, yc):
        draw.text((FX, yc), f"{label} :", fill=DARK, font=lf, anchor="lm")
        lw   = _tw(draw, f"{label} :", lf)
        lx0  = FX + lw + int(W * 0.010)
        ly   = yc + int(H * 0.022)
        draw.line([(lx0, ly), (FX+FW, ly)], fill=LC, width=2)
        if value:
            draw.text((lx0 + int(W*0.005), yc),
                      str(value)[:28], fill=DARK, font=vf, anchor="lm")

    ys = [BODY_TOP + int(BODY_H * f) for f in [0.13, 0.30, 0.47, 0.63]]
    field("Name",    req.get_display_name(),   ys[0])
    field("Course",  req.get_display_course(),  ys[1])
    field("Batch 1", req.get_display_batch(),   ys[2])
    field("Batch 2", "",                         ys[3])

    # Lower rows: blank line (left) + Batch 4 / Batch 6 (right)
    ly1  = BODY_TOP + int(BODY_H * 0.775)
    ly2  = BODY_TOP + int(BODY_H * 0.905)
    MIDX = FX + FW // 2 + int(W * 0.04)
    lline_end = MIDX - int(W * 0.055)

    draw.line([(FX, ly1+int(H*0.022)), (lline_end, ly1+int(H*0.022))],
              fill=LC, width=2)
    draw.line([(FX, ly2+int(H*0.022)), (lline_end, ly2+int(H*0.022))],
              fill=LC, width=2)

    b46f   = _font(int(H * 0.055))
    b46lw  = _tw(draw, "Batch 4 :", b46f)
    b46lx0 = MIDX + b46lw + int(W * 0.008)
    draw.text((MIDX, ly1), "Batch 4 :", fill=DARK, font=b46f, anchor="lm")
    draw.line([(b46lx0, ly1+int(H*0.022)), (FX+FW, ly1+int(H*0.022))],
              fill=LC, width=2)
    draw.text((MIDX, ly2), "Batch 6 :", fill=DARK, font=b46f, anchor="lm")
    draw.line([(b46lx0, ly2+int(H*0.022)), (FX+FW, ly2+int(H*0.022))],
              fill=LC, width=2)

    # 6 ── QR code bottom-left
    QR_SZ = int(H * 0.165)
    try:
        qr_img = _make_qr(
            f"Name:{req.get_display_name()}|Roll:{req.get_display_roll()}"
            f"|Course:{req.get_display_course()}|NIT Hyderabad",
            QR_SZ)
        qr_y = FTR_Y - QR_SZ - int(H * 0.006)
        if qr_y >= PB - QR_SZ // 3:
            img.paste(qr_img, (PL, qr_y))
    except Exception:
        pass

    # 7 ── Outer border
    draw.rectangle([(0, 0), (W-1, H-1)], outline=RED, width=5)

    # 8 ── Save
    roll_safe = str(req.get_display_roll()).replace('/', '_').replace(' ', '_')
    fname     = f"idcard_{roll_safe}_{req.pk}.png"
    save_dir  = os.path.join(settings.MEDIA_ROOT, 'generated_cards')
    os.makedirs(save_dir, exist_ok=True)
    img.save(os.path.join(save_dir, fname), 'PNG', dpi=(DPI, DPI))
    return os.path.join('generated_cards', fname)


def generate_id_card_pdf(req, png_relative_path):
    cw = CARD_W_MM * 72 / 25.4
    ch = CARD_H_MM * 72 / 25.4
    roll_safe = str(req.get_display_roll()).replace('/', '_').replace(' ', '_')
    fname     = f"idcard_{roll_safe}_{req.pk}.pdf"
    save_dir  = os.path.join(settings.MEDIA_ROOT, 'generated_cards')
    os.makedirs(save_dir, exist_ok=True)
    c = rl_canvas.Canvas(os.path.join(save_dir, fname), pagesize=(cw, ch))
    png_full = os.path.join(settings.MEDIA_ROOT, png_relative_path)
    if os.path.exists(png_full):
        c.drawImage(ImageReader(png_full), 0, 0, width=cw, height=ch)
    c.save()
    return os.path.join('generated_cards', fname)
