#!/usr/bin/env python3
"""清理抠图边缘的白边/光晕（不改产品内部像素）。

用法：
  clean_cutout_alpha.py in.png out.png [--erode 2] [--feather 1.0] [--decontam 3] [--from-white 245]
  --from-white T : 输入无 alpha（白底）时，先把亮度 > T 且与四周连通的背景设为透明
  --erode N      : alpha 向内收 N 像素（去掉半透明白边）
  --decontam N   : 边缘 N 像素内，把偏白像素的颜色替换为内部邻近颜色（去色晕）
  --feather R    : 收边后高斯羽化半径
同时输出 out_compare.png（原图 | 处理后，棋盘格背景）便于核对产品没有被改动。
"""
import argparse, sys
from PIL import Image, ImageFilter, ImageChops
import numpy as np

def flood_white(im, t):
    rgb = np.asarray(im.convert('RGB')).astype(np.int16); h, w = rgb.shape[:2]
    white = (rgb.min(axis=2) > t)
    from collections import deque
    bg = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if white[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if white[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and white[ny, nx] and not bg[ny, nx]: bg[ny, nx] = True; q.append((ny, nx))
    rgba = np.dstack([rgb.astype(np.uint8), np.where(bg, 0, 255).astype(np.uint8)])
    return Image.fromarray(rgba, 'RGBA')

def checker(size, s=16):
    w, h = size; a = np.indices((h, w)).sum(axis=0) // s % 2
    v = np.where(a, 200, 255).astype(np.uint8); return Image.fromarray(np.dstack([v, v, v]), 'RGB')

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inp'); ap.add_argument('out'); ap.add_argument('--erode', type=int, default=2)
    ap.add_argument('--feather', type=float, default=1.0); ap.add_argument('--decontam', type=int, default=3)
    ap.add_argument('--from-white', type=int, default=None)
    a = ap.parse_args()
    src = Image.open(a.inp)
    im = flood_white(src, a.from_white) if a.from_white is not None else src.convert('RGBA')
    if im.getchannel('A').getextrema()[0] == 255:
        sys.exit('ERROR: 输入没有透明背景；白底图请加 --from-white 245')
    alpha = im.getchannel('A').point(lambda v: 255 if v > 127 else 0)
    if a.erode > 0: alpha = alpha.filter(ImageFilter.MinFilter(2 * a.erode + 1))
    arr = np.asarray(im).copy()
    if a.decontam > 0:
        inner = np.asarray(alpha.filter(ImageFilter.MinFilter(2 * a.decontam + 1))) > 0
        grow = int(a.feather * 2) + 2
        ring = (np.asarray(alpha.filter(ImageFilter.MaxFilter(2 * grow + 1))) > 0) & ~inner
        blurred = np.asarray(Image.fromarray(np.where(inner[..., None], arr[..., :3], 0).astype(np.uint8)).filter(ImageFilter.BoxBlur(a.decontam + 2))).astype(np.float32)
        wts = np.asarray(Image.fromarray((inner * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(a.decontam + 2))).astype(np.float32) / 255
        fill = np.clip(blurred / np.maximum(wts[..., None], 1e-3), 0, 255).astype(np.uint8)
        whiteish = arr[..., :3].min(axis=2) > 200
        sel = ring & (whiteish | (np.asarray(alpha) == 0)) & (wts > 0.01)
        arr[..., :3][sel] = fill[sel]
    if a.feather > 0: alpha = alpha.filter(ImageFilter.GaussianBlur(a.feather))
    arr[..., 3] = np.asarray(alpha)
    out = Image.fromarray(arr, 'RGBA'); out.save(a.out)
    W, H = out.size; cmp = Image.new('RGB', (W * 2 + 10, H), 'white')
    c1 = checker(src.size); c1.paste(src.convert('RGBA'), (0, 0), src.convert('RGBA')); cmp.paste(c1, (0, 0))
    c2 = checker(out.size); c2.paste(out, (0, 0), out); cmp.paste(c2, (W + 10, 0))
    cp = a.out.rsplit('.', 1)[0] + '_compare.png'; cmp.save(cp)
    print('saved', a.out, 'and', cp)

if __name__ == '__main__':
    main()
