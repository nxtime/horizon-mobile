"""Starling's touch buttons in a Bedrock-like look, drawn from scratch: a 24x24 stone-grey tile
(a speckled face, a black outline with cut corners, a 2-pixel bevel lit at the top left) and a
thick white icon outlined in dark grey; pressed, the face darkens, the bevel turns over and the
icon sinks a pixel. The sprites go to crates/horizon-client/assets/touch, which the game carries
as `starling:touch/<name>` (hud.rs `TOUCH_SPRITES`; a resource pack's own win).

    python packaging/touch/make.py                     # the sprites
    python packaging/touch/make.py SCREENSHOT OUTDIR   # and a sheet and a preview, to look at
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "crates" / "horizon-client" / "assets" / "touch"
T = 24  # a button's tile
STICK = 48  # the stick's base

OUTLINE = (16, 16, 16, 245)
ICON = (255, 255, 255, 255)
ICON_EDGE = (38, 38, 38, 255)


def face(pressed, alpha):
    """The face's grey and its bevel's, up and pressed."""
    if pressed:
        return dict(face=118, light=(78, 92), dark=(176, 158), alpha=alpha)
    return dict(face=150, light=(222, 196), dark=(92, 112), alpha=alpha)


def plate(size, pressed, alpha=226, seed=7):
    """A bevelled stone plate: outline, two rings of bevel, a speckled face."""
    look = face(pressed, alpha)
    rng = random.Random(seed + (1000 if pressed else 0))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    last = size - 1
    for y in range(size):
        for x in range(size):
            # Cut corners: the outline's corner pixels go, and the bevel's step in.
            if (x in (0, last)) and (y in (0, last)):
                continue
            ring = min(x, y, last - x, last - y)
            if ring == 0:
                px[x, y] = OUTLINE
                continue
            if ring in (1, 2) and (x in (1, last - 1)) and (y in (1, last - 1)):
                px[x, y] = OUTLINE
                continue
            top_left = (x + y) < last
            if ring <= 2:
                shade = look["light"][ring - 1] if top_left else look["dark"][ring - 1]
                px[x, y] = (shade, shade, shade, min(255, look["alpha"] + 20))
            else:
                g = look["face"] + rng.choice((-14, -8, -4, 0, 0, 0, 4, 8, 10))
                px[x, y] = (g, g, g, look["alpha"])
    return img


ICONS = {
    "jump": """
        .......##.......
        ......####......
        .....######.....
        ....########....
        ...##########...
        ..############..
        .....######.....
        .....######.....
        .....######.....
        .....######.....
        ................
        ..############..
        ..############..
    """,
    "sneak": """
        ..############..
        ..############..
        ................
        .....######.....
        .....######.....
        .....######.....
        .....######.....
        ..############..
        ...##########...
        ....########....
        .....######.....
        ......####......
        .......##.......
    """,
    "attack": """
        .............###
        ............####
        ...........####.
        ..........####..
        .........####...
        ........####....
        .......####.....
        ..##..####......
        ...######.......
        ....####........
        ...######.......
        ..###..##.......
        .###............
        ###.............
        ##..............
    """,
    "use": """
        ......####......
        ......####......
        ......####......
        ......####......
        ................
        ####...##...####
        ####..####..####
        ####..####..####
        ####...##...####
        ................
        ......####......
        ......####......
        ......####......
        ......####......
    """,
    "inventory": """
        ###..###..###
        ###..###..###
        ###..###..###
    """,
    "chat": """
        .############.
        ##############
        ##..........##
        ##.########.##
        ##..........##
        ##.######...##
        ##..........##
        ##############
        .#####..######
        ....###.......
        ....##........
        ....#.........
    """,
    "pause": """
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
        ..####..####..
    """,
    "drop": """
        .....####.....
        .....####.....
        .....####.....
        .....####.....
        ..##########..
        ...########...
        ....######....
        .....####.....
        ......##......
        ..............
        ##############
        ##############
    """,
    "offhand": """
        ....##..........
        ...###..........
        ..##############
        .###############
        ..##############
        ...###..........
        ....##..........
        ................
        ..........##....
        ..........###...
        ##############..
        ###############.
        ##############..
        ..........###...
        ..........##....
    """,
    "camera": """
        .....######.....
        ...##########...
        .####......####.
        ###....##....###
        ##....####....##
        ###....##....###
        .####......####.
        ...##########...
        .....######.....
    """,
    "command": """
        ..........###
        .........###.
        ........###..
        .......###...
        ......###....
        .....###.....
        ....###......
        ...###.......
        ..###........
        .###.........
        ###..........
    """,
    "debug": """
        ######.#####.
        ######.######
        ##.........##
        ##.........##
        #####...####.
        #####...####.
        ##.........##
        ##.........##
        ##.....######
        ##.....#####.
    """,
    "pick": """
        ......#......
        ....##.##....
        ..##.....##..
        ##.........##
        #.##.....##.#
        #...##.##...#
        #.....#.....#
        #.....#.....#
        #.....#.....#
        ##....#....##
        ..##..#..##..
        ....##.##....
        ......#......
    """,
    "players": """
        ###.#########
        ###.#########
        .............
        ###.#########
        ###.#########
        .............
        ###.#########
        ###.#########
    """,
    "up": """
        .......##.......
        ......####......
        .....######.....
        ....########....
        ...##########...
        ..############..
        .##############.
        ################
    """,
}


def bitmap(name):
    rows = [r.strip() for r in ICONS[name].strip("\n").splitlines() if r.strip()]
    width = max(len(r) for r in rows)
    return [r.ljust(width, ".") for r in rows]


def draw_icon(img, rows, ox, oy):
    """`rows` at (ox, oy): white, with a dark edge around (and between) its pixels."""
    px = img.load()
    on = {(ox + x, oy + y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "#"}
    for (x, y) in on:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                p = (x + dx, y + dy)
                if p not in on and 0 <= p[0] < img.width and 0 <= p[1] < img.height:
                    px[p] = ICON_EDGE
    for p in on:
        px[p] = ICON


def tile(name, pressed, turn=None):
    img = plate(T, pressed, seed=sum(map(ord, name or "plain")))
    if name:
        rows = bitmap(name)
        if turn:
            # The D-pad's arrows: the same icon turned.
            square = Image.new("1", (16, 16))
            for y, row in enumerate(rows):
                for x, c in enumerate(row):
                    if c == "#":
                        square.putpixel((x, y + (16 - len(rows)) // 2), 1)
            square = square.transpose(turn)
            rows = ["".join("#" if square.getpixel((x, y)) else "." for x in range(16))
                    for y in range(16)]
        h, w = len(rows), len(rows[0])
        ox, oy = (T - w) // 2, (T - h) // 2 + (1 if pressed else 0)
        draw_icon(img, rows, ox, oy)
    return img


# The Modern style's icons: thin white outlines, drawn at four times their size and scaled down.
M = 64
LINE = 20


def line_icon(paint):
    big = M * 4
    img = Image.new("RGBA", (big, big), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)

    def pts(*p):
        return [(x * big / 24, y * big / 24) for x, y in p]

    def path(*p, close=False):
        p = pts(*p) + (pts(p[0]) if close else [])
        d.line(p, fill=ICON, width=LINE, joint="curve")
        for x, y in p:
            d.ellipse((x - LINE / 2, y - LINE / 2, x + LINE / 2, y + LINE / 2), fill=ICON)

    def ring(x, y, r):
        (x0, y0), (x1, y1) = pts((x - r, y - r), (x + r, y + r))
        d.ellipse((x0, y0, x1, y1), outline=ICON, width=LINE)

    def box(x0, y0, x1, y1, r=2):
        (a, b), (c, e) = pts((x0, y0), (x1, y1))
        d.rounded_rectangle((a, b, c, e), radius=r * big / 24, outline=ICON, width=LINE)

    paint(path, ring, box)
    return img.resize((M, M), Image.Resampling.LANCZOS)


def _sword(path, ring, box):
    path((20, 4), (14, 4), (5, 13), (11, 19), (20, 10), (20, 4))
    path((3, 15), (9, 21))
    path((4, 20), (2, 22))


def _eye(path, ring, box):
    path((2, 12), (7, 7), (12, 5.5), (17, 7), (22, 12), (17, 17), (12, 18.5), (7, 17), (2, 12))
    ring(12, 12, 3)


def _bug(path, ring, box):
    box(7, 8, 17, 21, 5)
    path((9, 8), (9, 6), (15, 6), (15, 8))
    path((12, 12), (12, 21))
    path((2, 11), (7, 12))
    path((22, 11), (17, 12))
    path((2, 20), (7, 17))
    path((22, 20), (17, 17))


def _players(path, ring, box):
    ring(9, 8, 4)
    path((2, 20), (4, 15), (9, 14), (14, 15), (16, 20))
    path((15, 4.5), (18, 6), (18, 10), (15, 11.5))
    path((18, 14.5), (21, 16), (22, 20))


MODERN = {
    "jump": lambda path, ring, box: path((12, 3), (21, 12), (16, 12), (16, 20), (8, 20), (8, 12),
                                         (3, 12), close=True),
    "sneak": lambda path, ring, box: (
        path((12, 18), (21, 9), (16, 9), (16, 4), (8, 4), (8, 9), (3, 9), close=True),
        path((6, 21), (18, 21))),
    "inventory": lambda path, ring, box: (
        box(5, 7, 19, 21, 4),
        path((9, 7), (9, 4), (15, 4), (15, 7)),
        path((8, 13), (16, 13)),
        box(9, 13, 15, 18, 1)),
    "menu": lambda path, ring, box: (path((4, 6), (20, 6)), path((4, 12), (20, 12)),
                                     path((4, 18), (20, 18))),
    "close": lambda path, ring, box: (path((5, 5), (19, 19)), path((19, 5), (5, 19))),
    "offhand": lambda path, ring, box: (
        path((3, 8), (21, 8)), path((17, 4), (21, 8), (17, 12)),
        path((21, 16), (3, 16)), path((7, 12), (3, 16), (7, 20))),
    "drop": lambda path, ring, box: (
        path((12, 3), (12, 15)), path((7, 10), (12, 15), (17, 10)), path((4, 20), (20, 20))),
    "pause": lambda path, ring, box: (box(6, 4, 10, 20, 1), box(14, 4, 18, 20, 1)),
    "chat": lambda path, ring, box: path((3, 5), (21, 5), (21, 17), (11, 17), (6, 21), (6, 17),
                                         (3, 17), close=True),
    "command": lambda path, ring, box: (box(2, 4, 22, 20, 2), path((6, 9), (10, 12), (6, 15)),
                                        path((12, 15), (18, 15))),
    "camera": _eye,
    "debug": _bug,
    "players": _players,
    "attack": _sword,
    "use": lambda path, ring, box: (ring(12, 12, 8), path((12, 8), (12, 16)), path((8, 12), (16, 12))),
    "pick": lambda path, ring, box: (ring(12, 12, 8), ring(12, 12, 2)),
}


def stick_base():
    """The stick's base: a large plate, its face see-through so the world shows."""
    return plate(STICK, False, alpha=96, seed=3)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    sprites = {}
    for name in ["jump", "sneak", "attack", "use", "inventory", "chat", "pause", "drop", "offhand",
                 "camera", "command", "debug", "pick", "players"]:
        sprites[name] = tile(name, False)
        sprites[name + "_pressed"] = tile(name, True)
    turns = {"up": None, "down": Image.Transpose.ROTATE_180,
             "left": Image.Transpose.ROTATE_90, "right": Image.Transpose.ROTATE_270}
    for d, turn in turns.items():
        sprites["dpad_" + d] = tile("up", False, turn) if turn else tile("up", False)
        sprites["dpad_" + d + "_pressed"] = tile("up", True, turn) if turn else tile("up", True)
    sprites["dpad_middle"] = tile(None, False)
    sprites["stick"] = stick_base()
    sprites["stick_knob"] = tile(None, False)
    for name, paint in MODERN.items():
        sprites["modern_" + name] = line_icon(paint)
    for name, img in sprites.items():
        img.save(OUT / f"{name}.png")
    return sprites


