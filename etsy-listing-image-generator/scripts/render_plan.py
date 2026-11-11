#!/usr/bin/env python3
"""把图片方案 image_plan.json 校验并渲染成交付总览（Markdown + 可选 HTML），供用户查看。
按 v3.3 五步流程和逐图验收规则检查方案。

用法：
  render_plan.py templates/image_plan.example.json [--md out.md] [--html out.html] [--strict]
方案校验（ERROR → 退出码 1）：
  - slots ≤ 20；slot 编号不重复
  - 每张图必须有 job（这张图回答买家哪个顾虑/完成哪个转化任务）、reason（为何选这个场景构图）、
    new_info（相对前面各张新增了什么信息）；job 不能与别的图重复（一张图只做一件事）
  - visible_proof：方案声称要展示的差异（镜像、尺寸差、白边/无白边等）必须写出"画面里怎么看得出来"
  - real_photo_slot（默认 3）必须 kind=reserved 或 real；reserved 位不得有 file（不传占位图）
  - kind=ai/edited 的图要有 source（用了哪张实拍/参考、改了什么）；plan.ai_disclosure 必须为 true
  - forbidden_poses 中的词（默认 3D hug / arms-out）不得出现在 prompt/job/alt
  - samples_gate：status 不是 approved/skipped_by_boss 时，只允许 slot 1 和 hardest_slot 有 file（先出 2 张样图）
  - 有 file 的图必须有 alt（≤250）；alt 要在终图出来后对着画面写
"""
import argparse, html, json, os, re, sys

def validate(P):
    E, W = [], []
    slots = P.get('slots', [])
    if len(slots) > 20: E.append(f'{len(slots)} slots > 20')
    nums = [s.get('slot') for s in slots]
    if len(set(nums)) != len(nums): E.append('duplicate slot numbers')
    rp = P.get('real_photo_slot', 3)
    forb = [f.lower() for f in P.get('forbidden_poses', ['3d hug', 'arms-out', 'arms out', 'open arms'])]
    jobs = {}
    gate = (P.get('samples_gate') or {}); gst = gate.get('status', 'pending')
    allowed = {1, gate.get('hardest_slot')} if gst not in ('approved', 'skipped_by_boss') else None
    for s in slots:
        n = s.get('slot'); k = s.get('kind')
        if n == rp:
            if k not in ('reserved', 'real'): E.append(f'slot {n:02d} must be reserved for the unedited real photo')
            if k == 'reserved' and s.get('file'): E.append(f'slot {n:02d}: reserved slot must stay empty (不要上传占位图)')
            continue
        for f in ('job', 'reason', 'new_info'):
            if not s.get(f): E.append(f'slot {n:02d}: missing {f}')
        j = (s.get('job') or '').strip().lower()
        if j in jobs: E.append(f'slot {n:02d}: same job as slot {jobs[j]:02d} (一张图只做一件事)')
        elif j: jobs[j] = n
        for claim in s.get('claims', []):
            if not (s.get('visible_proof') or {}).get(claim): E.append(f'slot {n:02d}: claim "{claim}" has no visible_proof (画面里看不出来就不算)')
        if k in ('ai', 'edited') and not s.get('source'): E.append(f'slot {n:02d}: AI/edited image without source note')
        text = ' '.join(str(s.get(x, '')) for x in ('prompt', 'job', 'alt')).lower()
        bad = [f for f in forb if f in text]
        if bad: E.append(f'slot {n:02d}: forbidden pose wording {bad}')
        if s.get('file'):
            alt = s.get('alt', '')
            if not alt: E.append(f'slot {n:02d}: file present but no alt')
            elif len(alt) > 250: E.append(f'slot {n:02d}: alt {len(alt)} > 250')
            if allowed is not None and n not in allowed: E.append(f'slot {n:02d}: samples gate {gst} — only slot 1 and hardest slot may be produced before approval')
        if s.get('mobile_check') not in (True, 'pass'): W.append(f'slot {n:02d}: mobile thumbnail check not recorded')
        if s.get('retries'): W.append(f'slot {n:02d}: redone {s["retries"]}x — {s.get("retry_reason", "reason missing")}')
    if any(s.get('kind') in ('ai', 'edited') for s in slots) and not P.get('ai_disclosure'): E.append('plan.ai_disclosure must be true (描述需含 AI 效果图说明)')
    if not P.get('product_facts'): W.append('product_facts missing (第 1 步：开工前先问齐)')
    if not P.get('buyer_concerns'): W.append('buyer_concerns missing (第 2 步：Reddit/差评/问答)')
    return E, W

def to_md(P, E, W):
    L = [f"# 图片方案总览：{P.get('product', '')}", '', f"- listing：{P.get('listing', '新建')}  |  站点：{P.get('market', 'US')}  |  单位：{P.get('units', 'inch/cm')}",
         f"- 样图闸门：{(P.get('samples_gate') or {}).get('status', 'pending')}（先出主图 + 最难的一张）", f"- 实拍位：{P.get('real_photo_slot', 3):02d}（老板上传未修图实拍）", '']
    if P.get('buyer_concerns'):
        L += ['## 买家顾虑（来源）', ''] + [f"- {c.get('concern')}（{c.get('source', '来源未写')}）→ 图 {c.get('answered_by', '?')}" for c in P['buyer_concerns']] + ['']
    L += ['## 逐图', '', '| # | 类型 | 任务（job） | 新增信息 | 画面证据 | 来源/改动 | alt 字数 |', '|---|---|---|---|---|---|---|']
    for s in P.get('slots', []):
        vp = '; '.join(f'{k}: {v}' for k, v in (s.get('visible_proof') or {}).items())
        L.append(f"| {s.get('slot'):02d} | {s.get('kind', '')} | {s.get('job', '—')} | {s.get('new_info', '')} | {vp} | {s.get('source', '')} | {len(s.get('alt', ''))} |")
    L += ['', '## 校验', ''] + [f'- ERROR {e}' for e in E] + [f'- WARN {w}' for w in W] + (['- PASS'] if not E else [])
    L += ['', '## Alt text（逐张复制）', '']
    for s in P.get('slots', []):
        if s.get('alt'): L += [f"第 {s['slot']} 张（{len(s['alt'])} 字符）", '```', s['alt'], '```']
    return '\n'.join(L) + '\n'

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('plan'); ap.add_argument('--md'); ap.add_argument('--html'); ap.add_argument('--strict', action='store_true')
    a = ap.parse_args(); P = json.load(open(a.plan)); E, W = validate(P)
    md = to_md(P, E, W)
    if a.md: open(a.md, 'w').write(md)
    if a.html:
        open(a.html, 'w').write('<!doctype html><meta charset=utf-8><style>body{font-family:sans-serif;max-width:1100px;margin:auto}pre{background:#f4f4f4;padding:8px}td,th{border:1px solid #ccc;padding:4px}</style><pre style="white-space:pre-wrap;background:none">' + html.escape(md) + '</pre>')
    print(md if not a.md else f'written {a.md}')
    for e in E: print('ERROR', e)
    for w in W: print('WARN', w)
    fail = bool(E) or (a.strict and bool(W))
    print('OVERALL:', 'FAIL' if fail else 'PASS'); sys.exit(1 if fail else 0)

if __name__ == '__main__':
    main()
