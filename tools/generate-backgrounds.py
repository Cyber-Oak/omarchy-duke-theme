#!/usr/bin/env python3
"""Generate the Duke wallpapers into backgrounds/.

Everything here is procedural: smooth noise, gaussian glows and a green
tone curve. No source images, no logos.

    python3 -m venv .venv && .venv/bin/pip install pillow numpy
    .venv/bin/python tools/generate-backgrounds.py [--width 3840 --height 2160]

Seeds are fixed, so the output is reproducible.
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "backgrounds"

# colors.toml background, a deep green, the accent, and a pale green highlight.
BG = np.array([0x0A, 0x0C, 0x0A], np.float32) / 255
DEEP = np.array([0x06, 0x3A, 0x0A], np.float32) / 255
ACCENT = np.array([0x1F, 0xE8, 0x1F], np.float32) / 255
HOT = np.array([0xD8, 0xFF, 0xC8], np.float32) / 255


def smooth_noise(rng, w, h, cells_x, cells_y):
    """Value noise in 0..1: a coarse random grid upscaled bicubically."""
    grid = rng.random((cells_y + 1, cells_x + 1)).astype(np.float32)
    img = Image.fromarray(grid, mode="F").resize((w, h), Image.BICUBIC)
    return np.clip(np.asarray(img), 0, 1)


def fbm(rng, w, h, base=4, octaves=5, aspect=None):
    """Fractal sum of value noise. `aspect` stretches cells (x cells per y cell)."""
    aspect = aspect if aspect is not None else w / h
    total = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    for i in range(octaves):
        cy = base * 2**i
        cx = max(1, int(round(cy * aspect)))
        total += amp * smooth_noise(rng, w, h, cx, cy)
        norm += amp
        amp *= 0.5
    return total / norm


def tone(energy):
    """Map glow energy (0..inf) onto the BG -> DEEP -> ACCENT -> HOT ramp."""
    e = (1.0 - np.exp(-np.maximum(energy, 0)))[..., None]
    lo = BG + (DEEP - BG) * (e / 0.35)
    mid = DEEP + (ACCENT - DEEP) * ((e - 0.35) / 0.45)
    hi = ACCENT + (HOT - ACCENT) * np.clip((e - 0.8) / 0.2, 0, 1) ** 1.6
    return np.where(e < 0.35, lo, np.where(e < 0.8, mid, hi))


def finish(rgb, rng, vignette=0.55):
    h, w, _ = rgb.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
    v = 1.0 - vignette * np.clip(r / 1.414, 0, 1) ** 2
    rgb = BG + (rgb - BG) * v[..., None]
    # Fine dither so the dark gradients never band on 8-bit panels.
    rgb = rgb + (rng.random(rgb.shape, dtype=np.float32) - 0.5) * (1.5 / 255)
    return Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")


def gauss(x, y, cx, cy, sx, sy):
    return np.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))


def aurora(w, h, seed=2001):
    """Curtains of green light hanging across the lower half."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = x / w, y / h
    warp = fbm(rng, w, h, base=2, octaves=4) - 0.5
    # Cells 24x wider in y than x: tall vertical rays.
    rays = fbm(rng, w, h, base=1, octaves=4, aspect=24)
    energy = np.zeros((h, w), np.float32)

    ribbons = [
        # base, amplitude, freq, phase, width, strength
        (0.66, 0.08, 1.1, 0.4, 0.024, 2.0),
        (0.58, 0.05, 1.9, 2.2, 0.018, 1.1),
        (0.74, 0.04, 0.7, 4.0, 0.030, 0.7),
    ]
    for base, amp, freq, phase, width, strength in ribbons:
        centre = base + amp * np.sin(2 * np.pi * freq * u + phase) + 0.08 * warp
        d = v - centre
        # Sharp lower edge, long fade upward: the profile of a hanging curtain.
        shape = np.where(d > 0, np.exp(-((d / (width * 1.6)) ** 2)), np.exp(d / (width * 7.0)))
        energy += strength * shape * (0.18 + 1.2 * rays**2)

    # A soft wash on the horizon and a faint high glow for depth.
    energy += 0.18 * gauss(u, v, 0.5, 1.08, 0.7, 0.2)
    energy += 0.05 * gauss(u, v, 0.80, 0.16, 0.25, 0.18)
    energy *= 0.7 + 0.6 * fbm(rng, w, h, base=3, octaves=3)
    return finish(tone(energy * 0.75), rng)


def orbs(w, h, seed=1115):
    """Soft glowing blobs in a dark field, circled by broken rings of light."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    ar = w / h
    u, v = x / w * ar, y / h
    uu = u + (fbm(rng, w, h, base=2, octaves=4) - 0.5) * 0.25
    vv = v + (fbm(rng, w, h, base=2, octaves=4) - 0.5) * 0.25
    energy = np.zeros((h, w), np.float32)

    # The main mass sits right of centre, leaving the left calm for windows.
    blobs = [
        # cx (aspect units), cy, radius, strength
        (0.70 * ar, 0.52, 0.16, 2.6),
        (0.57 * ar, 0.38, 0.08, 1.3),
        (0.84 * ar, 0.67, 0.07, 1.1),
        (0.47 * ar, 0.71, 0.05, 0.7),
        (0.93 * ar, 0.28, 0.05, 0.5),
        (0.22 * ar, 0.24, 0.10, 0.3),
        (0.10 * ar, 0.84, 0.07, 0.2),
    ]
    for cx, cy, r, s in blobs:
        energy += s * gauss(uu, vv, cx, cy, r, r)

    # A thin glowing ring around the main mass, broken up by noise.
    d = np.hypot(uu - blobs[0][0], vv - blobs[0][1])
    ring = np.exp(-(((d - 0.30) / 0.010) ** 2))
    breakup = np.clip(fbm(rng, w, h, base=3, octaves=3) * 2.2 - 0.7, 0, 1)
    energy += 1.2 * ring * breakup

    # Two fainter arcs further out, each showing only where the noise allows.
    for radius, width, strength in [(0.42, 0.006, 0.45), (0.55, 0.004, 0.25)]:
        arc = np.exp(-(((d - radius) / width) ** 2))
        gate = np.clip(fbm(rng, w, h, base=2, octaves=2) * 2.6 - 1.1, 0, 1)
        energy += strength * arc * gate

    energy += 0.15 * fbm(rng, w, h, base=2, octaves=3) * gauss(u, v, 0.7 * ar, 0.5, 0.9, 0.7)
    return finish(tone(energy), rng, vignette=0.45)


def minimal(w, h, seed=42):
    """Almost black: one low corner glow and a hairline horizon."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = x / w, y / h
    energy = 0.38 * gauss(u, v, 0.92, 1.02, 0.42, 0.30)
    energy += 0.06 * gauss(u, v, 0.05, -0.05, 0.4, 0.3)
    horizon = np.exp(-(((v - 0.78) / (1.6 / 1080)) ** 2)) * np.exp(-(((u - 0.78) / 0.28) ** 2))
    energy += 0.5 * horizon
    energy *= 0.85 + 0.3 * fbm(rng, w, h, base=2, octaves=3)
    return finish(tone(energy), rng, vignette=0.3)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--width", type=int, default=3840)
    p.add_argument("--height", type=int, default=2160)
    a = p.parse_args()
    OUT.mkdir(exist_ok=True)
    for name, fn in [("1-duke-aurora", aurora), ("2-duke-orbs", orbs), ("3-duke-minimal", minimal)]:
        path = OUT / f"{name}.png"
        fn(a.width, a.height).save(path, optimize=True)
        print(path)


if __name__ == "__main__":
    main()
