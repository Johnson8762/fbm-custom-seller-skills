#!/usr/bin/env python3
"""write_ai_metadata.py —— 给 AI 生成的 JPG 写入 AI 元数据。
写入 XMP：Iptc4xmpExt:DigitalSourceType = http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia，
dc:description / photoshop:Credit = "AI-generated"，xmp:Label = DRAFT（可 --label 改）。使用 Pillow 的 xmp 参数。
用法：python write_ai_metadata.py <in.jpg> [<out.jpg>] [--label DRAFT]  （不给 out 则原地覆盖）
注意：亚马逊上传后可能剥离元数据。
"""
import argparse
from PIL import Image
XMP = """<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'><rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
<rdf:Description rdf:about='' xmlns:Iptc4xmpExt='http://iptc.org/std/Iptc4xmpExt/2008-02-29/' xmlns:dc='http://purl.org/dc/elements/1.1/'
 xmlns:photoshop='http://ns.adobe.com/photoshop/1.0/' xmlns:xmp='http://ns.adobe.com/xap/1.0/'
 Iptc4xmpExt:DigitalSourceType='http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia'
 photoshop:Credit='AI-generated' xmp:Label='{label}'>
<dc:description><rdf:Alt><rdf:li xml:lang='x-default'>AI-generated image{extra}</rdf:li></rdf:Alt></dc:description>
</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end='w'?>"""
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst", nargs="?"); ap.add_argument("--label", default="DRAFT"); ap.add_argument("--desc", default="")
a = ap.parse_args(); im = Image.open(a.src)
xmp = XMP.format(label=a.label, extra=(" - " + a.desc) if a.desc else "").encode("utf-8")
im.convert("RGB").save(a.dst or a.src, "JPEG", quality=95, xmp=xmp, exif=im.info.get("exif", b""))
print("written", a.dst or a.src)
