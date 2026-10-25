#!/usr/bin/env python3
"""
Listing-Skill HTML 可视化生成器 v2

用法:
    python3 render_listing_html.py --input <listing.md> [--output <output.html>]

功能:
    解析 listing_output.md 的全部 9 个模块（可复制区 + 分析参考区），
    生成一站式可视化展示页面（含一键复制按钮）。
"""

import argparse
import re
import sys
import html as html_module
from pathlib import Path


# ─── Extractors ───────────────────────────────────────────────────────────────

def extract_section(content, heading_pattern):
    pattern = rf"^##\s+.*{heading_pattern}.*$"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r'^##\s+', content[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end].strip()


def extract_title(content):
    section = extract_section(content, r"Title|标题")
    for line in section.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('**') or line.startswith('---') or line.startswith('|') or line.startswith('>'):
            continue
        clean = re.sub(r'[`]', '', line)
        if len(clean) > 20:
            return clean
    return ""


def extract_bullet_points(content):
    section = extract_section(content, r"Bullet|五点")
    bullets, current = [], ""
    for line in section.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('**') or line.startswith('---'):
            if current:
                bullets.append(current)
                current = ""
            continue
        if line.startswith('[') and current:
            bullets.append(current)
            current = line
        elif line.startswith('['):
            current = line
        else:
            current += " " + line if current else line
    if current:
        bullets.append(current)
    return [b for b in bullets if len(b) > 50]


def extract_description(content):
    section = extract_section(content, r"Description|产品描述")
    lines, in_html = [], False
    for line in section.split('\n'):
        stripped = line.strip()
        if stripped.startswith('<'):
            in_html = True
        if in_html:
            if stripped.startswith('---'):
                break
            lines.append(line)
    return '\n'.join(lines).strip()


def extract_search_terms(content):
    section = extract_section(content, r"Search Terms|搜索词")
    for line in section.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('**') or line.startswith('|') or line.startswith('```') or line.startswith('---') or line.startswith('>'):
            continue
        clean = re.sub(r'[`]', '', line)
        if len(clean) > 10 and not clean.startswith('字节'):
            return clean
    return ""


def extract_product_name(content):
    match = re.search(r'产品关键词[：:]\s*(.+)', content)
    if match:
        return match.group(1).strip()
    match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    return match.group(1).strip() if match else "Amazon Listing"


def extract_main_image_prompt(content):
    section = extract_section(content, r"主图设计|Main Image")
    if not section:
        return {}
    result = {}
    comp_match = re.search(r'\*\*构图\*\*[：:]\s*(.+)', section)
    if comp_match:
        result['composition'] = comp_match.group(1).strip()
    prompt_match = re.search(r'>\s*(.+(?:\n>\s*.+)*)', section)
    if prompt_match:
        prompt_lines = prompt_match.group(0).split('\n')
        result['prompt'] = ' '.join(line.lstrip('> ').strip() for line in prompt_lines if line.strip())
    if 'prompt' not in result:
        lines = section.split('\n')
        capture_next = False
        for line in lines:
            if 'AI' in line and '提示词' in line:
                capture_next = True
                continue
            if capture_next and line.strip():
                result['prompt'] = line.strip().lstrip('> ').strip()
                break
    return result


def extract_secondary_image_prompts(content):
    section = extract_section(content, r"副图设计|Secondary Image")
    if not section:
        return []
    images = []
    for line in section.split('\n'):
        line = line.strip()
        if not line.startswith('|') or line.startswith('|---') or line.startswith('| 图序') or line.startswith('| #'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) >= 3:
            images.append({'index': cells[0], 'type': cells[1], 'prompt': cells[2]})
    return images


def extract_aplus_prompt(content):
    section = extract_section(content, r"A\+\s*内容|A\+\s*Content")
    if not section:
        return {}
    result = {}
    style_match = re.search(r'\*\*风格\*\*[：:]\s*(.+)', section)
    if style_match:
        result['style'] = style_match.group(1).strip()
    modules = []
    for line in section.split('\n'):
        m = re.match(r'^\d+\.\s+(.+)', line.strip())
        if m:
            modules.append(m.group(1).strip())
    if modules:
        result['modules'] = modules
    return result


