#!/usr/bin/env python3
"""YouTube 字幕/元信息抓取（box 版，替代 NotebookLM 的 source_add）
  python fetch_youtube_transcript.py <url> -o /tmp/yt.json
输出: {video_id,title,channel,duration,lang,transcript:[{start,text}],text}
优先人工字幕(zh/en)，其次自动字幕；都没有时 transcript 为空，Agent 需改用浏览器打开 NotebookLM 网页版。
"""
import argparse, json, re, subprocess, sys

def vid(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", url)
    return m.group(1) if m else url

def meta(url):
    try:
        out = subprocess.run([sys.executable, "-m", "yt_dlp", "-J", "--skip-download", "--no-warnings", url],
                             capture_output=True, text=True, timeout=90)
        d = json.loads(out.stdout)
        return {"title": d.get("title"), "channel": d.get("channel") or d.get("uploader"),
                "duration": d.get("duration"), "upload_date": d.get("upload_date")}
    except Exception as e:
        return {"title": None, "meta_error": str(e)[:200]}

def transcript(v):
    from youtube_transcript_api import YouTubeTranscriptApi
    api = YouTubeTranscriptApi()
    tl = api.list(v)
    langs = ["zh-Hans", "zh-CN", "zh", "zh-Hant", "zh-TW", "en", "en-US"]
    for finder in (tl.find_manually_created_transcript, tl.find_generated_transcript):
        try:
            t = finder(langs)
            return t.language_code, [{"start": round(s.start, 1), "text": s.text} for s in t.fetch()]
        except Exception:
            continue
    t = next(iter(tl))
    return t.language_code, [{"start": round(s.start, 1), "text": s.text} for s in t.fetch()]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("url"); ap.add_argument("-o", "--output", default="yt_transcript.json")
    ap.add_argument("--no-meta", action="store_true")
    a = ap.parse_args(); v = vid(a.url)
    res = {"video_id": v, "url": a.url}
    if not a.no_meta:
        res.update(meta(a.url))
    try:
        lang, segs = transcript(v); res.update(lang=lang, transcript=segs, text=" ".join(s["text"] for s in segs))
    except Exception as e:
        res.update(lang=None, transcript=[], text="", transcript_error=f"{type(e).__name__}: {str(e)[:300]}")
    json.dump(res, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{'✅' if res['text'] else '⚠️'} {res.get('title')} | lang={res.get('lang')} | {len(res['text'])} chars → {a.output}")
    if not res["text"]:
        print("   字幕获取失败:", res.get("transcript_error"))

if __name__ == "__main__":
    main()
