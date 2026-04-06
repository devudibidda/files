"""
=============================================================
  Employee Card Generator  -- Birthday & Work Anniversary
  Stack  : Python + Pillow (PIL) + Google Fonts (auto-download)
  Output : 1080x1080 px PNG cards
=============================================================
"""

import math, random, csv, urllib.request
from datetime import date, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
FONT_DIR   = BASE_DIR / "fonts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FONT_DIR.mkdir(parents=True, exist_ok=True)

W = H = 1080

# ─── Google Fonts (auto-download from GitHub mirror) ──────────────────────────
GOOGLE_FONT_URLS = {
    "Poppins-Bold":
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-SemiBold":
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
    "Poppins-Medium":
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf",
    "Poppins-Regular":
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "Poppins-Light":
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Light.ttf",
    "Poppins-LightItalic":
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-LightItalic.ttf",
    "GreatVibes-Regular":
        "https://github.com/google/fonts/raw/main/ofl/greatvibes/GreatVibes-Regular.ttf",
}


def _download_font(name: str) -> Path:
    dest = FONT_DIR / f"{name}.ttf"
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    url = GOOGLE_FONT_URLS.get(name)
    if not url:
        raise FileNotFoundError(f"No URL for font '{name}'")
    print(f"  Downloading font {name}...")
    urllib.request.urlretrieve(url, str(dest))
    return dest


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(_download_font(name)), size)
    except Exception:
        return ImageFont.load_default()


# ─── Font shortcuts ───────────────────────────────────────────────────────────
def poppins_bold(s):        return load_font("Poppins-Bold", s)
def poppins_semibold(s):    return load_font("Poppins-SemiBold", s)
def poppins_medium(s):      return load_font("Poppins-Medium", s)
def poppins_regular(s):     return load_font("Poppins-Regular", s)
def poppins_light(s):       return load_font("Poppins-Light", s)
def poppins_light_italic(s):return load_font("Poppins-LightItalic", s)
def greatvibes(s):          return load_font("GreatVibes-Regular", s)


# ─── Quotes ───────────────────────────────────────────────────────────────────
BIRTHDAY_QUOTES = [
    "May this birthday mark the beginning of a wonderful new chapter full of joy, growth, and achievement.",
    "Wishing you a day as bright and impactful as your contributions to our team. Happy Birthday!",
    "Another year wiser, more accomplished, and absolutely irreplaceable. Celebrate big today!",
    "Your energy and passion inspire everyone around you. Here's to another amazing year ahead!",
    "Today is all about you \u2014 your talent, your heart, and the incredible difference you make daily.",
    "Celebrating you today and always! May this year bring you every success you deserve.",
]

ANNIVERSARY_QUOTES = [
    "Your dedication and passion continue to raise the bar for everyone around you. Thank you!",
    "Every milestone you reach reflects the commitment and excellence you bring each day.",
    "Your contributions make a real impact, and your dedication is truly inspiring.",
    "Thank you for your unwavering commitment. Here's to many more milestones together!",
    "Years of dedication, countless contributions, and immeasurable impact. We're proud to have you.",
    "Your journey with us has been nothing short of remarkable. Here's to the road ahead!",
]


# ─── Utility ──────────────────────────────────────────────────────────────────
def ordinal(n: int) -> str:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(
        n % 10 if n % 100 not in (11, 12, 13) else 0, "th"
    )
    return f"{n}{suffix}"


def years_since(date_str: str) -> int:
    d = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    today = date.today()
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))


# ─── Drawing Helpers ──────────────────────────────────────────────────────────
def text_size(draw, text, font_obj):
    """Return (width, height) of rendered text."""
    bb = draw.textbbox((0, 0), text, font=font_obj)
    return bb[2] - bb[0], bb[3] - bb[1]


