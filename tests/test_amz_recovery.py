"""Amazon skills regression tests. Run: python -m pytest -q tests"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; PY = sys.executable; FX = ROOT / "tests" / "fixtures"

def run(*a):
    return subprocess.run([PY, *map(str, a)], capture_output=True, text=True, cwd=ROOT)

def test_ads_gates_1617(tmp_path):
    out = tmp_path / "a.json"
    r = run(ROOT / "amazon-ads-diagnostics/ads_csv_analyzer.py", FX / "st_synthetic.csv", "--target-acos", "30", "--irrelevant-terms", "weird stuff", "-o", out)
    assert r.returncode == 0, r.stderr
    d = json.loads(out.read_text()); kw = {k["关键词"]: k["建议动作"] for k in d["keywords"]}
    assert d["gates"]["negate_min_clicks"] == 20
    assert kw["term fifteen clicks"].startswith("保持")          # 15 次点击 <20，不否
    assert kw["term twenty clicks"].startswith("否定精准")        # 20 次点击 0 单，否
    assert kw["term expensive"].startswith("否定精准")            # 保险规则：花费 ≥2×目标 CPA
    assert kw["weird stuff"].startswith("人工复核")               # 明显无关词：人工复核
    assert kw["term winner"].startswith("收割")

def test_listing_validator_builtin():
    assert run(ROOT / "amazon-listing-writer/validate_listing.py", "--test-blacklist").returncode == 0

def test_listing_validator_75_125():
    r = run(ROOT / "amazon-listing-writer/validate_listing.py", "--input", FX / "listing_new_rules.md")
    assert "合规检查结果: PASS" in r.stdout, r.stdout
    r2 = run(ROOT / "amazon-listing-writer/validate_listing.py", "--input", ROOT / "amazon-listing-writer/examples/sample_listing_output.md")
    assert "上限 75" in r2.stdout   # 旧样例 167 字符标题按新规应报错

def test_image_qc(tmp_path):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (2400, 2400), "white"); ImageDraw.Draw(im).ellipse((120, 120, 2280, 2280), fill=(70, 100, 150))
    p = tmp_path / "01_main.jpg"; im.save(p, quality=95)
    assert run(ROOT / "amazon-listing-image-prompts/write_ai_metadata.py", p).returncode == 0
    r = run(ROOT / "amazon-listing-image-prompts/image_qc.py", tmp_path, "--require-ai-meta", "--out", tmp_path / "qc")
    assert r.returncode == 0, r.stdout
    assert "trainedAlgorithmicMedia" in r.stdout
