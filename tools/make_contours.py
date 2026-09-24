#!/usr/bin/env python3
"""Generate the decorative contour-line landscape used in the home-page hero.

Run it only when you want a new landscape:

    python tools/make_contours.py            # writes templates/partials/contours.svg
    python tools/make_contours.py --seed 7   # a different landscape

Requires numpy, scipy and contourpy (`pip install numpy scipy contourpy`).
It is NOT needed to build the site: the generated SVG is committed.

The terrain is synthetic (smoothed fractal noise plus one dominant massif).
Lines follow cartographic convention: a thin contour at every step, a heavier
"index" contour every fifth one. Contours are grouped by elevation so the page
can reveal them from the lowest level to the highest.
"""
import argparse
from pathlib import Path

import numpy as np
from contourpy import contour_generator
from scipy.ndimage import gaussian_filter

W, H = 1600, 900          # SVG viewBox
GRID = (450, 253)         # sampling grid (cols, rows)
PEAK = (0.80, 0.36)       # massif position, fraction of width/height
LEVELS = 26
INDEX_EVERY = 5


def make_terrain(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    cols, rows = GRID
    z = np.zeros((rows, cols))
    # fractal noise: several smoothing scales, decreasing amplitude
    for sigma, amp in [(48, 1.0), (24, 0.55), (12, 0.28), (6, 0.12), (3, 0.05)]:
        n = gaussian_filter(rng.standard_normal((rows, cols)), sigma, mode="wrap")
        n /= n.std()
        z += amp * n
    yy, xx = np.mgrid[0:rows, 0:cols]
    px, py = PEAK[0] * cols, PEAK[1] * rows
    # one dominant, slightly elongated massif
    d2 = ((xx - px) / (0.30 * cols)) ** 2 + ((yy - py) / (0.42 * rows)) ** 2
    z += 3.4 * np.exp(-d2)
    # a gentle tilt so the left side (under the text) drops away
    z += 0.9 * (xx / cols)
    return z


def rdp(points: np.ndarray, eps: float) -> np.ndarray:
    """Ramer-Douglas-Peucker line simplification (iterative)."""
    if len(points) < 3:
        return points
    keep = np.zeros(len(points), bool)
    keep[[0, -1]] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        p, q = points[a], points[b]
        seg = q - p
        norm = np.hypot(*seg)
        rel = points[a + 1:b] - p
        if norm == 0:
            dist = np.hypot(rel[:, 0], rel[:, 1])
        else:
            dist = np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / norm
        i = int(np.argmax(dist))
        if dist[i] > eps:
            k = a + 1 + i
            keep[k] = True
            stack += [(a, k), (k, b)]
    return points[keep]


def path_d(line: np.ndarray, closed: bool) -> str:
    pts = " ".join(f"{x:.1f} {y:.1f}" for x, y in line[1:])
    return f"M{line[0][0]:.1f} {line[0][1]:.1f}L{pts}" + ("Z" if closed else "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default="templates/partials/contours.svg")
    args = ap.parse_args()

    z = make_terrain(args.seed)
    cols, rows = GRID
    sx, sy = W / (cols - 1), H / (rows - 1)
    gen = contour_generator(np.arange(cols), np.arange(rows), z)
    levels = np.linspace(np.percentile(z, 6), np.percentile(z, 99.6), LEVELS)

    groups = []
    for i, lv in enumerate(levels):
        cls = "idx" if i % INDEX_EVERY == 0 else "cn"
        paths = []
        for line in gen.lines(lv):
            if len(line) < 6:
                continue
            pts = np.column_stack([line[:, 0] * sx, line[:, 1] * sy])
            closed = bool(np.allclose(pts[0], pts[-1]))
            pts = rdp(pts, 0.7)
            if len(pts) < 3:
                continue
            paths.append(f'<path class="{cls}" pathLength="1" d="{path_d(pts, closed)}"/>')
        if paths:
            groups.append(f'<g class="lv" style="--i:{i}">' + "".join(paths) + "</g>")

    # survey triangle on the highest point inside a window that keeps the label
    # comfortably on screen (right of centre, not at an edge)
    x0, x1 = int(0.62 * cols), int(0.80 * cols)
    y0, y1 = int(0.22 * rows), int(0.72 * rows)
    win = z[y0:y1, x0:x1]
    wy, wx = np.unravel_index(np.argmax(win), win.shape)
    ix, iy = x0 + wx, y0 + wy
    mx, my = ix * sx, iy * sy
    svg = (
        f'<svg class="contours" viewBox="0 0 {W} {H}" preserveAspectRatio="xMaxYMid slice" '
        f'aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">'
        + "".join(groups)
        + f'<g class="summit" transform="translate({mx:.0f} {my:.0f})">'
        + '<circle r="17" class="summit-ring"/>'
        + '<path d="M0 -9.5L8.6 5.5H-8.6Z" class="summit-tri"/>'
        + '<text x="28" y="6" class="summit-label">M\u00fcnchen, 519 m</text>'
        + "</g></svg>"
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"{out}  {out.stat().st_size/1024:.0f} KB  summit at ({mx:.0f}, {my:.0f})  groups={len(groups)}")


if __name__ == "__main__":
    main()