def draw_centered(draw, text, y, font_obj, color, cw=W):
    """Draw horizontally centered text. Returns height."""
    tw, th = text_size(draw, text, font_obj)
    draw.text(((cw - tw) // 2, y), text, font=font_obj, fill=color)
    return th


def draw_centered_shadow(draw, text, y, font_obj, color, shadow, off=(2, 3), cw=W):
    tw, th = text_size(draw, text, font_obj)
    x = (cw - tw) // 2
    draw.text((x + off[0], y + off[1]), text, font=font_obj, fill=shadow)
    draw.text((x, y), text, font=font_obj, fill=color)
    return th


def wrap_text(draw, text, font_obj, max_w):
    words = text.split()
    lines, buf = [], []
    for w in words:
        test = " ".join(buf + [w])
        tw, _ = text_size(draw, test, font_obj)
        if tw > max_w and buf:
            lines.append(" ".join(buf))
            buf = [w]
        else:
            buf.append(w)
    if buf:
        lines.append(" ".join(buf))
    return lines or [text]


def draw_wrapped_centered(draw, text, y, font_obj, color, max_w, gap=8, cw=W):
    """Word-wrapped centered text. Returns total height consumed."""
    lines = wrap_text(draw, text, font_obj, max_w)
    cy = y
    for ln in lines:
        tw, th = text_size(draw, ln, font_obj)
        draw.text(((cw - tw) // 2, cy), ln, font=font_obj, fill=color)
        cy += th + gap
    return cy - y


def gradient_fill(draw, y0, y1, c_top, c_bot):
    span = max(y1 - y0, 1)
    for i in range(span):
        t = i / span
        r = int(c_top[0] + (c_bot[0] - c_top[0]) * t)
        g = int(c_top[1] + (c_bot[1] - c_top[1]) * t)
        b = int(c_top[2] + (c_bot[2] - c_top[2]) * t)
        draw.line([(0, y0 + i), (W, y0 + i)], fill=(r, g, b))


# ─── Photo Helpers ────────────────────────────────────────────────────────────
def _placeholder(size, bg=(100, 130, 170), fg=(170, 200, 230)):
    img = Image.new("RGBA", (size, size), (*bg, 255))
    d = ImageDraw.Draw(img)
    cx, hr = size // 2, size // 6
    head_y = int(size * 0.35)
    d.ellipse([cx - hr, head_y - hr, cx + hr, head_y + hr], fill=(*fg, 255))
    bw = int(size * 0.32)
    by = head_y + hr + 6
    d.ellipse([cx - bw, by, cx + bw, by + int(size * 0.48)], fill=(*fg, 255))
    return img


def paste_photo_circle(canvas, photo_path, cx, cy, radius, border_color, border_w=6):
    diameter = radius * 2
    try:
        photo = Image.open(photo_path).convert("RGBA")
        if photo.size[0] == 0:
            raise ValueError
    except Exception:
        photo = _placeholder(diameter)

    pw, ph = photo.size
    side = min(pw, ph)
    l, t = (pw - side) // 2, (ph - side) // 2
    photo = photo.crop((l, t, l + side, t + side)).resize(
        (diameter, diameter), Image.LANCZOS
    )
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter, diameter), fill=255)
    circ = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    circ.paste(photo, (0, 0), mask)

    draw = ImageDraw.Draw(canvas)
    draw.ellipse(
        [cx - radius - border_w, cy - radius - border_w,
         cx + radius + border_w, cy + radius + border_w],
        outline=border_color, width=border_w,
    )
    canvas.paste(circ, (cx - radius, cy - radius), circ)


# ─── Logo ─────────────────────────────────────────────────────────────────────
def paste_logo(canvas, x, y, height):
    """Paste logo.png scaled to height. No fallback."""
    p = BASE_DIR / "logo.png"
    if not p.exists():
        print(f"  Warning: logo.png not found at {p}")
        return 0
    logo = Image.open(str(p)).convert("RGBA")
    lw, lh = logo.size
    new_w = int(lw * height / lh)
    logo = logo.resize((new_w, height), Image.LANCZOS)
    canvas.paste(logo, (x, y), logo)
    return new_w


# ══════════════════════════════════════════════════════════════════════════════
#  ANNIVERSARY CARD  -- Clean centered vertical layout
# ══════════════════════════════════════════════════════════════════════════════
def generate_anniversary_card(employee_name, years, photo_path=None, company="Vestas"):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)

    # Palette
    NAVY      = (15, 30, 60)
    NAVY_LITE = (25, 50, 100)
    GOLD      = (212, 175, 89)
    GOLD_LT   = (240, 215, 145)
    WHITE     = (255, 255, 255)
    SLATE     = (190, 205, 228)

    # Background gradient
    gradient_fill(draw, 0, H, NAVY, NAVY_LITE)

    # Double border frame
    PAD = 32
    draw.rounded_rectangle([PAD, PAD, W - PAD, H - PAD],
                           radius=10, outline=(*GOLD, 120), width=2)
    draw.rounded_rectangle([PAD + 5, PAD + 5, W - PAD - 5, H - PAD - 5],
                           radius=8, outline=(*GOLD, 50), width=1)

    # Corner accents
    for cx2, cy2 in [(PAD, PAD), (W - PAD, PAD),
                     (PAD, H - PAD), (W - PAD, H - PAD)]:
        draw.ellipse([cx2 - 5, cy2 - 5, cx2 + 5, cy2 + 5], fill=GOLD)

    # ──────────── FOOTER (fixed at bottom) ────────────
    FOOTER_H = 80
    footer_y = H - FOOTER_H
    draw.rectangle([0, footer_y, W, H], fill=(0, 0, 0, 50))
    draw.line([(0, footer_y), (W, footer_y)], fill=(*GOLD, 120), width=1)
    logo_h = 50
    paste_logo(canvas, 40, footer_y + (FOOTER_H - logo_h) // 2, logo_h)
    f_co = poppins_semibold(18)
    f_tl = poppins_light(14)
    draw.text((W - 240, footer_y + 18), company, font=f_co, fill=(*GOLD, 220))
    draw.text((W - 240, footer_y + 44), "Inspire to Improve",
              font=f_tl, fill=(*SLATE, 180))

    # ──────────── PRE-MEASURE all content to center vertically ────────────
    # Fonts (pre-load once)
    f_badge  = poppins_bold(21)
    f_name   = poppins_bold(42)
    f_celeb  = poppins_light(24)
    f_num    = poppins_bold(120)
    f_suf    = poppins_bold(50)
    f_label  = poppins_light(26)
    f_quote  = poppins_light_italic(20)

    # Measure heights
    badge_h     = 48
    photo_r     = 130
    photo_block = photo_r * 2 + 10  # diameter + border
    name_lines  = wrap_text(draw, employee_name, f_name, W - 160)
    _, single_h = text_size(draw, "A", f_name)
    name_h      = len(name_lines) * (single_h + 6)
    divider_h   = 16
    _, celeb_h  = text_size(draw, "Celebrating", f_celeb)
    num_str     = str(years)
    suf_str     = ordinal(years)[len(num_str):]
    # Use textbbox y1 (full bottom from draw pos), not tight height
    num_bb      = draw.textbbox((0, 0), num_str, font=f_num)
    suf_bb      = draw.textbbox((0, 0), suf_str, font=f_suf)
    num_bottom  = num_bb[3]           # visual bottom of number from y
    suf_bottom  = 14 + suf_bb[3]     # suffix drawn at y+14, so its bottom
    ordinal_h   = max(num_bottom, suf_bottom)
    _, label_h  = text_size(draw, "Y E A R S", f_label)
    quote       = random.choice(ANNIVERSARY_QUOTES)
    q_text      = f"\u201c{quote}\u201d"
    q_lines     = wrap_text(draw, q_text, f_quote, W - 180)
    _, ql_h     = text_size(draw, "A", f_quote)
    quote_h     = len(q_lines) * (ql_h + 6)

    # Gaps between sections
    G = [34, 28, 16, 24, 10, 16, 30]  # 7 gaps between 8 elements
    total_content = (badge_h + photo_block + name_h + divider_h +
                     celeb_h + ordinal_h + label_h + quote_h + sum(G))

    # Usable area: from top pad to footer
    TOP_PAD = 55
    usable = footer_y - TOP_PAD
    start_y = TOP_PAD + max(0, (usable - total_content) // 2)

    y = start_y

    # ── 1. "WORK ANNIVERSARY" gold pill badge
    badge_w = 420
    bx = (W - badge_w) // 2
    draw.rounded_rectangle([bx, y, bx + badge_w, y + badge_h],
                           radius=badge_h // 2, fill=GOLD)
    draw_centered(draw, "WORK ANNIVERSARY", y + 12, f_badge, NAVY)
    y += badge_h + G[0]

    # ── 2. Employee photo
    photo_cx = W // 2
    photo_cy = y + photo_r
    for h in range(20, 0, -4):
        draw.ellipse(
            [photo_cx - photo_r - h, photo_cy - photo_r - h,
             photo_cx + photo_r + h, photo_cy + photo_r + h],
            outline=(*GOLD, max(8, h * 3)), width=1,
        )
    paste_photo_circle(canvas, photo_path, photo_cx, photo_cy,
                       photo_r, GOLD, border_w=5)
    y = photo_cy + photo_r + G[1]

    # ── 3. Employee name
    for ln in name_lines:
        tw, th = text_size(draw, ln, f_name)
        draw.text(((W - tw) // 2, y), ln, font=f_name, fill=WHITE)
        y += th + 6
    y += G[2]

    # ── 4. Gold divider with diamond
    line_inset = 140
    draw.line([(line_inset, y), (W // 2 - 14, y)], fill=(*GOLD, 160), width=1)
    draw.line([(W // 2 + 14, y), (W - line_inset, y)], fill=(*GOLD, 160), width=1)
    d = 7
    draw.polygon([(W//2, y-d), (W//2+d, y), (W//2, y+d), (W//2-d, y)], fill=GOLD)
    y += divider_h + G[3]

    # ── 5. "Celebrating"
    draw_centered(draw, "Celebrating", y, f_celeb, SLATE)
    y += celeb_h + G[4]

    # ── 6. Big ordinal number (e.g. "2nd") — suffix as superscript
    nw = num_bb[2] - num_bb[0]
    sw = suf_bb[2] - suf_bb[0]
    total_w = nw + sw + 6
    sx = (W - total_w) // 2

    # Draw shadow then number
    draw.text((sx + 2, y + 2), num_str, font=f_num, fill=(*GOLD, 40))
    draw.text((sx, y), num_str, font=f_num, fill=GOLD_LT)
    # Suffix positioned as superscript (offset 14px from top)
    draw.text((sx + nw + 6, y + 14), suf_str, font=f_suf, fill=GOLD)
    y += ordinal_h + G[5]

    # ── 7. "Y E A R S"
    yr_label = "Y E A R" if years == 1 else "Y E A R S"
    draw_centered(draw, yr_label, y, f_label, SLATE)
    y += label_h + G[6]

    # ── 8. Quote
    for ln in q_lines:
        tw, th = text_size(draw, ln, f_quote)
        draw.text(((W - tw) // 2, y), ln, font=f_quote, fill=(*SLATE, 200))
        y += th + 6

    # Save
    safe = employee_name.replace(" ", "_")
    out = OUTPUT_DIR / f"anniversary_{safe}_{years}yr.png"
    canvas.convert("RGB").save(str(out), "PNG", quality=98)
    print(f"  Done: Anniversary card -> {out}")
    return str(out)


# ══════════════════════════════════════════════════════════════════════════════
#  BIRTHDAY CARD  -- Vibrant sky-blue with confetti & balloons
# ══════════════════════════════════════════════════════════════════════════════
def generate_birthday_card(employee_name, photo_path=None):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)

    # Palette
    SKY_TOP = (30, 140, 200)
    SKY_BOT = (100, 200, 240)
    WHITE   = (255, 255, 255)
    NAVY    = (18, 50, 90)
    CREAM   = (255, 252, 240)
    CORAL   = (255, 120, 100)
    MINT    = (120, 220, 170)
    LEMON   = (255, 225, 70)
    LILAC   = (190, 160, 255)

    # Background gradient
    gradient_fill(draw, 0, H, SKY_TOP, SKY_BOT)

    # Confetti (background layer)
    random.seed(hash(employee_name) % 10000)
    conf_colors = [
        (*CORAL, 110), (*LEMON, 110), (*MINT, 110), (*WHITE, 70),
        (255, 180, 210, 90), (*LILAC, 90),
    ]
    for _ in range(100):
        cx2 = random.randint(0, W)
        cy2 = random.randint(0, H)
        sz = random.randint(4, 14)
        col = random.choice(conf_colors)
        shape = random.choice(["r", "c", "t"])
        if shape == "r":
            draw.rectangle([cx2, cy2, cx2 + sz, cy2 + sz // 2], fill=col)
        elif shape == "c":
            draw.ellipse([cx2, cy2, cx2 + sz, cy2 + sz], fill=col)
        else:
            draw.polygon([(cx2, cy2 - sz), (cx2 + sz, cy2 + sz),
                          (cx2 - sz, cy2 + sz)], fill=col)

    # Corner balloons
    def _balloon(d, bx, by, color, sd=1):
        bw, bh = 40, 52
        d.ellipse([bx, by, bx + bw, by + bh],
                  fill=(*color, 130), outline=(*color, 190), width=2)
        d.ellipse([bx + 8, by + 8, bx + 18, by + 20],
                  fill=(255, 255, 255, 45))
        d.ellipse([bx + bw//2 - 3, by + bh, bx + bw//2 + 3, by + bh + 5],
                  fill=(*color, 170))
        for seg in range(4):
            sx = bx + bw//2 + sd * int(5 * math.sin(seg * 0.9))
            sy = by + bh + 5 + seg * 11
            d.line([(sx, sy), (sx + sd * 3, sy + 10)],
                   fill=(*color, 90), width=1)

    _balloon(draw, 25, 25, CORAL[:3], 1)
    _balloon(draw, W - 80, 20, LEMON[:3], -1)
    _balloon(draw, 15, H - 160, MINT[:3], 1)
    _balloon(draw, W - 70, H - 150, LILAC[:3], -1)

    # ──────────── FOOTER (fixed) ────────────
    FOOTER_H = 60
    footer_y = H - FOOTER_H
    draw.rectangle([0, footer_y, W, H], fill=(0, 0, 0, 30))
    draw.line([(0, footer_y), (W, footer_y)], fill=(*WHITE, 40), width=1)
    f_ft = poppins_light(17)
    draw_centered(draw, "Celebrate  \u2022  Smile  \u2022  Shine",
                  footer_y + 18, f_ft, (*WHITE, 170))

    # ──────────── PRE-MEASURE for vertical centering ────────────
    f_happy = poppins_bold(56)
    f_bday  = greatvibes(96)
    f_name  = poppins_bold(40)
    f_quote = poppins_regular(22)

    _, happy_h = text_size(draw, "H A P P Y", f_happy)
    _, bday_h  = text_size(draw, "Birthday!", f_bday)
    photo_r    = 145
    photo_block = photo_r * 2 + 14
    ntw, nth   = text_size(draw, employee_name, f_name)
    pill_h     = nth + 28
    quote      = random.choice(BIRTHDAY_QUOTES)
    q_text     = f"\u201c{quote}\u201d"
    q_lines    = wrap_text(draw, q_text, f_quote, W - 140)
    _, ql_h    = text_size(draw, "A", f_quote)
    quote_h    = len(q_lines) * (ql_h + 6)

    G = [6, 26, 24, 22, 22]  # gaps between 6 elements
    total = happy_h + bday_h + photo_block + pill_h + quote_h + sum(G)

    TOP_PAD = 60
    usable = footer_y - TOP_PAD
    start_y = TOP_PAD + max(0, (usable - total) // 2)

    y = start_y

    # ── 1. "H A P P Y"
    th = draw_centered_shadow(draw, "H A P P Y", y, f_happy,
                              WHITE, (0, 0, 0, 45))
    y += th + G[0]

    # ── 2. "Birthday!" in script font
    th = draw_centered_shadow(draw, "Birthday!", y, f_bday,
                              CREAM, (0, 0, 0, 45), off=(3, 4))
    y += th + G[1]

    # ── 3. Photo circle
    photo_cx = W // 2
    photo_cy = y + photo_r

    for ang in range(0, 360, 15):
        rad = math.radians(ang)
        dx = int(photo_cx + (photo_r + 16) * math.cos(rad))
        dy = int(photo_cy + (photo_r + 16) * math.sin(rad))
        dot_col = conf_colors[(ang // 15) % len(conf_colors)]
        draw.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=dot_col)

    paste_photo_circle(canvas, photo_path, photo_cx, photo_cy,
                       photo_r, WHITE, border_w=7)
    y = photo_cy + photo_r + G[2]

    # ── 4. Name pill
    px, py = 36, 12
    tw2 = ntw + px * 2
    th2 = pill_h
    tx = (W - tw2) // 2

    draw.rounded_rectangle([tx, y, tx + tw2, y + th2],
                           radius=th2 // 2, fill=(*WHITE, 225))
    draw.text((tx + px, y + py + 2), employee_name, font=f_name, fill=NAVY)
    y += th2 + G[3]

    # ── 5. Quote
    for ln in q_lines:
        tw, th = text_size(draw, ln, f_quote)
        draw.text(((W - tw) // 2, y), ln, font=f_quote, fill=(*WHITE, 215))
        y += th + 6

    # Save
    safe = employee_name.replace(" ", "_")
    out = OUTPUT_DIR / f"birthday_{safe}.png"
    canvas.convert("RGB").save(str(out), "PNG", quality=98)
    print(f"  Done: Birthday card -> {out}")
    return str(out)


# ══════════════════════════════════════════════════════════════════════════════
#  CSV BATCH PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
def process_csv(csv_path: str, mode="both"):
    """
    CSV columns: employeeName, username, dob, doj, photo_path
    mode: 'birthday' | 'anniversary' | 'both' | 'auto'
    """
    today = date.today()
    generated = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from header names for resilience
            row = {k.strip(): v for k, v in row.items()}
            name    = row["employeeName"].strip()
            dob_str = row.get("dob", "").strip()
            doj_str = row.get("doj", "").strip()
            photo   = row.get("photo_path", "").strip() or None

            print(f"\nProcessing: {name}")

            if mode in ("birthday", "both", "auto") and dob_str:
                if mode != "auto" or _is_upcoming(dob_str, today):
                    path = generate_birthday_card(name, photo)
                    generated.append({"type": "birthday", "name": name,
                                      "file": path})

            if mode in ("anniversary", "both", "auto") and doj_str:
                yrs = years_since(doj_str)
                if yrs > 0 and (mode != "auto" or _is_upcoming(doj_str, today)):
                    path = generate_anniversary_card(name, yrs, photo)
                    generated.append({"type": "anniversary", "name": name,
                                      "years": yrs, "file": path})

    print(f"\nGenerated {len(generated)} card(s).")
    return generated


def _is_upcoming(date_str, today, window_days=7):
    try:
        d = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        this_year = d.replace(year=today.year)
        return abs((this_year - today).days) <= window_days
    except Exception:
        return False


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    print("\nCard Generator v2\n" + "=" * 50)

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else "both"
        process_csv(csv_file, mode)
    else:
        # Demo
        generate_anniversary_card("Rajesh Asokan", years=2)
        generate_anniversary_card("Priya Sharma", years=5)
        generate_birthday_card("Biswajit Das")
        generate_birthday_card("Ananya Krishnan")

    print(f"\nAll cards saved to: {OUTPUT_DIR}\n")
