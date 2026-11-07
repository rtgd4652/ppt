"""将渲染帧编码为无限循环的 GIF，用同一色表避免背景在帧间闪烁。"""
from pathlib import Path
import sys

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.path.insert(0, str(Path("temp/cc_surface_v02_deps").resolve()))
    from PIL import Image, ImageChops


def shared_palette(paths):
    # 为银壳的亮暗面和中央暖金线都留出颜色。
    atlas = Image.new("RGB", (256 * 4, 224 * 4))
    for i in range(16):
        with Image.open(paths[i * len(paths) // 16]) as frame:
            color = frame.convert("RGB")
            x, y = (i % 4) * 256, (i // 4) * 224
            atlas.paste(color.resize((256, 144), Image.Resampling.BOX), (x, y))
            crop = color.crop((205, 125, 842, 325))
            atlas.paste(crop.resize((256, 80), Image.Resampling.BOX), (x, y + 144))
    general = atlas.quantize(colors=237, method=Image.Quantize.MEDIANCUT)
    with Image.open(paths[0]) as first:
        candidates = [rgb for rgb in first.convert("RGB").get_flattened_data()
                      if rgb[0] > rgb[1] + 6 and rgb[1] > rgb[2] + 2]
    gold = Image.new("RGB", (len(candidates), 1))
    gold.putdata(candidates)
    highlights = gold.quantize(colors=18, method=Image.Quantize.MEDIANCUT)
    colors = general.getpalette()[:237 * 3] + highlights.getpalette()[:18 * 3]
    palette = Image.new("P", (1, 1))
    palette.putpalette(colors + [0, 0, 0])
    return palette


def fixed_dither(size):
    # 在所有帧的相同位置抖动，渐变中的细纹保持静止。
    matrix = [[0]]
    for _ in range(3):
        matrix = [[4 * matrix[y % len(matrix)][x % len(matrix)]
                   + ((0, 2), (3, 1))[y // len(matrix)][x // len(matrix)]
                   for x in range(len(matrix) * 2)] for y in range(len(matrix) * 2)]
    rows = [bytes(round(128 + (v / 63.0 - .5) * 5.4) for v in line) for line in matrix]
    width, height = size
    data = b"".join((rows[y % 8] * ((width + 7) // 8))[:width] for y in range(height))
    return Image.frombytes("L", size, data).convert("RGB")


def encode(directory, target, expected_frames=160):
    paths = sorted(directory.glob("*.png"))
    if len(paths) != expected_frames:
        raise ValueError(f"需要{expected_frames}帧，实际为{len(paths)}")
    palette = shared_palette(paths)
    with Image.open(paths[0]) as first:
        noise = fixed_dither(first.size)

    def render_indices():
        for source in paths:
            with Image.open(source) as frame:
                adjusted = ImageChops.add(frame.convert("RGB"), noise, offset=-128)
                yield adjusted.quantize(palette=palette, dither=Image.Dither.NONE)

    frames = render_indices()
    first = next(frames)
    # GIF 以厘秒计时。24 fps 的三维源也可精确落在同一个八秒周期。
    ends = [round(800*i/len(paths)) for i in range(len(paths)+1)]
    durations = [(b-a)*10 for a,b in zip(ends,ends[1:])]
    first.save(target, format="GIF", save_all=True, append_images=frames,
               palette=bytes(palette.getpalette()), transparency=255,
               optimize=True, disposal=1, loop=0, duration=durations)
    print(f"{target.name}: {target.stat().st_size:,} bytes")


if __name__ == "__main__":
    encode(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv)>3 else 160)
