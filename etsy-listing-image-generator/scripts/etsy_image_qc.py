#!/usr/bin/env python3
"""Etsy 商品图自动质检（只读，不改图）。
检查白底、产品占比、分辨率和 alt。图上文字没有 OCR 时只能人工核对。

用法：
  etsy_image_qc.py img1.png img2.jpg ...            # 逐张检查
  etsy_image_qc.py --plan image_plan.json [--root DIR]  # 按图片方案（含 alt、slot、kind）检查
  可选：--sheet out.png 生成手机尺寸缩略图总览（340 px/张，用于人工看手机端是否看得清）
       --json report.json
检查项（ERROR 会让退出码=1）：
  - 首图最短边 < 635 px → ERROR；任一图最短边 < 2000 px → WARN（Etsy 建议 ≥2000）
  - 首图为竖图 → WARN（Etsy 首图建议横图或方图；不再写"推荐 4:3"）
  - 产品占比（有 alpha 用 alpha；无 alpha 用四角背景色差估计）< 35% 或 > 95% → WARN
  - 产品四周留边 < 4% → WARN
  - 白边/白色光晕：alpha 边缘一圈像素的平均亮度 > 235 且与内部差距大 → WARN（无白边款必须为 0）
  - 白底主图（四角接近纯白）→ INFO（Etsy 主图不强制白底，生活场景优先）
  - alt：缺失 → ERROR；> 250 字符 → ERROR（kind=reserved 的空位跳过）
  - 文件 > 10 MB → WARN
"""
import argparse, json, os, sys
from PIL import Image, ImageDraw
import numpy as np