def preview(sprites, background, out):
    """The sprites where Starling's default layout puts its buttons, over a screenshot of it
    (3200 x 1440): each covers the old round button it replaces."""
    bg = Image.open(background).convert("RGBA")
    k = bg.width / 2000  # the places below are measured on the screenshot shown at 2000 wide

    def put(img, cx, cy, side):
        big = img.resize((round(side * k),) * 2, Image.Resampling.NEAREST)
        bg.alpha_composite(big, (round(cx * k - big.width / 2), round(cy * k - big.height / 2)))

    put(sprites["attack_pressed"], 1620, 548, 170)
    put(sprites["use"], 1840, 481, 130)
    put(sprites["jump"], 1810, 682, 170)
    put(sprites["sneak"], 1610, 772, 130)
    put(sprites["offhand"], 578, 858, 90)
    put(sprites["drop"], 1420, 858, 90)
    put(sprites["camera"], 860, 77, 100)
    put(sprites["pause"], 1000, 77, 100)
    put(sprites["stick"], 220, 705, 300)
    put(sprites["stick_knob"], 250, 680, 130)
    bg.convert("RGB").save(out, quality=92)


def sheet(sprites, out):
    names = list(sprites)
    cols = 8
    cell = T * 5 + 12
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cell, rows * cell), (70, 120, 60, 255))
    for i, name in enumerate(names):
        sp = sprites[name]
        side = T * 5 if sp.width == T else T * 5
        big = sp.resize((side, side), Image.Resampling.NEAREST)
        img.alpha_composite(big, ((i % cols) * cell + 6, (i // cols) * cell + 6))
    img.convert("RGB").save(out)


if __name__ == "__main__":
    sprites = build()
    if len(sys.argv) > 2:
        look = Path(sys.argv[2])
        look.mkdir(parents=True, exist_ok=True)
        sheet(sprites, look / "sheet.png")
        preview(sprites, sys.argv[1], look / "preview.jpg")
    print("ok", len(sprites))
