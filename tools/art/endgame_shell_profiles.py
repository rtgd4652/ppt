"""第二稿银壳的原画截面、闭合截面色带与 PdxMeshShip 贴图。"""

import bisect
import csv
import math
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CONCEPT = ROOT / "art/concepts/aemusa_flagship_redesign_20261107"
OUT = ROOT / "art/models/aemusa_endgame_runtime_v04"
EXPORT = OUT / "export"
STYLES = ("fore_far", "fore_near", "aft_far", "aft_near")
WIDTH, HEIGHT, BORDER = 1024, 512, 5


def clamp(x, a, b):
    return max(a, min(b, x))


class Spline:
    """单调三次插值，和动图共用原始截面及尖端切线。"""

    def __init__(self, x, values):
        self.x = list(x)
        self.values = list(values)
        h = [b - a for a, b in zip(x, x[1:])]
        sec = [(b - a) / step for a, b, step in zip(values, values[1:], h)]
        self.slopes = [sec[0]]
        for i in range(1, len(x) - 1):
            left, right = sec[i - 1], sec[i]
            if left * right <= 0:
                self.slopes.append(0)
            else:
                a, b = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                self.slopes.append((a + b) / (a / left + b / right))
        self.slopes.append(sec[-1])

    def __call__(self, x):
        i = max(0, min(len(self.x) - 2, bisect.bisect_right(self.x, x) - 1))
        h = self.x[i + 1] - self.x[i]
        t = clamp((x - self.x[i]) / h, 0, 1)
        q = 1 - t
        return ((1 + 2*t)*q*q*self.values[i] + t*q*q*h*self.slopes[i]
                + t*t*(3 - 2*t)*self.values[i+1] - t*t*q*h*self.slopes[i+1])


@dataclass
class Shell:
    name: str
    x: list
    edges: tuple
    depth: tuple
    motion: dict

    def slice(self, s):
        x = self.x[0] + s * (self.x[-1] - self.x[0])
        top, fold, bottom = (curve(x) for curve in self.edges)
        # 处于两端的单点共用一个顶点，面片闭合在该点。
        fold = clamp(fold, top, max(top, bottom))
        width = max(0, bottom - top)
        ordinates = (top, top + .48*(fold-top), fold, fold + .53*(bottom-fold), bottom,
                     bottom - .28*width, top + .44*width, top + .12*width)
        curve = math.sin(s * math.pi)
        base = self.depth[0] + (self.depth[1]-self.depth[0])*s + self.depth[2]*curve
        m = self.motion
        base += m["depth_offset"] * (m["end_fraction"] + (1 - m["end_fraction"])*curve)
        return x, ordinates, base

    def phase(self, t):
        m = self.motion
        return t + math.radians(m["sine_degrees"]*math.sin(t) + m["versine_degrees"]*(1-math.cos(t)))


def load_shells():
    folder = CONCEPT / "motion_source"
    with (folder / "orbit_motion.csv").open(encoding="utf-8", newline="") as f:
        motion = {r["shell"]: {k: float(v) for k, v in r.items() if k != "shell"} for r in csv.DictReader(f)}
    with (folder / "shell_contours.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    result = []
    for name in STYLES:
        points = [r for r in rows if r["shell"] == name]
        x = [float(r["x"]) for r in points]
        edges = tuple(Spline(x, [float(r[k]) for r in points]) for k in ("upper_edge", "fold", "lower_edge"))
        depth = tuple(float(points[0][k]) for k in ("depth_start", "depth_end", "depth_arc"))
        result.append(Shell(name, x, edges, depth, motion[name]))
    return result


def uv(index, length, row):
    band = HEIGHT // len(STYLES)
    return ((BORDER + .5 + length*(WIDTH-2*BORDER-1)) / WIDTH,
            1 - (index*band + BORDER + .5 + row/8*(band-2*BORDER-1)) / HEIGHT)


def bake_textures():
    sys.path.insert(0, str(ROOT / "temp/cc_surface_v02_deps"))
    from PIL import Image
    from prepare_central_court_surface_v02 import dds_with_mips

    EXPORT.mkdir(parents=True, exist_ok=True)
    with Image.open(CONCEPT / "outer_shell_oblique_v02.png") as original:
        source = original.convert("RGB")
    atlas = Image.new("RGBA", (WIDTH, HEIGHT))
    pixels = atlas.load()
    band = HEIGHT // len(STYLES)
    # 内侧取原画同一银面的色相，靠近内缘逐步过渡到深靛色。
    reverse_y = (.045, .18, .42, .72, .94, .72, .45, .16, .045)
    finish = (.90, .90, .90, .90, .29, .55, .93, .99, .90)
    for index, shell in enumerate(load_shells()):
        for col in range(WIDTH):
            s = clamp((col-BORDER)/(WIDTH-2*BORDER-1), .017, .983)
            x, ys, _ = shell.slice(s)
            front = ys + (ys[0],)
            for line in range(band):
                q = clamp((line-BORDER)/(band-2*BORDER-1), 0, 1)*8
                row = min(7, int(q))
                f = q-row
                if row < 4:
                    y = (1-f)*front[row] + f*front[row+1]
                    # 边缘向各自材质区收一个纹素，防止把原画天空带进下级 mip。
                    low, high = (ys[0], ys[2]) if row < 2 else (ys[2], ys[4])
                    pad = min(1.4, (high-low)*.18)
                    y = clamp(y, low+pad, high-pad)
                    paint = 1
                else:
                    t = (1-f)*reverse_y[row] + f*reverse_y[row+1]
                    y = ys[0] + t*(ys[2]-ys[0])
                    paint = (1-f)*finish[row] + f*finish[row+1]
                rgb = source.getpixel((round(x), round(y)))
                neutral = (188, 199, 224) if row < 2 or row >= 4 else (49, 60, 95)
                color = [round((.66*v+.34*n)*paint + lining*(1-paint))
                         for v, n, lining in zip(rgb, neutral, (35, 46, 77))]
                pixels[col, index*band+line] = (*color, 255)
    atlas.save(OUT / "shell_albedo.png")
    textures = {"diffuse": atlas,
                "normal": Image.new("RGBA", (16,16), (0,128,0,128)),
                "properties": Image.new("RGBA", (16,16), (0,92,46,105))}
    for suffix, image in textures.items():
        dds_with_mips(image, EXPORT / f"aef04_shell_{suffix}.dds", Image)
    print("四片银壳的色带与三张 BC3 贴图已就绪。")


if __name__ == "__main__":
    bake_textures()
