#!/usr/bin/env python3
"""THE DAILY SIGNAL - front page for Monday, 23 November 2026.

Pure Python 3 standard library. Draws a 1024x1024 newspaper front page
and writes it as a PNG (own encoder, own 5x7 bitmap font).

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
Output: $MAKEFUN_OUTPUT_DIR/entry.png (deterministic, <= 1 MiB)
"""

import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (247, 243, 232)   # off-white newsprint
INK = (17, 17, 17)        # near-black
RED = (178, 34, 34)       # accent red for kickers
BLUE = (28, 68, 120)      # deep blue for charts / sea
GREY = (110, 105, 95)     # muted grey
LIGHT = (226, 220, 205)   # light rule / panel fill

# ---------------------------------------------------------------- font 5x7
# Each glyph: 7 rows, 5 bits each (bit 4 = leftmost column).
FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    'a': (0x00, 0x0E, 0x01, 0x0F, 0x11, 0x11, 0x0F),
    'b': (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    'c': (0x00, 0x0E, 0x11, 0x10, 0x10, 0x11, 0x0E),
    'd': (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    'e': (0x00, 0x0E, 0x11, 0x1F, 0x10, 0x11, 0x0E),
    'f': (0x06, 0x08, 0x08, 0x1E, 0x08, 0x08, 0x08),
    'g': (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'h': (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    'i': (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    'j': (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    'k': (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    'l': (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'm': (0x00, 0x1A, 0x15, 0x15, 0x15, 0x15, 0x15),
    'n': (0x00, 0x1E, 0x11, 0x11, 0x11, 0x11, 0x11),
    'o': (0x00, 0x0E, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'p': (0x00, 0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10),
    'q': (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x01),
    'r': (0x00, 0x16, 0x19, 0x10, 0x10, 0x10, 0x10),
    's': (0x00, 0x0F, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    't': (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    'u': (0x00, 0x11, 0x11, 0x11, 0x11, 0x13, 0x0D),
    'v': (0x00, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'w': (0x00, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    'x': (0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'y': (0x00, 0x11, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'z': (0x00, 0x1F, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ',': (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ';': (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    '-': (0, 0, 0, 0x0E, 0, 0, 0),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '+': (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    '=': (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '*': (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    '_': (0, 0, 0, 0, 0, 0, 0x1F),
    ':': (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    '[': (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
    ']': (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
    '<': (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    '>': (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    '|': (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
}

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[i * 3:i * 3 + 3] = bytes(bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x0, x1, y, c, t=1):
        for yy in range(y, y + t):
            for xx in range(x0, x1 + 1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        for xx in range(x, x + t):
            for yy in range(y0, y1 + 1):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=False):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, c)
                else:
                    if abs(d2 - r * r) <= r:
                        self.set(xx, yy, c)

    def disc(self, cx, cy, r, c):
        self.circle(cx, cy, r, c, fill=True)


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, s, x, y, scale, c=INK):
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT['?'])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row & (1 << (4 - col)):
                    cv.rect(cx + col * scale, y + r * scale, scale, scale, c)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, s, cx, y, scale, c=INK):
    draw_text(cv, s, cx - text_w(s, scale) // 2, y, scale, c)


def wrap(s, max_w, scale):
    """Greedy word wrap; returns list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(cv, s, x, y, max_w, scale, c=INK, lh=None):
    """Draw wrapped paragraph; returns y after last line."""
    lh = lh or (9 * scale + 3)
    for ln in wrap(s, max_w, scale):
        draw_text(cv, ln, x, y, scale, c)
        y += lh
    return y


def para_indent(cv, s, first_x, rest_x, y, first_w, rest_w, scale, c=INK, lh=None):
    """Wrapped paragraph whose first line is indented (starts at first_x,
    max width first_w) and continuation lines start at rest_x (max rest_w).
    Returns y after last line."""
    lh = lh or (9 * scale + 3)
    lines, cur, limit = [], "", first_w
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= limit or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
            limit = rest_w
    if cur:
        lines.append(cur)
    for i, ln in enumerate(lines):
        draw_text(cv, ln, first_x if i == 0 else rest_x, y, scale, c)
        y += lh
    return y


def headline(cv, s, x, y, max_w, scale, c=INK, lh=None):
    lh = lh or (9 * scale + 2)
    for ln in wrap(s, max_w, scale):
        draw_text(cv, ln, x, y, scale, c)
        y += lh
    return y


# ---------------------------------------------------------------- PNG encoder
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- page
def build():
    cv = Canvas(W, H, PAPER)
    # outer frame
    cv.rect(0, 0, W, 4, INK)
    cv.rect(0, H - 4, W, 4, INK)
    cv.rect(0, 0, 4, H, INK)
    cv.rect(W - 4, 0, 4, H, INK)

    # ---- masthead ----
    draw_text_centered(cv, "THE DAILY SIGNAL", W // 2, 26, 7)
    cv.hline(24, W - 24, 96, INK, 2)
    draw_text(cv, "EST. 2026", 24, 108, 2, GREY)
    draw_text_centered(cv, "Monday, 23 November 2026", W // 2, 108, 2)
    draw_text(cv, "WORLD EDITION", W - 24 - text_w("WORLD EDITION", 2), 108, 2, GREY)
    cv.hline(24, W - 24, 130, INK, 4)
    cv.hline(24, W - 24, 138, INK, 1)

    # ---- lead story: COP31 ----
    LX, LW = 24, 560
    y = 156
    draw_text(cv, "CLIMATE  |  COP31", LX, y, 2, RED)
    y += 26
    y = headline(cv, "COP31 COLLAPSES", LX, y, LW, 4, lh=38)
    y = headline(cv, "WITHOUT A DEAL", LX, y, LW, 4, lh=38)
    y += 6
    y = para(cv, "Climate talks at COP31 in Antalya, Turkiye, collapsed on "
                "Sunday after two weeks plus two days of overtime - the "
                "longest COP in history.", LX, y, LW, 2, lh=19)
    y += 4
    y = para(cv, "Negotiators failed to agree a final text after the words "
                "'fossil fuels' were stripped from the draft.", LX, y, LW, 2, lh=19)
    y += 4
    y = para(cv, "UN chief Antonio Guterres said he was 'deeply "
                "disappointed'. The EU, Panama, the Marshall Islands and "
                "Norway rejected the draft.", LX, y, LW, 2, lh=19)
    y += 4
    y = para(cv, "Attention now turns to COP32 in Addis Ababa, Ethiopia.",
             LX, y, LW, 2, lh=19)

    # ---- procedural illustration: cracked earth + globe + sun ----
    ix0, iy0, iw, ih = LX, 490, LW, 110
    cv.rect(ix0, iy0, iw, ih, LIGHT)
    cv.rect(ix0, iy0, iw, 2, INK)
    cv.rect(ix0, iy0 + ih - 2, iw, 2, INK)
    # sun
    cv.disc(ix0 + 52, iy0 + 34, 22, (214, 140, 40))
    for k in range(8):
        import math
        a = k * math.pi / 4
        cv.line(ix0 + 52 + int(27 * math.cos(a)), iy0 + 34 + int(27 * math.sin(a)),
                ix0 + 52 + int(36 * math.cos(a)), iy0 + 34 + int(36 * math.sin(a)),
                (214, 140, 40))
    # globe
    gx, gy, gr = ix0 + 230, iy0 + 56, 40
    cv.disc(gx, gy, gr, (120, 170, 205))
    cv.disc(gx - 14, gy - 9, 11, (90, 150, 90))
    cv.disc(gx + 12, gy + 12, 12, (90, 150, 90))
    cv.disc(gx + 6, gy - 20, 8, (90, 150, 90))
    cv.circle(gx, gy, gr, INK)
    cv.circle(gx, gy, gr + 2, INK)
    # cracked ground (between globe and thermometer)
    cv.line(ix0 + 330, iy0 + ih - 2, ix0 + 352, iy0 + 82, INK)
    cv.line(ix0 + 352, iy0 + 82, ix0 + 332, iy0 + 96, INK)
    cv.line(ix0 + 352, iy0 + 82, ix0 + 378, iy0 + 98, INK)
    cv.line(ix0 + 378, iy0 + 98, ix0 + 396, iy0 + 84, INK)
    # thermometer
    tx, ty = ix0 + 440, iy0 + 22
    cv.rect(tx, ty, 10, 34, INK)
    cv.disc(tx + 5, ty + 38, 11, RED)
    cv.rect(tx + 2, ty + 14, 6, 22, RED)
    draw_text(cv, "TALKS: 2 WEEKS + 2 DAYS", ix0 + 12, iy0 + ih - 20, 2, INK)
    draw_text(cv, "NO DEAL", ix0 + iw - 12 - text_w("NO DEAL", 2), iy0 + ih - 20, 2, RED)

    # ---- right column: Gulf escalation ----
    RX, RW = 600, 400
    cv.vline(588, 156, 600, INK, 1)
    y = 156
    draw_text(cv, "MIDDLE EAST  |  GULF", RX, y, 2, RED)
    y += 26
    y = headline(cv, "GULF ON EDGE AS", RX, y, RW, 3, lh=29)
    y = headline(cv, "STRIKES SPREAD", RX, y, RW, 3, lh=29)
    y += 6
    y = para(cv, "Houthi forces struck Riyadh for a third straight day on "
                "Sunday.", RX, y, RW, 2, lh=18)
    y += 4
    y = para(cv, "Iran's IRGC claimed it destroyed two Patriot radars at a "
                "US base in Bahrain; Bahrain demanded UN action.", RX, y, RW, 2, lh=18)
    y += 4
    y = para(cv, "A Saudi-led coalition intercepted a Houthi missile in "
                "western Saudi Arabia.", RX, y, RW, 2, lh=18)
    y += 4
    y = para(cv, "At least 25 tankers were hit near the Strait of Hormuz in "
                "seven days; Gulf oil flows fell sharply.", RX, y, RW, 2, lh=18)

    # schematic map: Gulf of Oman / Strait of Hormuz
    mx0, my0, mw, mh = RX, 498, RW, 102
    cv.rect(mx0, my0, mw, mh, (214, 228, 240))
    cv.rect(mx0, my0, mw, 2, INK)
    cv.rect(mx0, my0 + mh - 2, mw, 2, INK)
    # land masses
    cv.rect(mx0, my0 + 4, 130, 40, (226, 214, 170))
    cv.rect(mx0 + mw - 130, my0 + 4, 130, 36, (226, 214, 170))
    draw_text(cv, "IRAN", mx0 + 18, my0 + 16, 2, INK)
    draw_text(cv, "OMAN", mx0 + mw - 72, my0 + 14, 2, INK)
    # strait marker
    cv.line(mx0 + 130, my0 + 40, mx0 + 210, my0 + 54, RED)
    draw_text(cv, "STRAIT OF HORMUZ", mx0 + 110, my0 + 58, 2, RED)
    # tanker dots (attacked)
    for (dx, dy) in [(40, 78), (100, 78), (160, 78), (220, 78),
                     (280, 78), (340, 78)]:
        cv.disc(mx0 + dx, my0 + dy, 4, RED)
    draw_text(cv, "UKMTO: INCIDENT IN GULF OF OMAN", mx0 + 10, my0 + 86, 2, INK)

    # ---- middle band: three secondary stories ----
    cv.hline(24, W - 24, 610, INK, 2)
    cols = [
        ("US POLITICS", "DEMOCRATS TAKE THE HOUSE",
         "Democrats won the US House: at least 258 seats, their largest "
         "since 1992."),
        ("SPACE  |  EUROPE-JAPAN", "BEPICOLOMBO REACHES MERCURY",
         "BepiColombo reached Mercury orbit after an eight-year journey."),
        ("TRAVEL", "DELTA DELAYS HIT THANKSGIVING",
         "About 1,000 Delta flights delayed Sunday - 67% of schedule."),
    ]
    cw = 312
    for i, (kick, head, body) in enumerate(cols):
        cx = 24 + i * (cw + 16)
        if i:
            cv.vline(cx - 8, 622, 757, GREY, 1)
        draw_text(cv, kick, cx, 622, 2, RED)
        y = headline(cv, head, cx, 644, cw, 3, lh=29)
        para(cv, body, cx, 706, cw, 2, lh=16)

    # ---- World in Brief grid ----
    cv.hline(24, W - 24, 760, INK, 4)
    draw_text_centered(cv, "WORLD IN BRIEF", W // 2, 768, 3)
    cv.hline(24, W - 24, 794, INK, 1)
    briefs = [
        ("GAZA", "Israeli strikes killed 9 people in 48 hours; the toll "
         "since the October 2025 ceasefire reached 1,661."),
        ("UKRAINE", "Russian drone hit a building in Kyiv region; 14 "
         "missing. BBC: blast before part of Crimea Bridge fell."),
        ("UAP", "Pentagon: 43 more UAP files, incl. three Mideast videos, "
         "all unexplained."),
        ("INDONESIA", "A candy-factory fire: 7 bodies found, 50 workers "
         "missing."),
        ("NEPAL", "PM Balendra Shah visits India, meets PM Modi on "
         "23 November."),
        ("SOUTH KOREA", "Education minister resigned amid AI-cheating "
         "scandal."),
        ("NIGERIA", "A boat sank, killing at least 24 people."),
        ("SOUTH SUDAN", "An SPLA-IO attack killed 24 civilians."),
    ]
    bw = 480
    row_h = [56, 40, 40, 40]
    row_y = [800, 856, 896, 936]
    for i, (tag, txt) in enumerate(briefs):
        bx = 24 + (i % 2) * (bw + 8)
        by = row_y[i // 2]
        draw_text(cv, tag, bx, by, 2, RED)
        tw = text_w(tag + "  ", 2)
        para_indent(cv, txt, bx + tw, bx, by, bw - tw, bw, 2, lh=17)

    # ---- footer strip ----
    cv.hline(24, W - 24, 982, INK, 2)
    draw_text(cv, "SPORT: Liverpool thrashed 10-man Man Utd; India set a "
                "Test record 720/9d vs NZ.", 24, 988, 2, INK)
    draw_text(cv, "WHO: fighting near the Ebola outbreak in Congo is "
                "hampering the response.", 24, 1002, 2, GREY)

    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output/entry.png")
    if out_dir.endswith(".png"):
        path = out_dir
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    else:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "entry.png")
    cv = build()
    n = write_png(cv, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, n, W, H))


if __name__ == "__main__":
    main()