def extract_video_script(content):
    section = extract_section(content, r"视频脚本|Video Script")
    if not section:
        return {}
    result = {}
    dur_match = re.search(r'\*\*时长\*\*[：:]\s*(.+)', section)
    if dur_match:
        result['duration'] = dur_match.group(1).strip()
    rows = []
    for line in section.split('\n'):
        line = line.strip()
        if not line.startswith('|') or line.startswith('|---') or line.startswith('| 时间') or line.startswith('| Time'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) >= 4:
            rows.append({'time': cells[0], 'visual': cells[1], 'text': cells[2], 'action': cells[3]})
    if rows:
        result['scenes'] = rows
    return result


def extract_strategy_brief(content):
    return extract_section(content, r"策略分析简报|Strategy Brief")


# ─── HTML Section Builders ────────────────────────────────────────────────────

def h(s):
    return html_module.escape(str(s))


def js_escape(s):
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')


COPY_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>'
COPY_SVG_SM = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>'


def build_strategy_section(strategy_brief):
    if not strategy_brief:
        return ""
    body = ""
    for line in strategy_brief.split('\n'):
        s = line.strip()
        if s.startswith('### '):
            body += '<h4 class="strat-h4">' + h(s[4:]) + '</h4>\n'
        elif s.startswith('- '):
            body += '<div class="strat-item">• ' + h(s[2:]) + '</div>\n'
        elif s.startswith('| ') and not s.startswith('|---') and not s.startswith('| #'):
            cells = [c.strip() for c in s.split('|')[1:-1]]
            body += '<div class="strat-row">' + ' — '.join(h(c) for c in cells if c) + '</div>\n'
        elif s:
            body += '<div class="strat-line">' + h(s) + '</div>\n'

    return (
        '<div class="section">\n'
        '  <div class="section-title ref-section">策略分析简报 Strategy Brief</div>\n'
        '  <div class="card ref-card">\n'
        '    <div class="strat-toggle" onclick="toggleStrategy(this)">\n'
        '      <span class="arrow">▶</span>\n'
        '      <span class="card-label ref-label">策略简报（点击展开）</span>\n'
        '    </div>\n'
        '    <div class="strat-body">' + body + '</div>\n'
        '  </div>\n'
        '</div>\n'
    )


def build_main_image_section(main_image):
    if not main_image:
        return ""
    comp_html = ""
    if main_image.get('composition'):
        comp_html = '<div class="comp-line"><strong>构图：</strong>' + h(main_image['composition']) + '</div>'
    prompt = h(main_image.get('prompt', ''))
    return (
        '<div class="section">\n'
        '  <div class="section-title ref-section">主图设计 Prompt — Main Image</div>\n'
        '  <div class="card ref-card">\n'
        '    <div class="card-header">\n'
        '      <span class="card-label ref-label">Main Image Prompt</span>\n'
        '      <button class="copy-btn" onclick="copyText(this, \'main-img-prompt\')">' + COPY_SVG + ' 复制 Prompt</button>\n'
        '    </div>\n'
        '    ' + comp_html + '\n'
        '    <div class="card-body prompt-body" id="main-img-prompt">' + prompt + '</div>\n'
        '  </div>\n'
        '</div>\n'
    )


def build_secondary_images_section(secondary_images):
    if not secondary_images:
        return ""
    rows = ""
    for img in secondary_images:
        idx = h(img['index'])
        rows += (
            '<tr>'
            '<td class="cell-index">' + idx + '</td>'
            '<td class="cell-type">' + h(img['type']) + '</td>'
            '<td class="cell-prompt" id="sec-img-' + idx + '">' + h(img['prompt']) + '</td>'
            '<td class="cell-action"><button class="copy-btn" onclick="copyText(this, \'sec-img-' + idx + '\')">' + COPY_SVG_SM + '</button></td>'
            '</tr>\n'
        )
    return (
        '<div class="section">\n'
        '  <div class="section-title ref-section">副图设计 Prompt — Secondary Images (×' + str(len(secondary_images)) + ')</div>\n'
        '  <div class="card ref-card">\n'
        '    <div class="card-header">\n'
        '      <span class="card-label ref-label">Secondary Image Prompts</span>\n'
        '      <button class="copy-btn" onclick="copyAllSecondaryPrompts()">' + COPY_SVG + ' 复制全部</button>\n'
        '    </div>\n'
        '    <div style="overflow-x: auto;">\n'
        '      <table class="prompt-table">\n'
        '        <thead><tr><th>#</th><th>类型</th><th>AI Prompt</th><th></th></tr></thead>\n'
        '        <tbody>' + rows + '</tbody>\n'
        '      </table>\n'
        '    </div>\n'
        '  </div>\n'
        '</div>\n'
    )


