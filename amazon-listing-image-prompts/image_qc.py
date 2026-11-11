#!/usr/bin/env python3
"""image_qc.py —— 亚马逊 Listing 图片自动质检

检查项：
  1. 尺寸/比例：正方形、最长边 ≥2000（示例画布 2400×2400）
  2. 主图（文件名以 01 开头或 --main 指定）：四周边框纯白（RGB ≥250）、产品填充率（非白像素外接框最长边 / 画布边长，亚马逊建议 ≥85%）
  3. 文字检测：装了 tesseract 才做 OCR；否则标「未检测，需人工看」
  4. AI 元数据：XMP 中 DigitalSourceType = trainedAlgorithmicMedia（带人像的 AI 图必须有）
  5. 手机缩略图：输出 320px 缩略图到 <输出目录>/mobile/ 供人工核对
用法：
  python image_qc.py <图片或目录> [--main 01_main.jpg] [--out qc_dir] [--require-ai-meta]
退出码：有 FAIL 时为 1。
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

WHITE = 250

def border_white_ratio(im, band=0.02):
    w, h = im.size; b = max(2, int(min(w, h) * band)); px = im.load(); tot = ok = 0
    step = max(1, min(w, h) // 400)
    for x in range(0, w, step):
        for y in list(range(0, b, step)) + list(range(h - b, h, step)):
            r, g, bl = px[x, y][:3]; tot += 1; ok += (r >= WHITE and g >= WHITE and bl >= WHITE)
    for y in range(0, h, step):
        for x in list(range(0, b, step)) + list(range(w - b, w, step)):
            r, g, bl = px[x, y][:3]; tot += 1; ok += (r >= WHITE and g >= WHITE and bl >= WHITE)
    return ok / tot if tot else 0

def fill_ratio(im):
    g = im.convert("L").point(lambda v: 0 if v >= WHITE else 255)
    bbox = g.getbbox()
    if not bbox: return 0.0, None
    w, h = im.size; bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    return max(bw / w, bh / h), bbox

def ai_meta(path):
    data = Path(path).read_bytes()
    return b"trainedAlgorithmicMedia" in data, (b"AI-generated" in data or b"AI generated" in data)

def ocr_text(path):
    if not shutil.which("tesseract"): return None
    try:
        out = subprocess.run(["tesseract", str(path), "-", "--psm", "11"], capture_output=True, text=True, timeout=60).stdout
        return " ".join(t for t in out.split() if len(t) > 2)
    except Exception:
        return None

def check(path, is_main, outdir, require_ai):
    im = Image.open(path).convert("RGB"); w, h = im.size; res = {"file": str(path), "size": f"{w}x{h}", "checks": []}
    def add(name, status, detail): res["checks"].append({"check": name, "status": status, "detail": detail})
    add("正方形", "PASS" if abs(w - h) <= 2 else "WARN", f"{w}x{h}")
    add("分辨率≥2000", "PASS" if max(w, h) >= 2000 else "FAIL", f"最长边 {max(w, h)}")
    if is_main:
        br = border_white_ratio(im); add("主图边框纯白", "PASS" if br >= 0.98 else "FAIL", f"白色像素占比 {br:.1%}")
        fr, bbox = fill_ratio(im); add("主图产品填充≥85%", "PASS" if fr >= 0.85 else "FAIL", f"填充 {fr:.1%}，外接框 {bbox}")
        txt = ocr_text(path)
        add("主图无文字", "MANUAL" if txt is None else ("PASS" if not txt else "WARN"), "未安装 tesseract，需人工看" if txt is None else (txt[:80] or "未识别到文字"))
    dst, credit = ai_meta(path)
    add("AI 元数据", "PASS" if dst else ("FAIL" if require_ai else "WARN"), f"DigitalSourceType={'trainedAlgorithmicMedia' if dst else '缺失'}；AI-generated 描述={'有' if credit else '无'}")
    m = outdir / "mobile"; m.mkdir(parents=True, exist_ok=True); t = im.copy(); t.thumbnail((320, 320)); t.save(m / (Path(path).stem + "_320.jpg"), quality=85)
    res["status"] = "FAIL" if any(c["status"] == "FAIL" for c in res["checks"]) else "PASS"
    return res

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("target"); ap.add_argument("--main", default=None, help="主图文件名；缺省=文件名以 01 开头的图")
    ap.add_argument("--out", default=None); ap.add_argument("--require-ai-meta", action="store_true"); a = ap.parse_args()
    p = Path(a.target); files = sorted([f for f in p.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]) if p.is_dir() else [p]
    outdir = Path(a.out) if a.out else (p if p.is_dir() else p.parent) / "qc"; outdir.mkdir(parents=True, exist_ok=True)
    results = [check(f, (a.main == f.name) if a.main else f.name.startswith("01"), outdir, a.require_ai_meta) for f in files]
    (outdir / "qc_result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    lines = ["# image_qc 结果", ""]
    for r in results:
        lines.append(f"## {Path(r['file']).name} — {r['status']}（{r['size']}）")
        lines += [f"- {c['check']}：{c['status']}（{c['detail']}）" for c in r["checks"]]; lines.append("")
    (outdir / "qc_report.md").write_text("\n".join(lines)); print("\n".join(lines))
    sys.exit(1 if any(r["status"] == "FAIL" for r in results) else 0)

if __name__ == "__main__":
    main()
