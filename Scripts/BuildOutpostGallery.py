"""Build an offline, unretouched screenshot gallery beside a capture manifest.

Usage: python Scripts/BuildOutpostGallery.py path/to/manifest.json
Only index.html is written. Referenced PNG bytes are never modified or copied.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path, PureWindowsPath
import re
import struct
from urllib.parse import quote

GROUPS = (
    ('Exterior', 'Arrival & exterior'), ('PlayerPad', 'Your ship & landing pad'),
    ('Market', 'Market promenade'), ('Atrium', 'Planetary atrium'),
    ('Engineering', 'Flight engineering'), ('Lounge', 'Crew lounge'),
    ('Operations', 'Operations'), ('Gallery', 'Observation gallery'),
    ('Cockpit', 'Ship interior & cockpit'), ('VisitorBerths', 'Visitor berths'),
)
ALIASES = {'FlightEngineering': 'Engineering', 'ObservationGallery': 'Gallery',
           'Visitors': 'VisitorBerths',
           'PlanetaryArchive': 'Atrium', 'MarketPromenade': 'Market',
           'MarketMiniKits': 'Market', 'WardrobeLounge': 'Lounge',
           'ArcadeConversation': 'Lounge', 'ExteriorArrival': 'Exterior'}


def escape(value):
    return html.escape(str(value), quote=True)


def caption(name):
    text = re.sub(r'^\d+[ _.-]*', '', str(name))
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
    return re.sub(r'[ _-]+', ' ', text).strip() or 'View'


def group_for(name):
    compact = re.sub(r'[^a-zA-Z]', '', re.sub(r'^\d+[ _.-]*', '', str(name)))
    for key, _ in GROUPS:
        if compact.lower().startswith(key.lower()):
            return key
    for alias, key in ALIASES.items():
        if compact.lower().startswith(alias.lower()):
            return key
    return 'Other'


def read_images(manifest):
    manifest = Path(manifest).resolve(strict=True)
    report = json.loads(manifest.read_text(encoding='utf-8-sig'))
    folder, images = manifest.parent, []
    for row in report.get('images', []):
        name, raw = str(row.get('name', 'View')), str(row.get('png', ''))
        if not raw or '://' in raw:
            raise ValueError('Expected a local PNG for ' + name)
        path = Path(raw)
        path = path if path.is_absolute() else folder / path
        # Relocated capture folders retain old absolute paths. Keep the page
        # portable by accepting only PNGs within its own capture directory.
        try:
            path = path.resolve(strict=True)
            relative = path.relative_to(folder)
        except (OSError, ValueError):
            path = (folder / PureWindowsPath(raw).name).resolve(strict=True)
            relative = path.relative_to(folder)
        if path.suffix.lower() != '.png':
            raise ValueError('Only raw PNG captures are supported: ' + name)
        data = path.read_bytes()
        if len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
            raise ValueError('Invalid PNG capture: ' + name)
        width, height = struct.unpack('>II', data[16:24])
        if width < 1 or height < 1:
            raise ValueError('Invalid PNG dimensions: ' + name)
        if row.get('sha256') and hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Capture hash does not match its manifest: ' + name)
        images.append(dict(name=name, caption=caption(name), group=group_for(name),
                           url=quote(relative.as_posix(), safe='/'), width=width, height=height))
    if not images:
        raise ValueError('The manifest has no captured images yet.')
    return manifest, report, images


def render(manifest, report, images, title='Wayfarer Exchange — station walkthrough'):
    groups = [(key, label) for key, label in GROUPS if any(i['group'] == key for i in images)]
    if any(i['group'] == 'Other' for i in images):
        groups.append(('Other', 'More views'))
    nav, sections, index = [], [], 0
    for key, label in groups:
        rows = [i for i in images if i['group'] == key]
        anchor = key.lower()
        nav.append(f'<a href="#{anchor}">{escape(label)} <span>{len(rows)}</span></a>')
        cards = []
        for item in rows:
            cards.append(f'''<figure class="card"><a class="shot" href="{item['url']}"
 data-index="{index}" data-caption="{escape(item['caption'])}" data-area="{escape(label)}"
 aria-label="Enlarge {escape(item['caption'])}"><img src="{item['url']}"
 width="{item['width']}" height="{item['height']}" loading="lazy" decoding="async"
 alt="{escape(item['caption'])}" /></a><figcaption><h3>{escape(item['caption'])}</h3>
 <p>{item['width']} × {item['height']} · original PNG</p></figcaption></figure>''')
            index += 1
        sections.append(f'<section id="{anchor}" aria-labelledby="heading-{anchor}"><div class="section-heading">'
                        f'<h2 id="heading-{anchor}">{escape(label)}</h2><a href="#top">Back to top ↑</a>'
                        f'</div><div class="grid">{"".join(cards)}</div></section>')
    notes, warning = report.get('errors', []), ''
    if notes or report.get('status') == 'FAILED':
        warning = '<aside class="notice"><strong>Capture run needs attention.</strong> '
        warning += 'These images remain available for visual review; the capture manifest reports a failed or incomplete check.'
        if notes:
            warning += '<details><summary>Capture notes</summary><ul>'
            warning += ''.join('<li>' + escape(note) + '</li>' for note in notes)
            warning += '</ul></details>'
        warning += '</aside>'
    date = str(report.get('started_utc', report.get('run_id', '')))
    return HTML.replace('__TITLE__', escape(title)).replace('__COUNT__', str(len(images))).replace(
        '__DATE__', escape(date)).replace('__NAV__', ''.join(nav)).replace('__SECTIONS__', ''.join(sections)).replace(
        '__WARNING__', warning).replace('__MANIFEST__', quote(Path(manifest).name, safe=''))


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>__TITLE__</title>
<style>
:root{color-scheme:dark;--bg:#090f19;--panel:#141e2d;--text:#e7edf4;--muted:#a5b6c9;--line:#304359;--accent:#75d8e8}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:1.2rem}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,Segoe UI,sans-serif}
a{color:var(--accent)}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:5px}button{font:inherit;cursor:pointer}
main{max-width:1760px;margin:auto;padding:38px clamp(18px,4vw,64px) 70px}.eyebrow{color:var(--accent);font-size:.78rem;letter-spacing:.16em;text-transform:uppercase}h1{font-size:clamp(1.9rem,4vw,3rem);line-height:1.18;max-width:1000px;margin:12px 0 18px}h2{font-size:1.5rem;margin:0}h3{font-size:1rem;margin:0;font-weight:600}.intro{color:var(--muted);max-width:800px}.meta{font-size:.82rem;color:var(--muted)}nav{display:flex;flex-wrap:wrap;gap:9px;margin:28px 0 34px}nav a{border:1px solid var(--line);padding:8px 13px;border-radius:8px;text-decoration:none;background:var(--panel)}nav span{color:var(--muted);font-size:.8em;margin-left:6px}nav a:hover{border-color:var(--accent)}section{margin:38px 0 50px}.section-heading{display:flex;gap:20px;align-items:baseline;justify-content:space-between;margin-bottom:18px}.section-heading>a{font-size:.8rem;white-space:nowrap}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.card{margin:0;overflow:hidden;border:1px solid var(--line);border-radius:12px;background:var(--panel)}.shot{display:block;background:#000;line-height:0}.shot img{display:block;width:100%;height:auto}.shot:hover{outline:2px solid var(--accent);outline-offset:-2px}figcaption{padding:15px 18px}figcaption p{font-size:.78rem;color:var(--muted);margin:6px 0 0}.notice{border:1px solid #b79358;padding:15px 20px;border-radius:8px;color:#ead6b4}details{margin-top:8px}details li{white-space:pre-wrap;overflow-wrap:anywhere}footer{color:var(--muted);font-size:.82rem;border-top:1px solid var(--line);padding-top:24px}
dialog{width:98vw;height:96dvh;max-width:98vw;max-height:96dvh;padding:0;border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--text)}dialog::backdrop{background:rgba(0,0,0,.88)}.viewer{height:100%;display:flex;flex-direction:column}.tools{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:12px 16px;background:var(--panel);border-bottom:1px solid var(--line)}.tools button,.tools a{padding:7px 11px;border:1px solid var(--line);border-radius:6px;background:#1b293c;color:var(--text);text-decoration:none}.tools a{color:var(--accent)}.tools .close{margin-left:auto}.tools button:disabled{opacity:.35;cursor:default}.viewer-caption{padding:10px 16px;font-size:.9rem;color:var(--muted)}.image-stage{min-height:0;flex:1;overflow:auto;display:flex;align-items:center;justify-content:center;background:#000}.image-stage img{display:block;max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain}.image-stage.actual{display:block}.image-stage.actual img{max-width:none;max-height:none;width:auto;height:auto}body.modal-open{overflow:hidden}@media(max-width:760px){main{padding-top:24px}.grid{grid-template-columns:1fr}nav{gap:7px}nav a{font-size:.88rem;padding:7px 9px}dialog{height:98dvh}.tools{gap:7px}.tools button,.tools a{font-size:.85rem;padding:7px}.section-heading{gap:12px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{:root{color-scheme:light}body,main,.card{background:white;color:black}nav,dialog,.section-heading>a{display:none!important}.grid{display:block}.card{break-inside:avoid;margin-bottom:20px;border:1px solid #aaa}h2{break-after:avoid}.intro,.meta,figcaption p,footer{color:#444}main{padding:0}section{margin:20px 0}a{color:black}}
</style></head><body><main id="top"><header><div class="eyebrow">SpaceSurvival / screenshot tour</div>
<h1>__TITLE__</h1><p class="intro">Explore each area at your own pace. Select a screenshot to enlarge it, use the arrow keys to move between views, or open its original PNG. The images are unretouched and shown without cropping.</p>
<p class="meta">__COUNT__ views · Captured __DATE__</p></header>__WARNING__
<nav aria-label="Station areas">__NAV__</nav>__SECTIONS__
<footer>Local screenshot review · These still images do not establish movement, interaction or performance.<br><a href="__MANIFEST__">Capture manifest</a> · Keep this page beside its PNG files when moving the gallery.</footer></main>
<dialog id="lightbox" aria-label="Full screenshot viewer"><div class="viewer"><div class="tools">
<button type="button" id="previous" aria-label="Previous screenshot">← Previous</button><button type="button" id="next" aria-label="Next screenshot">Next →</button>
<button type="button" id="zoom" aria-pressed="false">Actual size</button><a id="original" target="_blank" rel="noopener">Open original PNG ↗</a><button type="button" class="close" id="close">Close ×</button></div>
<div id="viewer-caption" class="viewer-caption" role="status" aria-live="polite"></div><div id="stage" class="image-stage"><img id="full-image" alt=""></div></div></dialog>
<script>
(() => {
 'use strict';
 const shots=Array.from(document.querySelectorAll('.shot')),dialog=document.getElementById('lightbox');
 if(!dialog || typeof dialog.showModal!=='function')return;
 const image=document.getElementById('full-image'),stage=document.getElementById('stage');
 const previous=document.getElementById('previous'),next=document.getElementById('next'),zoom=document.getElementById('zoom');
 const original=document.getElementById('original'),caption=document.getElementById('viewer-caption');
 let current=0,opener=null;
 function fit(){stage.classList.remove('actual');zoom.textContent='Actual size';zoom.setAttribute('aria-pressed','false');stage.scrollTo(0,0);}
 function show(index){current=Math.max(0,Math.min(shots.length-1,index));const shot=shots[current];fit();image.src=shot.getAttribute('href');image.alt=shot.dataset.caption;original.href=shot.getAttribute('href');caption.textContent=(current+1)+' / '+shots.length+' · '+shot.dataset.area+' · '+shot.dataset.caption;previous.disabled=current===0;next.disabled=current===shots.length-1;}
 shots.forEach((shot,index)=>shot.addEventListener('click',event=>{if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;event.preventDefault();opener=shot;show(index);dialog.showModal();document.body.classList.add('modal-open');document.getElementById('close').focus();}));
 previous.addEventListener('click',()=>show(current-1));next.addEventListener('click',()=>show(current+1));
 zoom.addEventListener('click',()=>{const actual=stage.classList.toggle('actual');zoom.textContent=actual?'Fit to window':'Actual size';zoom.setAttribute('aria-pressed',String(actual));});
 document.getElementById('close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>{document.body.classList.remove('modal-open');if(opener)opener.focus();});
 dialog.addEventListener('keydown',event=>{if(event.key==='ArrowLeft'){event.preventDefault();show(current-1);}else if(event.key==='ArrowRight'){event.preventDefault();show(current+1);}else if(event.key==='Home'){event.preventDefault();show(0);}else if(event.key==='End'){event.preventDefault();show(shots.length-1);}});
})();
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path, help='Capture manifest.json; writes sibling index.html')
    parser.add_argument('--title', default='Wayfarer Exchange — station walkthrough')
    args = parser.parse_args()
    manifest, report, images = read_images(args.manifest)
    output = manifest.parent / 'index.html'
    output.write_text(render(manifest, report, images, args.title), encoding='utf-8')
    print(f'Gallery: {output}\nViews: {len(images)}; PNG files unchanged')


if __name__ == '__main__':
    main()