def build_aplus_section(aplus):
    if not aplus:
        return ""
    style_html = ""
    if aplus.get('style'):
        style_html = '<div class="comp-line"><strong>风格：</strong>' + h(aplus['style']) + '</div>'
    modules_html = ""
    for j, mod in enumerate(aplus.get('modules', []), 1):
        modules_html += (
            '<div class="aplus-module">'
            '<span class="module-num">' + str(j) + '</span> '
            + h(mod) +
            '</div>\n'
        )
    return (
        '<div class="section">\n'
        '  <div class="section-title ref-section">A+ 内容设计 — Enhanced Brand Content</div>\n'
        '  <div class="card ref-card">\n'
        '    <div class="card-header">\n'
        '      <span class="card-label ref-label">A+ Content Design</span>\n'
        '      <button class="copy-btn" onclick="copyAplusAll()">' + COPY_SVG + ' 复制全部</button>\n'
        '    </div>\n'
        '    ' + style_html + '\n'
        '    <div id="aplus-content" style="padding: 0.5rem 0;">\n'
        '      ' + modules_html + '\n'
        '    </div>\n'
        '  </div>\n'
        '</div>\n'
    )


def build_video_section(video_script):
    if not video_script:
        return ""
    dur = video_script.get('duration', '')
    dur_label = ' (' + h(dur) + ')' if dur else ''
    rows = ""
    for scene in video_script.get('scenes', []):
        rows += (
            '<tr>'
            '<td class="cell-time">' + h(scene['time']) + '</td>'
            '<td>' + h(scene['visual']) + '</td>'
            '<td class="cell-text">「' + h(scene['text']) + '」</td>'
            '<td>' + h(scene['action']) + '</td>'
            '</tr>\n'
        )
    return (
        '<div class="section">\n'
        '  <div class="section-title ref-section">视频脚本 — Video Script' + dur_label + '</div>\n'
        '  <div class="card ref-card">\n'
        '    <div class="card-header">\n'
        '      <span class="card-label ref-label">Video Script</span>\n'
        '      <button class="copy-btn" onclick="copyVideoScript()">' + COPY_SVG + ' 复制全部</button>\n'
        '    </div>\n'
        '    <div style="overflow-x: auto;">\n'
        '      <table class="prompt-table">\n'
        '        <thead><tr><th>时间</th><th>画面</th><th>文字</th><th>动作</th></tr></thead>\n'
        '        <tbody>' + rows + '</tbody>\n'
        '      </table>\n'
        '    </div>\n'
        '  </div>\n'
        '</div>\n'
    )


# ─── Main HTML Generator ─────────────────────────────────────────────────────