def bg_mask(arr):
    """Return boolean mask of 'product' pixels."""
    if arr.shape[2] == 4 and arr[..., 3].min() < 250:
        return arr[..., 3] > 16, True
    rgb = arr[..., :3].astype(np.int16)
    h, w = rgb.shape[:2]; k = max(2, min(h, w) // 50)
    corners = np.concatenate([rgb[:k, :k].reshape(-1, 3), rgb[:k, -k:].reshape(-1, 3), rgb[-k:, :k].reshape(-1, 3), rgb[-k:, -k:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    diff = np.abs(rgb - bg).sum(axis=2)
    return diff > 40, False

def halo_score(arr):
    if arr.shape[2] != 4: return None
    a = arr[..., 3] > 16
    if a.all() or not a.any(): return None
    inner = a.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        inner &= np.roll(a, (dy, dx), axis=(0, 1))
    edge = a & ~inner
    deep = inner.copy()
    for _ in range(4):
        d2 = deep.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): d2 &= np.roll(deep, (dy, dx), axis=(0, 1))
        deep = d2
    lum = arr[..., :3].mean(axis=2)
    e = float(lum[edge].mean()) if edge.any() else 0.0
    i = float(lum[deep].mean()) if deep.any() else e
    return e, i

def check(path, idx, alt=None, kind=None):
    res = dict(file=path, slot=idx, errors=[], warns=[], info=[])
    if kind == 'reserved':
        res['info'].append('reserved slot (老板上传未修图实拍)，跳过'); return res
    if not path or not os.path.exists(path):
        res['errors'].append('file missing'); return res
    im = Image.open(path); w, h = im.size; s = min(w, h)
    res.update(width=w, height=h)
    if idx == 1 and s < 635: res['errors'].append(f'first image short side {s} < 635 px')
    if s < 2000: res['warns'].append(f'short side {s} < 2000 px (Etsy 建议)')
    if idx == 1 and h > w: res['warns'].append('first image is portrait (首图建议横图或方图)')
    if os.path.getsize(path) > 10 * 1024 * 1024: res['warns'].append('file > 10 MB')
    arr = np.asarray(im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB'))
    if arr.ndim == 2: arr = np.stack([arr] * 3, axis=2)
    m, has_alpha = bg_mask(arr)
    occ = float(m.mean()); res['occupancy_pct'] = round(100 * occ, 1)
    if occ < 0.35: res['warns'].append(f'product occupancy {occ:.0%} < 35%')
    if occ > 0.95 and has_alpha: res['warns'].append(f'product occupancy {occ:.0%} > 95%')
    ys, xs = np.where(m)
    if len(xs) and (has_alpha or occ < 0.9):
        margins = [xs.min() / w, (w - 1 - xs.max()) / w, ys.min() / h, (h - 1 - ys.max()) / h]
        res['min_margin_pct'] = round(100 * min(margins), 1)
        if min(margins) < 0.04: res['warns'].append(f'product margin {min(margins):.1%} < 4%')
    hs = halo_score(arr)
    if hs:
        e, i = hs; res['edge_lum'] = round(e, 1); res['inner_lum'] = round(i, 1)
        if e > 235 and e - i > 25: res['warns'].append(f'white halo on cutout edge (edge lum {e:.0f} vs inner {i:.0f}) — 无白边款不允许')
    rgb = arr[..., :3]; k = max(2, s // 50)
    corners = np.concatenate([rgb[:k, :k].reshape(-1, 3), rgb[-k:, -k:].reshape(-1, 3)])
    if corners.min() > 240: res['info'].append('white background (Etsy 不强制白底；主图优先生活场景)')
    if alt is not None or kind is not None:
        if not alt: res['errors'].append('missing alt text (最终图出来后对着画面写)')
        elif len(alt) > 250: res['errors'].append(f'alt {len(alt)} > 250')
    res['info'].append('图上文字/产品一致性/工艺一致：需人工核对（无 OCR）')
    return res

def sheet(items, out, tw=340):
    thumbs = []
    for it in items:
        p = it.get('file')
        if p and os.path.exists(p):
            src = Image.open(p).convert('RGBA'); im = Image.new('RGB', src.size, 'white'); im.paste(src, (0, 0), src); im.thumbnail((tw, tw))
        else:
            im = Image.new('RGB', (tw, tw), (235, 235, 235)); ImageDraw.Draw(im).text((10, tw // 2), 'RESERVED / MISSING', fill=(90, 90, 90))
        c = Image.new('RGB', (tw, tw + 22), 'white'); c.paste(im, ((tw - im.width) // 2, (tw - im.height) // 2))
        ImageDraw.Draw(c).text((6, tw + 4), f"{it.get('slot', ''):02d} {os.path.basename(p or '')[:40]}" if isinstance(it.get('slot'), int) else str(p), fill=(0, 0, 0))
        thumbs.append(c)
    cols = min(5, max(1, len(thumbs))); rows = (len(thumbs) + cols - 1) // cols
    S = Image.new('RGB', (cols * (tw + 8), rows * (tw + 30)), 'white')
    for n, t in enumerate(thumbs): S.paste(t, ((n % cols) * (tw + 8), (n // cols) * (tw + 30)))
    S.save(out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('images', nargs='*'); ap.add_argument('--plan'); ap.add_argument('--root', default='')
    ap.add_argument('--sheet'); ap.add_argument('--json')
    a = ap.parse_args(); items = []
    if a.plan:
        P = json.load(open(a.plan)); root = a.root or os.path.dirname(os.path.abspath(a.plan))
        for s in P['slots']:
            f = s.get('file'); f = os.path.join(root, f) if f and not os.path.isabs(f) else f
            items.append(dict(slot=s['slot'], file=f, alt=s.get('alt', ''), kind=s.get('kind')))
    else:
        items = [dict(slot=n + 1, file=p, alt=None, kind=None) for n, p in enumerate(a.images)]
    results = [check(it['file'], it['slot'], it['alt'], it['kind']) for it in items]
    nerr = 0
    for r in results:
        print(f"[{r['slot']:02d}] {os.path.basename(r['file'] or '-')} {r.get('width', '')}x{r.get('height', '')} occ={r.get('occupancy_pct', '-')}% margin={r.get('min_margin_pct', '-')}%")
        for m in r['errors']: print('     ERROR', m)
        for m in r['warns']: print('     WARN', m)
        nerr += len(r['errors'])
    if a.sheet: sheet(items, a.sheet); print('sheet:', a.sheet)
    if a.json: json.dump(results, open(a.json, 'w'), ensure_ascii=False, indent=1)
    print('OVERALL:', 'FAIL' if nerr else 'PASS')
    sys.exit(1 if nerr else 0)

if __name__ == '__main__':
    main()
