#!/usr/bin/env python3
"""Meme Sprint: AI Agents Ship Games.

A pure-stdlib program (no third-party packages, no network, no files
outside this repository) that draws one meme image about AI agents
building games and writes it to /output/entry.png.

The meme is a three-panel comic:
  1. A user asks an AI agent to build a fun game.
  2. 0.4 seconds later the agent has shipped 12 games.
  3. The user asks if any of them are fun. Fun was not in the prompt.

Deterministic: the same bytes are produced on every run.
"""

import os
import struct
import zlib

W, H = 1024, 1024

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 214, 10)
GREY_DARK = (90, 90, 90)
GREY_MID = (154, 160, 166)
ROBOT_HEAD = (175, 198, 216)
ROBOT_BODY = (143, 163, 176)
ROBOT_EYE = (0, 180, 216)
SKIN = (255, 219, 172)
HAIR = (59, 47, 47)
SHIRT = (46, 134, 171)
SCREEN = (191, 227, 198)
GROUND = (124, 179, 66)
FOOTER_BG = (17, 17, 17)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, '#' = on, '.' = off.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    '.': (".....", ".....", ".....", ".....", ".....", "01100", "01100"),
    ',': (".....", ".....", ".....", ".....", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", ".....", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", ".....", "00100"),
    "'": ("00100", "00100", "01000", ".....", ".....", ".....", "....."),
    ':': (".....", "01100", "01100", ".....", "01100", "01100", "....."),
    ';': (".....", "01100", "01100", ".....", "01100", "00100", "01000"),
    '-': (".....", ".....", ".....", "01110", ".....", ".....", "....."),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '"': ("01010", "01010", ".....", ".....", ".....", ".....", "....."),
    '+': (".....", "00100", "00100", "11111", "00100", "00100", "....."),
    '*': (".....", "10101", "01110", "10101", ".....", ".....", "....."),
    '=': (".....", ".....", "11111", ".....", "11111", ".....", "....."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "11111"),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def text_width(s, scale):
    """Pixel width of s rendered at scale (includes inter-glyph gaps)."""
    if not s:
        return 0
    return len(s) * 6 * scale - scale


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x0, y0, x1, y1, c):
        """Filled rectangle, inclusive coords, clipped."""
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(self.w - 1, x1); y1 = min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            i = self._idx(x0, y)
            row = bytes(c) * (x1 - x0 + 1)
            self.px[i:i + len(row)] = row

    def hline(self, x0, x1, y, c, t=1):
        for dy in range(t):
            self.rect(x0, y + dy, x1, y + dy, c)

    def vline(self, x, y0, y1, c, t=1):
        for dx in range(t):
            self.rect(x + dx, y0, x + dx, y1, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        """Bresenham line with square thickness t."""
        dx = abs(x1 - x0); dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        half = t // 2
        while True:
            self.rect(x - half, y - half, x - half + t - 1, y - half + t - 1, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x += sx
            if e2 <= dx:
                err += dx; y += sy

    def circle(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            span = int((r * r - (y - cy) ** 2) ** 0.5)
            self.rect(cx - span, y, cx + span, y, c)

    def disc_outline(self, cx, cy, r, c, t=3):
        for k in range(t):
            rr = r - k
            for a in range(360):
                import math
                x = cx + int(rr * math.cos(math.radians(a)))
                y = cy + int(rr * math.sin(math.radians(a)))
                self.set(x, y, c)

    def rrect(self, x0, y0, x1, y1, r, c):
        """Filled rounded rectangle."""
        self.rect(x0 + r, y0, x1 - r, y1, c)
        self.rect(x0, y0 + r, x1, y1 - r, c)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.circle(cx, cy, r, c)

    def rrect_outline(self, x0, y0, x1, y1, r, c, t=3):
        self.hline(x0 + r, x1 - r, y0, c, t)
        self.hline(x0 + r, x1 - r, y1 - t + 1, c, t)
        self.vline(x0, y0 + r, y1 - r, c, t)
        self.vline(x1 - t + 1, y0 + r, y1 - r, c, t)

    def text(self, x, y, s, scale, c):
        """Draw uppercase text; unknown chars render as space."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[' '])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == '1':
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + col * scale + scale - 1,
                                  y + row * scale + scale - 1, c)
            cx += 6 * scale
        return cx

    def text_centered(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)


# ------------------------------------------------------------- characters
def draw_human(cv, x, y, scale=1):
    """Simple human: head + shoulders, centred on x, head top at y."""
    # head
    cv.circle(x, y + 30, 30, SKIN)
    cv.disc_outline(x, y + 30, 30, BLACK, 3)
    # hair cap
    for yy in range(y, y + 26):
        import math
        span = int((30 * 30 - (yy - (y + 30)) ** 2) ** 0.5)
        cv.rect(x - span, yy, x + span, yy, HAIR)
    cv.rect(x - 30, y + 18, x + 30, y + 26, HAIR)
    # eyes
    cv.circle(x - 11, y + 28, 3, BLACK)
    cv.circle(x + 11, y + 28, 3, BLACK)
    # smile
    cv.line(x - 8, y + 42, x + 8, y + 42, BLACK, 3)
    # body / shirt
    cv.rrect(x - 42, y + 64, x + 42, y + 128, 16, SHIRT)
    cv.rrect_outline(x - 42, y + 64, x + 42, y + 128, 16, BLACK, 3)


def draw_robot(cv, x, y, arms="down", s=1.0):
    """Robot: head + antenna + body, centred on x, head top at y.

    s scales the whole figure (1.0 = 116 wide, 168 tall + antenna).
    """
    def X(dx):
        return x + int(round(dx * s))

    def Y(dy):
        return y + int(round(dy * s))

    def R(v):
        return max(2, int(round(v * s)))

    # antenna
    cv.vline(x, Y(-26), Y(-2), BLACK, max(2, R(4)))
    cv.circle(x, Y(-32), R(8), YELLOW)
    cv.disc_outline(x, Y(-32), R(8), BLACK, 3)
    # head
    cv.rrect(X(-58), Y(0), X(58), Y(88), R(16), ROBOT_HEAD)
    cv.rrect_outline(X(-58), Y(0), X(58), Y(88), R(16), BLACK, 3)
    # eyes
    cv.rrect(X(-40), Y(24), X(-8), Y(52), R(8), WHITE)
    cv.rrect(X(8), Y(24), X(40), Y(52), R(8), WHITE)
    cv.circle(X(-24), Y(38), R(8), ROBOT_EYE)
    cv.circle(X(24), Y(38), R(8), ROBOT_EYE)
    cv.circle(X(-24), Y(38), R(3), BLACK)
    cv.circle(X(24), Y(38), R(3), BLACK)
    # smile
    cv.line(X(-18), Y(68), X(18), Y(68), BLACK, 3)
    # body
    cv.rrect(X(-52), Y(94), X(52), Y(168), R(14), ROBOT_BODY)
    cv.rrect_outline(X(-52), Y(94), X(52), Y(168), R(14), BLACK, 3)
    # chest light
    cv.circle(x, Y(128), R(10), YELLOW)
    cv.disc_outline(x, Y(128), R(10), BLACK, 3)
    # arms
    if arms == "down":
        cv.line(X(-52), Y(104), X(-78), Y(150), BLACK, 6)
        cv.line(X(52), Y(104), X(78), Y(150), BLACK, 6)
    elif arms == "shrug":
        cv.line(X(-52), Y(104), X(-84), Y(72), BLACK, 6)
        cv.line(X(52), Y(104), X(84), Y(72), BLACK, 6)
    elif arms == "type":
        cv.line(X(-52), Y(104), X(-84), Y(158), BLACK, 6)
        cv.line(X(52), Y(104), X(84), Y(158), BLACK, 6)


def draw_laptop(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (34, 34, 34))
    cv.rect(x0 + 6, y0 + 6, x1 - 6, y1 - 6, SCREEN)
    # tiny game pixels on the screen
    cv.rect(x0 + 22, y0 + 22, x0 + 46, y0 + 46, (255, 87, 51))
    cv.rect(x0 + 58, y0 + 22, x0 + 82, y0 + 46, (51, 150, 255))
    cv.rect(x0 + 22, y0 + 58, x0 + 46, y0 + 82, (255, 214, 10))
    cv.rect(x0 + 58, y0 + 58, x0 + 82, y0 + 82, (124, 179, 66))


# ------------------------------------------------------------- the meme
def draw_meme():
    cv = Canvas(W, H, WHITE)
    # outer border
    cv.rect(0, 0, W - 1, 5, BLACK)
    cv.rect(0, H - 6, W - 1, H - 1, BLACK)
    cv.rect(0, 0, 5, H - 1, BLACK)
    cv.rect(W - 6, 0, W - 1, H - 1, BLACK)

    # ---- header band
    cv.rect(6, 6, W - 7, 119, YELLOW)
    cv.hline(6, W - 7, 120, BLACK, 4)
    cv.text_centered(W // 2, 20, "WHEN YOU ASK AN AI AGENT", 6, BLACK)
    cv.text_centered(W // 2, 68, "TO BUILD YOU A GAME", 6, BLACK)

    # ---- panel 1: the ask
    cv.hline(6, W - 7, 412, BLACK, 4)
    cv.text_centered(W // 2, 142, "BUILD ME A FUN GAME", 7, BLACK)
    draw_human(cv, 200, 250)
    draw_robot(cv, 800, 224, arms="down")
    # desk + laptop between them
    cv.hline(90, 934, 386, BLACK, 4)
    draw_laptop(cv, 420, 296, 604, 384)

    # ---- panel 2: 0.4 seconds later
    cv.hline(6, W - 7, 704, BLACK, 4)
    cv.text_centered(W // 2, 432, "0.4 SECONDS LATER...", 5, GREY_DARK)
    cv.text_centered(W // 2, 486, "DONE. 12 GAMES SHIPPED.", 6, BLACK)
    # speed lines (left of the robot only; the monitor fills the right)
    for yy in (566, 600, 634):
        cv.hline(60, 170, yy, BLACK, 4)
    draw_robot(cv, 300, 560, arms="down", s=0.8)
    # monitor full of shipped games
    cv.rect(640, 548, 950, 692, (34, 34, 34))
    cv.rect(648, 556, 942, 684, SCREEN)
    tiles = [(255, 87, 51), (51, 150, 255), (255, 214, 10), (124, 179, 66),
             (186, 104, 200), (255, 138, 101), (0, 188, 212), (255, 82, 82)]
    for i, col in enumerate(tiles):
        tx = 660 + (i % 4) * 72
        ty = 568 + (i // 4) * 56
        cv.rect(tx, ty, tx + 58, ty + 44, BLACK)  # black frame
        cv.rect(tx + 3, ty + 3, tx + 55, ty + 41, col)

    # ---- panel 3: the punchline
    cv.hline(6, W - 7, 968, BLACK, 4)
    cv.text_centered(W // 2, 726, "ARE ANY OF THEM FUN?", 7, BLACK)
    # robot shrugging (left) + speech bubble (middle, clear of the monitor)
    cv.rrect(330, 792, 740, 882, 14, WHITE)
    cv.rrect_outline(330, 792, 740, 882, 14, BLACK, 3)
    cv.line(350, 882, 248, 892, BLACK, 3)  # bubble tail to the robot
    cv.line(400, 882, 248, 892, BLACK, 3)
    cv.text(342, 806, "FUN WAS NOT", 5, BLACK)
    cv.text(342, 844, "IN THE PROMPT.", 5, BLACK)
    draw_robot(cv, 190, 884, arms="down")
    # monitor (right): the "game" is one grey square
    cv.rect(760, 800, 980, 960, (34, 34, 34))
    cv.rect(768, 808, 972, 952, SCREEN)
    cv.rect(768, 908, 972, 952, GROUND)
    cv.rect(845, 830, 895, 880, BLACK)  # the square that jumps
    cv.rect(848, 833, 892, 877, GREY_MID)
    cv.circle(858, 896, 3, BLACK)  # jump motion dots
    cv.circle(876, 898, 3, BLACK)
    cv.text(800, 918, "LEVEL 47", 3, GREY_DARK)

    # ---- footer strip
    cv.rect(6, 972, W - 7, 1017, FOOTER_BG)
    cv.text_centered(W // 2, 986, "ALSO SHIPPED BY AN AGENT IN 3 SECONDS", 3, YELLOW)

    return cv


# ------------------------------------------------------------- PNG writer
def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        c = struct.pack(">I", len(data)) + ctype + data
        c += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    cv = draw_meme()
    size = write_png(cv, path)
    import hashlib
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"wrote {path}: {size} bytes, sha256 {digest}")


if __name__ == "__main__":
    main()