def generate_html(title, bullets, description, search_terms, product_name,
                  main_image, secondary_images, aplus, video_script, strategy_brief):

    # Bullet cards
    bullet_cards = ""
    for i, bp in enumerate(bullets, 1):
        bullet_cards += (
            '<div class="card">'
            '<div class="card-header">'
            '<span class="card-label copy-label">Bullet Point ' + str(i) + '</span>'
            '<button class="copy-btn" onclick="copyText(this, \'bp' + str(i) + '\')">' + COPY_SVG + ' 复制</button>'
            '</div>'
            '<div class="card-body" id="bp' + str(i) + '">' + h(bp) + '</div>'
            '</div>\n'
        )

    title_chars = len(title)
    st_bytes = len(search_terms.encode('utf-8'))
    title_status = 'pass' if title_chars <= 200 else 'warning'
    st_status = 'pass' if st_bytes <= 249 else 'warning'

    # Reference zone sections
    ref_sections = (
        build_strategy_section(strategy_brief)
        + build_main_image_section(main_image)
        + build_secondary_images_section(secondary_images)
        + build_aplus_section(aplus)
        + build_video_section(video_script)
    )
    has_ref = bool(ref_sections.strip())

    ref_zone = ""
    if has_ref:
        ref_zone = (
            '<div id="zone-ref">\n'
            '  <div class="zone-divider ref-zone">📊 分析参考区 — Internal Reference</div>\n'
            + ref_sections +
            '</div>\n'
        )

    desc_escaped = h(description)

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Amazon Listing — ''' + h(product_name) + '''</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg-primary: #0f1117; --bg-card: #1a1d27; --bg-card-hover: #22253a;
      --border: #2a2d3e; --text-primary: #e8eaed; --text-secondary: #9aa0b0;
      --accent: #6c63ff; --accent-light: #8b83ff; --accent-glow: rgba(108,99,255,0.15);
      --success: #34d399; --warning: #fbbf24;
      --tag-bg: rgba(108,99,255,0.12); --tag-text: #a5a0ff;
      --orange: #f97316; --orange-bg: rgba(249,115,22,0.10); --orange-border: rgba(249,115,22,0.30);
      --cyan: #22d3ee; --pink: #e879f9;
    }
    body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; min-height: 100vh; }
    .container { max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
    .header { text-align: center; padding: 3rem 0 1.5rem; margin-bottom: 1.5rem; }
    .header h1 { font-size: 1.75rem; font-weight: 700; background: linear-gradient(135deg, var(--accent-light), var(--pink)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
    .header .subtitle { color: var(--text-secondary); font-size: 0.9rem; }
    .zone-nav { display: flex; gap: 0.5rem; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
    .zone-btn { padding: 0.5rem 1.2rem; font-size: 0.8rem; font-weight: 600; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-secondary); transition: all 0.2s; font-family: inherit; }
    .zone-btn:hover { border-color: var(--accent); color: var(--accent-light); }
    .zone-btn.active { background: var(--accent-glow); border-color: var(--accent); color: var(--accent-light); }
    .zone-divider { display: flex; align-items: center; gap: 1rem; margin: 2.5rem 0 1.5rem; color: var(--text-secondary); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }
    .zone-divider::before, .zone-divider::after { content: ''; flex: 1; height: 1px; }
    .zone-divider.copy-zone::before, .zone-divider.copy-zone::after { background: linear-gradient(90deg, transparent, var(--accent), transparent); }
    .zone-divider.ref-zone::before, .zone-divider.ref-zone::after { background: linear-gradient(90deg, transparent, var(--orange), transparent); }
    .section { margin-bottom: 2rem; }
    .section-title { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-secondary); margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }
    .section-title::before { content: ''; width: 3px; height: 14px; border-radius: 2px; }
    .section-title.copy-section::before { background: var(--accent); }
    .section-title.ref-section::before { background: var(--orange); }
    .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; margin-bottom: 0.75rem; transition: border-color 0.2s, box-shadow 0.2s; }
    .card:hover { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent-glow), 0 4px 24px rgba(0,0,0,0.3); }
    .card.ref-card:hover { border-color: var(--orange); box-shadow: 0 0 0 1px var(--orange-bg), 0 4px 24px rgba(0,0,0,0.3); }
    .card-header { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 1rem; background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border); }
    .card-label { font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 6px; }
    .card-label.copy-label { color: var(--tag-text); background: var(--tag-bg); }
    .card-label.ref-label { color: var(--orange); background: var(--orange-bg); }
    .card-body { padding: 1rem 1.25rem; font-size: 0.92rem; line-height: 1.7; color: var(--text-primary); }
    .card-body.description-html { font-family: 'Courier New', monospace; font-size: 0.82rem; white-space: pre-wrap; word-break: break-all; color: #c9d1d9; background: #161b22; border-radius: 0 0 12px 12px; }
    .card-body.description-preview { padding: 1.25rem; }
    .card-body.description-preview h2 { font-size: 1.05rem; margin: 1rem 0 0.4rem; color: var(--accent-light); }
    .card-body.description-preview h2:first-child { margin-top: 0; }
    .card-body.description-preview p { margin-bottom: 0.6rem; }
    .card-body.description-preview ul { padding-left: 1.2rem; margin-bottom: 0.6rem; }
    .card-body.description-preview li { margin-bottom: 0.3rem; }
    .card-body.prompt-body { font-family: 'Courier New', monospace; font-size: 0.85rem; line-height: 1.8; color: #c9d1d9; background: #161b22; border-radius: 0 0 12px 12px; white-space: pre-wrap; }
    .copy-btn { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0.7rem; font-size: 0.72rem; font-weight: 500; color: var(--text-secondary); background: transparent; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
    .copy-btn:hover { color: var(--accent-light); border-color: var(--accent); background: var(--accent-glow); }
    .copy-btn.copied { color: var(--success); border-color: var(--success); background: rgba(52,211,153,0.1); }
    .stats { display: flex; gap: 1rem; margin-top: 0.5rem; flex-wrap: wrap; }
    .stat { font-size: 0.75rem; color: var(--text-secondary); background: var(--bg-card); border: 1px solid var(--border); padding: 0.35rem 0.75rem; border-radius: 8px; }
    .stat .value { font-weight: 600; }
    .stat.pass .value { color: var(--success); }
    .stat.warning .value { color: var(--warning); }
    .tabs { display: flex; gap: 0; margin-bottom: 0; }
    .tab { padding: 0.5rem 1rem; font-size: 0.75rem; font-weight: 500; color: var(--text-secondary); background: var(--bg-card); border: 1px solid var(--border); border-bottom: none; border-radius: 8px 8px 0 0; cursor: pointer; transition: all 0.2s; }
    .tab.active { color: var(--accent-light); background: var(--bg-card-hover); border-color: var(--accent); }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .desc-card { border-radius: 0 12px 12px 12px; margin-bottom: 0.75rem; }
    .prompt-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    .prompt-table th { text-align: left; padding: 0.6rem 0.8rem; font-weight: 600; color: var(--text-secondary); border-bottom: 1px solid var(--border); background: rgba(255,255,255,0.02); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .prompt-table td { padding: 0.6rem 0.8rem; border-bottom: 1px solid rgba(42,45,62,0.5); color: var(--text-primary); vertical-align: top; }
    .prompt-table tr:last-child td { border-bottom: none; }
    .prompt-table tr:hover td { background: rgba(108,99,255,0.04); }
    .cell-index { width: 40px; color: var(--accent-light); font-weight: 600; }
    .cell-type { width: 120px; color: var(--cyan); font-weight: 500; }
    .cell-prompt { font-family: 'Courier New', monospace; font-size: 0.8rem; color: #c9d1d9; }
    .cell-action { width: 40px; text-align: center; }
    .cell-time { width: 60px; color: var(--orange); font-weight: 600; font-family: monospace; }
    .cell-text { color: var(--pink); font-style: italic; }
    .aplus-module { padding: 0.6rem 1rem; border-bottom: 1px solid rgba(42,45,62,0.5); display: flex; align-items: flex-start; gap: 0.6rem; }
    .aplus-module:last-child { border-bottom: none; }
    .module-num { min-width: 22px; height: 22px; border-radius: 50%; background: var(--orange-bg); border: 1px solid var(--orange-border); color: var(--orange); font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .strat-toggle { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; padding: 0.8rem 1rem; background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border); }
    .strat-toggle .arrow { transition: transform 0.2s; color: var(--text-secondary); }
    .strat-toggle.open .arrow { transform: rotate(90deg); }
    .strat-body { display: none; padding: 1rem 1.25rem; }
    .strat-body.open { display: block; }
    .strat-h4 { color: var(--accent-light); font-size: 0.85rem; margin: 0.8rem 0 0.4rem; }
    .strat-h4:first-child { margin-top: 0; }
    .strat-item { padding: 0.15rem 0 0.15rem 0.5rem; font-size: 0.85rem; color: var(--text-primary); }
    .strat-row { padding: 0.15rem 0; font-size: 0.82rem; color: var(--text-secondary); }
    .strat-line { padding: 0.15rem 0; font-size: 0.85rem; }
    .comp-line { padding: 0.6rem 1rem; border-bottom: 1px solid var(--border); font-size: 0.82rem; color: var(--text-secondary); background: rgba(255,255,255,0.02); }
    .comp-line strong { color: var(--cyan); }
    .footer { text-align: center; padding-top: 2rem; border-top: 1px solid var(--border); margin-top: 2rem; color: var(--text-secondary); font-size: 0.75rem; }
    @media (max-width: 640px) { .container { padding: 1rem; } .header h1 { font-size: 1.3rem; } .stats { flex-direction: column; } .zone-nav { flex-wrap: wrap; } }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📋 Amazon Listing 全览</h1>
      <div class="subtitle">''' + h(product_name) + '''</div>
    </div>
    <div class="zone-nav">
      <button class="zone-btn active" onclick="scrollToZone('zone-copy')">📋 可复制区</button>
      <button class="zone-btn" onclick="scrollToZone('zone-ref')">📊 分析参考区</button>
    </div>

    <div id="zone-copy">
      <div class="zone-divider copy-zone">📋 可复制区 — Platform-Ready</div>

      <div class="section">
        <div class="section-title copy-section">标题 Title</div>
        <div class="card">
          <div class="card-header">
            <span class="card-label copy-label">Title</span>
            <button class="copy-btn" onclick="copyText(this, 'title-text')">''' + COPY_SVG + ''' 复制</button>
          </div>
          <div class="card-body" id="title-text">''' + h(title) + '''</div>
        </div>
        <div class="stats">
          <div class="stat ''' + title_status + '''">字符数: <span class="value">''' + str(title_chars) + '''</span> / 200</div>
        </div>
      </div>

      <div class="section">
        <div class="section-title copy-section">五点描述 Bullet Points</div>
        ''' + bullet_cards + '''
        <div style="margin-top: 0.5rem;">
          <button class="copy-btn" onclick="copyAllBullets()">''' + COPY_SVG + ''' 复制全部五点</button>
        </div>
      </div>

      <div class="section">
        <div class="section-title copy-section">产品描述 Product Description</div>
        <div class="tabs">
          <div class="tab active" onclick="switchTab('preview')">预览</div>
          <div class="tab" onclick="switchTab('source')">HTML 源码</div>
        </div>
        <div class="card desc-card">
          <div class="card-header">
            <span class="card-label copy-label">Description (HTML)</span>
            <button class="copy-btn" onclick="copyDescription(this)">''' + COPY_SVG + ''' 复制 HTML</button>
          </div>
          <div id="tab-preview" class="tab-content active">
            <div class="card-body description-preview">''' + description + '''</div>
          </div>
          <div id="tab-source" class="tab-content">
            <div class="card-body description-html">''' + desc_escaped + '''</div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title copy-section">后台搜索词 Search Terms</div>
        <div class="card">
          <div class="card-header">
            <span class="card-label copy-label">Search Terms</span>
            <button class="copy-btn" onclick="copyText(this, 'st-text')">''' + COPY_SVG + ''' 复制</button>
          </div>
          <div class="card-body" id="st-text">''' + h(search_terms) + '''</div>
        </div>
        <div class="stats">
          <div class="stat ''' + st_status + '''">字节数: <span class="value">''' + str(st_bytes) + '''</span> / 249</div>
        </div>
      </div>
    </div>

    ''' + ref_zone + '''

    <div class="footer">Listing-Skill v2 · Generated by render_listing_html.py</div>
  </div>

  <script>
    const descriptionHtml = \'''' + js_escape(description) + '''\';

    function copyText(btn, elementId) {
      const text = document.getElementById(elementId).innerText;
      navigator.clipboard.writeText(text).then(() => showCopied(btn, '已复制'));
    }
    function copyDescription(btn) {
      navigator.clipboard.writeText(descriptionHtml).then(() => showCopied(btn, '已复制'));
    }
    function copyAllBullets() {
      const bullets = [];
      for (let i = 1; i <= 10; i++) {
        const el = document.getElementById('bp' + i);
        if (el) bullets.push(el.innerText);
      }
      const btn = event.currentTarget;
      navigator.clipboard.writeText(bullets.join('\\n\\n')).then(() => showCopied(btn, '已复制全部'));
    }
    function copyAllSecondaryPrompts() {
      const rows = document.querySelectorAll('[id^="sec-img-"]');
      const prompts = [];
      rows.forEach(r => prompts.push(r.innerText));
      const btn = event.currentTarget;
      navigator.clipboard.writeText(prompts.join('\\n\\n')).then(() => showCopied(btn, '已复制全部'));
    }
    function copyAplusAll() {
      const el = document.getElementById('aplus-content');
      const btn = event.currentTarget;
      navigator.clipboard.writeText(el.innerText).then(() => showCopied(btn, '已复制'));
    }
    function copyVideoScript() {
      const table = document.querySelector('#zone-ref .prompt-table:last-of-type');
      const rows = document.querySelectorAll('#zone-ref .section:last-child .prompt-table tbody tr');
      const lines = [];
      rows.forEach(r => {
        const cells = r.querySelectorAll('td');
        if (cells.length >= 4) lines.push(cells[0].innerText + ' | ' + cells[1].innerText + ' | ' + cells[2].innerText + ' | ' + cells[3].innerText);
      });
      const btn = event.currentTarget;
      navigator.clipboard.writeText(lines.join('\\n')).then(() => showCopied(btn, '已复制'));
    }
    function showCopied(btn, msg) {
      btn.classList.add('copied');
      const orig = btn.innerHTML;
      btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> ' + msg;
      setTimeout(() => { btn.classList.remove('copied'); btn.innerHTML = orig; }, 2000);
    }
    function switchTab(tab) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      if (tab === 'preview') {
        document.querySelectorAll('.tab')[0].classList.add('active');
        document.getElementById('tab-preview').classList.add('active');
      } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('tab-source').classList.add('active');
      }
    }
    function scrollToZone(id) {
      document.querySelectorAll('.zone-btn').forEach(b => b.classList.remove('active'));
      event.currentTarget.classList.add('active');
      document.getElementById(id).scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    function toggleStrategy(el) {
      el.classList.toggle('open');
      el.nextElementSibling.classList.toggle('open');
    }
  </script>
</body>
</html>'''
    return html


def main():
    parser = argparse.ArgumentParser(description="Listing HTML 可视化生成器 v2")
    parser.add_argument("--input", required=True, help="listing_output.md 文件路径")
    parser.add_argument("--output", help="输出 HTML 文件路径（默认同目录下 listing_visual.html）")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)

    content = input_path.read_text(encoding='utf-8')

    title = extract_title(content)
    bullets = extract_bullet_points(content)
    description = extract_description(content)
    search_terms = extract_search_terms(content)
    product_name = extract_product_name(content)
    main_image = extract_main_image_prompt(content)
    secondary_images = extract_secondary_image_prompts(content)
    aplus = extract_aplus_prompt(content)
    video_script = extract_video_script(content)
    strategy_brief = extract_strategy_brief(content)

    modules = [
        ("标题", bool(title)), ("五点描述", bool(bullets)),
        ("产品描述", bool(description)), ("搜索词", bool(search_terms)),
        ("主图 Prompt", bool(main_image)), ("副图 Prompt", bool(secondary_images)),
        ("A+ Prompt", bool(aplus)), ("视频脚本", bool(video_script)),
        ("策略简报", bool(strategy_brief)),
    ]
    for name, found in modules:
        print(f"  {'✅' if found else '⚠️ 未找到'} {name}")

    html_content = generate_html(
        title, bullets, description, search_terms, product_name,
        main_image, secondary_images, aplus, video_script, strategy_brief
    )

    output_path = Path(args.output) if args.output else input_path.parent / "listing_visual.html"
    output_path.write_text(html_content, encoding='utf-8')

    print(f"\n✅ HTML 可视化页面已生成: {output_path}")
    print(f"   标题: {len(title)} 字符 | 五点: {len(bullets)} 条 | 搜索词: {len(search_terms.encode('utf-8'))} bytes")
    print(f"   副图: {len(secondary_images)} 张 | 视频场景: {len(video_script.get('scenes', []))} 个")


if __name__ == "__main__":
    main()
