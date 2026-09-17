"""Build Artifacts/PrefabLibrary/index.html: the parts catalogue and prefabs as one offline web page.

  python Tools/SSLiveLink/build_gallery.py [--project <root>]

Reads catalog.json (and every Prefabs/**/*.json) and writes a single self-contained page next to the
catalogue, meant to be opened straight from disk. The page carries the catalogue as one JSON blob and
draws the cards in JavaScript, so search, type, category, pack and sort filters are instant; nothing is
fetched but the thumbnails, which render_thumbs writes separately (a card without one shows a named
placeholder box). The sections run type by type (Building, Decoration, ...) and category by category
inside a type, with a row of type chips above the category chips. Clicking a card copies its Unreal asset
path, ready to paste into the editor or the Blender add-on; the small i button opens the full paths and
materials inline.

Stdlib only, no Blender and no Unreal: the editor imports build() directly, and so can anything else.
"""
from pathlib import Path
import argparse
import html
import json
import sys

LIBRARY = Path('Artifacts') / 'PrefabLibrary'
PREFABS = Path('Prefabs')
THUMBS_PER_PREFAB = 4
# The types above the categories, in the order the page shows them. The catalogue names each mesh's type
# since ss_prefabs learnt them (GROUPS there); this copy covers a catalogue written before that.
GROUPS = (
    ('Building', ('Walls', 'Floors', 'Ceilings', 'Doors', 'Stairs & Rails', 'Pillars & Frames')),
    ('Decoration', ('Props', 'Furniture', 'Containers', 'Signs & Banners', 'Pipes & Cables', 'Machines',
                    'Consoles & Screens', 'Lights')),
    ('Exterior & Space', ('Station Exterior', 'Asteroids & Debris', 'Wreckage', 'Planets & Sky')),
    ('Ships', ('Ship Parts',)),
    ('Characters & Robots', ('Characters & Robots',)),
    ('Game Objects', ('Game Objects',)),
)
MISC = 'Misc'   # the type of every category no type lists


# ---------------------------------------------------------------- data
def load_catalog(root):
    path = root / LIBRARY / 'catalog.json'
    if not path.exists():
        raise RuntimeError(f'no catalogue at {path}; run SS Prefabs > Rebuild Catalogue in the editor')
    return json.loads(path.read_text(encoding='utf-8'))


def group_maps(catalog):
    """[(type, categories)] to look a category up in: the catalogue's own map when it has one, then GROUPS."""
    own = catalog.get('group_categories')
    own = [(str(g), c) for g, c in own.items() if isinstance(c, (list, tuple))] if isinstance(own, dict) else []
    return own + list(GROUPS)


def group_of(category, maps=GROUPS):
    for group, categories in maps:
        if category in categories:
            return group
    return MISC


def mesh_rows(catalog):
    """The per-card fields, trimmed to what the page shows so the blob stays small; sizes in metres."""
    rows = []
    maps = group_maps(catalog)
    for m in catalog.get('meshes', []):
        asset = m.get('asset', '')
        extent = m.get('extent') or [0.0, 0.0, 0.0]
        category = m.get('category') or 'Misc'
        rows.append({
            'asset': asset,
            'name': m.get('name') or asset.split('.')[-1],
            'pack': m.get('pack') or '',
            'group': str(m.get('group') or group_of(category, maps)),
            'category': category,
            'size': [round(2.0 * e / 100.0, 3) for e in extent],
            'origin': [round(v, 1) for v in (m.get('origin') or [0.0, 0.0, 0.0])],
            'radius': round(float(m.get('radius') or 0.0), 1),
            'triangles': int(m.get('triangles') or 0),
            'materials': list(m.get('materials') or []),
            'proxy': m.get('proxy'),
            'thumb': m.get('thumb'),
        })
    return rows


def group_rows(catalog, meshes):
    """[(type, count)] in the owner's order: the catalogue's map, then GROUPS, then any other type, Misc last."""
    counts = {}
    for m in meshes:
        counts[m['group']] = counts.get(m['group'], 0) + 1
    order = [g for g, _ in group_maps(catalog)]
    order = [g for g in dict.fromkeys(order + sorted(counts)) if g != MISC] + [MISC]
    return [(g, counts[g]) for g in order if counts.get(g)]


def category_rows(catalog, meshes, groups):
    """[(name, count, type)], type by type and in the catalogue's own order inside a type; counted from the
    meshes so the page never lies. A category's type is its first mesh's: every mesh of a category has the
    same one unless somebody edited the catalogue by hand."""
    counts, group = {}, {}
    for name in catalog.get('categories', {}):
        counts[name] = 0
    for m in meshes:
        counts[m['category']] = counts.get(m['category'], 0) + 1
        group.setdefault(m['category'], m['group'])
    rank = {g: i for i, (g, _) in enumerate(groups)}
    rows = [(name, n, group[name]) for name, n in counts.items() if n]
    return sorted(rows, key=lambda r: rank[r[2]])   # a stable sort: the catalogue's order survives inside a type


def pack_rows(meshes):
    counts = {}
    for m in meshes:
        counts[m['pack']] = counts.get(m['pack'], 0) + 1
    return sorted(counts.items())


def kind(value):
    """What a JSON value is, in the words of somebody editing the file by hand."""
    names = {dict: 'an object', list: 'a list', str: 'a string', bool: 'true/false', int: 'a number', float: 'a number', type(None): 'null'}
    return names.get(type(value), type(value).__name__)


def read_recipe(path):
    """(purpose, part count, light count, distinct asset paths) of a recipe file.

    Recipes are JSON people edit by hand, so the shape is checked and not trusted: a value of the wrong type
    raises ValueError naming it, where it used to surface as a TypeError three lines later (or, for an asset
    that is not a string, outside the try altogether) and take the whole build down.
    """
    recipe = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(recipe, dict):
        raise ValueError(f'the recipe must be an object, not {kind(recipe)}')
    lists = {}
    for key in ('static_meshes', 'point_lights'):
        value = recipe.get(key)
        lists[key] = [] if value is None else value
        if not isinstance(lists[key], list):
            raise ValueError(f'"{key}" must be a list, not {kind(value)}')
    assets = []
    for i, part in enumerate(lists['static_meshes']):
        if not isinstance(part, dict):
            raise ValueError(f'static_meshes[{i}] must be an object, not {kind(part)}')
        asset = part.get('asset')
        if asset is not None and not isinstance(asset, str):
            raise ValueError(f'static_meshes[{i}].asset must be a string, not {kind(asset)}')
        if asset and asset not in assets:
            assets.append(asset)
    purpose = recipe.get('purpose')
    return (purpose if isinstance(purpose, str) else ''), len(lists['static_meshes']), len(lists['point_lights']), assets


def prefab_rows(root, by_asset):
    """One row per recipe under Prefabs/, categorised by directory the way the editor menu does.

    A recipe that cannot be read, or holds values of the wrong type, is skipped: it keeps its card, empty,
    with a note saying what is wrong, and the rest of the page is built as usual.
    """
    folder = root / PREFABS
    rows = []
    if not folder.is_dir():
        return rows
    for f in sorted(folder.rglob('*.json')):
        rel = f.relative_to(folder)
        category = rel.parent.as_posix() if str(rel.parent) != '.' else 'Unsorted'
        row = {'ref': f'{category}/{rel.stem}', 'category': category, 'name': rel.stem,
               'path': f.relative_to(root).as_posix(), 'purpose': '', 'parts': 0, 'lights': 0,
               'assets': [], 'thumbs': [], 'error': None}
        try:
            row['purpose'], row['parts'], row['lights'], row['assets'] = read_recipe(f)
        except json.JSONDecodeError as e:
            # A half-written recipe should show up as a broken card, not take the whole page down.
            row['error'] = f'skipped, not valid JSON: {e}'
        except (OSError, UnicodeError) as e:
            row['error'] = f'skipped, unreadable: {e}'
        except (ValueError, RecursionError) as e:
            row['error'] = f'skipped, wrong value type: {e}'
        for asset in row['assets'][:THUMBS_PER_PREFAB]:
            entry = by_asset.get(asset)
            row['thumbs'].append({'name': entry['name'] if entry else asset.split('.')[-1],
                                  'thumb': entry.get('thumb') if entry else None})
        rows.append(row)
    # Grouped by category then name, so the section reads like the editor's Place menu.
    rows.sort(key=lambda r: (r['category'].lower(), r['name'].lower()))
    return rows


def gallery_data(root):
    catalog = load_catalog(root)
    meshes = mesh_rows(catalog)
    groups = group_rows(catalog, meshes)
    categories = category_rows(catalog, meshes, groups)
    by_asset = {m['asset']: m for m in meshes}
    return {
        'generated': str(catalog.get('generated', '')),
        'engine': str(catalog.get('engine', '')),
        'groups': groups,
        'categories': categories,
        'packs': pack_rows(meshes),
        'meshes': meshes,
        'prefabs': prefab_rows(root, by_asset),
    }


# ---------------------------------------------------------------- page
def json_for_script(data):
    """JSON that is safe inside a <script> element: no '<', '>' or '&' survive, so the HTML parser
    can never see '</script' or a comment opener inside the blob, and it still parses as plain JSON."""
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    for ch, code in (('<', '\\u003c'), ('>', '\\u003e'), ('&', '\\u0026'), (' ', '\\u2028'), (' ', '\\u2029')):
        text = text.replace(ch, code)
    return text


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SpaceSurvival parts library</title>
<link rel="icon" href="data:,">
<style>
:root { --bg: #1b1d22; --panel: #23262d; --panel2: #2b2f38; --line: #363b47; --text: #e8e9ec; --muted: #9aa0ad; --accent: #7cc4ff; --warn: #ff8a80; }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.4 system-ui, "Segoe UI", Roboto, sans-serif; }
[hidden] { display: none !important; }
header { position: sticky; top: 0; z-index: 10; background: rgba(27, 29, 34, 0.96); backdrop-filter: blur(6px); border-bottom: 1px solid var(--line); padding: 10px 16px; }
.row { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; }
h1 { font-size: 18px; margin: 0 8px 0 0; }
.counts, .muted { color: var(--muted); font-size: 12px; }
input[type=search], select { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: 6px; padding: 6px 10px; font: inherit; }
input[type=search] { flex: 1; min-width: 240px; }
input[type=search]:focus, select:focus { outline: none; border-color: var(--accent); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.chip { background: var(--panel); border: 1px solid var(--line); color: var(--text); border-radius: 999px; padding: 3px 10px; font: inherit; font-size: 12px; cursor: pointer; }
.chip:hover { border-color: var(--accent); }
.chip.on { background: var(--accent); color: #10131a; border-color: var(--accent); }
.chip .n { color: var(--muted); margin-left: 5px; }
.chip.on .n { color: #10131a; opacity: 0.7; }
.chips.types .chip { font-size: 13px; font-weight: 600; padding: 4px 12px; }
main { padding: 8px 16px 90px; }
section.cat { margin: 14px 0; }
.type-head { margin: 26px 0 0; font-size: 12px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
.type-head .count { color: var(--muted); font-weight: 400; letter-spacing: 0; margin-left: 8px; }
.sec { display: flex; align-items: center; gap: 8px; width: 100%; background: none; border: 0; border-bottom: 1px solid var(--line); color: var(--text); font: inherit; font-size: 16px; font-weight: 600; padding: 8px 0; cursor: pointer; text-align: left; }
.sec .caret { display: inline-block; width: 0; height: 0; border: 5px solid transparent; border-left-color: var(--muted); transform: rotate(90deg); transition: transform 0.15s; }
.sec[aria-expanded=false] .caret { transform: none; }
.sec .count { color: var(--muted); font-weight: 400; font-size: 13px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; padding-top: 10px; }
.card { position: relative; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; cursor: pointer; }
.card:hover, .card:focus-visible { border-color: var(--accent); outline: none; }
.thumb, .mini { display: block; width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background: var(--bg); }
.ph { display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 11px; text-align: center; padding: 8px; word-break: break-word; border-bottom: 1px dashed var(--line); }
.strip { display: grid; gap: 2px; background: var(--line); }
.meta { padding: 8px 10px; }
.name { font-weight: 600; font-size: 13px; word-break: break-word; }
.sub { color: var(--muted); font-size: 12px; display: flex; justify-content: space-between; gap: 6px; }
.err { color: var(--warn); font-size: 12px; margin-top: 4px; }
.info { position: absolute; top: 6px; right: 6px; width: 22px; height: 22px; border-radius: 50%; border: 1px solid var(--line); background: rgba(27, 29, 34, 0.85); color: var(--text); font: italic 600 13px/1 Georgia, serif; cursor: pointer; }
.info:hover { border-color: var(--accent); color: var(--accent); }
.details { display: none; padding: 0 10px 10px; cursor: auto; }
.card.open { grid-column: 1 / -1; display: grid; grid-template-columns: 220px 1fr; }
.card.open .details { display: block; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; margin: 6px 0 0; font-size: 12px; }
dt { color: var(--muted); }
dd { margin: 0; }
code { font-family: ui-monospace, Consolas, monospace; font-size: 12px; word-break: break-all; user-select: all; }
footer { position: fixed; left: 0; right: 0; bottom: 0; padding: 6px 16px; background: rgba(27, 29, 34, 0.92); border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; }
#toast { position: fixed; left: 50%; bottom: 44px; transform: translate(-50%, 16px); background: var(--panel2); color: var(--text); border: 1px solid var(--accent); border-radius: 8px; padding: 8px 14px; opacity: 0; transition: opacity 0.2s, transform 0.2s; pointer-events: none; max-width: 90vw; font-size: 13px; word-break: break-all; z-index: 20; }
#toast.show { opacity: 1; transform: translate(-50%, 0); }
</style>
</head>
<body>
<header>
  <div class="row">
    <h1>SpaceSurvival parts library</h1>
    <span class="counts">__COUNTS__</span>
  </div>
  <div class="row">
    <input id="q" type="search" placeholder="Search name, pack or asset path ( / )" aria-label="Search parts" autocomplete="off" spellcheck="false">
    <select id="pack" aria-label="Pack"><option value="">All packs</option></select>
    <select id="sort" aria-label="Sort">
      <option value="name">Sort: name</option>
      <option value="size">Sort: size</option>
      <option value="triangles">Sort: triangles</option>
    </select>
    <span class="counts" id="visible"></span>
  </div>
  <div class="chips types" id="types"></div>
  <div class="chips" id="chips"></div>
</header>
<main>
  <noscript><p>This page draws the catalogue with JavaScript; enable it to see the parts.</p></noscript>
  <div id="sections"></div>
  <section class="cat" id="prefabs">
    <button type="button" class="sec" aria-expanded="true"><span class="caret"></span><span class="label">Prefabs</span><span class="count" id="prefab-count"></span></button>
    <p class="muted" id="prefab-note" hidden></p>
    <div class="grid" id="prefab-grid"></div>
  </section>
</main>
<footer>Click a card to copy its asset path (a prefab card copies its Category/Name). In Blender, paste the path into the name field of the SS Link panel's Parts library: it finds that part, ready for Add at Cursor. The i button shows the full paths and materials. Press / to search.</footer>
<div id="toast" role="status" aria-live="polite"></div>
<script id="ss-data" type="application/json">__DATA__</script>
<script>
(function () {
  'use strict';
  var DATA = JSON.parse(document.getElementById('ss-data').textContent);
  var $ = function (sel) { return document.querySelector(sel); };
  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  var f1 = function (v) { return Number(v).toFixed(1); };
  var metres = function (m) { return f1(m.size[0]) + ' x ' + f1(m.size[1]) + ' x ' + f1(m.size[2]) + ' m'; };
  var shortPack = function (p) { return p.split('/').pop(); };
  // Type and category names come from the data, so they are kept in Sets and Maps, never as keys of a plain
  // object: there a category called 'constructor' or '__proto__' would already be "selected", or break the page.
  var state = { q: '', types: new Set(), cats: new Set(), pack: '', sort: 'name' };

  // ---- toast and clipboard. file:// pages do not always get navigator.clipboard, hence the textarea fallback.
  var toastEl = $('#toast');
  var toastTimer = 0;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 1600);
  }
  function copyText(text) {
    var done = function () { toast('Copied ' + text); };
    var fallback = function () {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      if (ok) { done(); } else { toast('Copy failed; open the details and select the path'); }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  // ---- thumbnails, with a named box standing in until render_thumbs has been run
  function placeholder(name, cls) {
    var d = document.createElement('div');
    d.className = cls + ' ph';
    d.textContent = name;
    return d;
  }
  function thumbNode(item, cls) {
    if (!item.thumb) { return placeholder(item.name, cls); }
    var img = document.createElement('img');
    img.className = cls;
    img.loading = 'lazy';
    img.alt = '';
    img.src = item.thumb;
    img.addEventListener('error', function () { img.replaceWith(placeholder(item.name, cls)); });
    return img;
  }
  function collapsible(btn, body) {
    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') !== 'true';
      btn.setAttribute('aria-expanded', String(open));
      body.hidden = !open;
    });
  }
  function onActivate(el, fn) {
    el.addEventListener('click', fn);
    el.addEventListener('keydown', function (e) {
      // Only keys pressed on the card itself. Enter or Space on the i button inside it bubbles up to here too,
      // and answering it would copy the path and, by preventing the default, swallow the button's own click.
      if (e.target !== el) { return; }
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(); }
    });
  }

  // ---- part cards
  function details(m) {
    var cm = m.size.map(function (v) { return Math.round(v * 100); });
    var mats = m.materials.length
      ? m.materials.map(function (p) { return '<code>' + esc(p) + '</code>'; }).join('<br>')
      : '<span class="muted">none</span>';
    return '<dl>'
      + '<dt>Asset</dt><dd><code>' + esc(m.asset) + '</code></dd>'
      + '<dt>Pack</dt><dd>' + esc(m.pack) + ' &middot; ' + esc(m.group) + ' &middot; ' + esc(m.category) + '</dd>'
      + '<dt>Bounds</dt><dd>' + cm.join(' x ') + ' cm, centre ' + m.origin.map(Math.round).join(', ') + ', radius ' + Math.round(m.radius) + ' cm</dd>'
      + '<dt>Triangles</dt><dd>' + m.triangles.toLocaleString() + '</dd>'
      + '<dt>Materials</dt><dd>' + mats + '</dd>'
      + '<dt>Proxy</dt><dd><code>' + esc(m.proxy || 'none') + '</code></dd>'
      + '<dt>Thumb</dt><dd><code>' + esc(m.thumb || 'not rendered yet') + '</code></dd>'
      + '</dl>';
  }
  function makeCard(m) {
    var card = document.createElement('article');
    card.className = 'card';
    card.tabIndex = 0;
    card.title = 'Click to copy ' + m.asset;
    card.appendChild(thumbNode(m, 'thumb'));
    var body = document.createElement('div');
    body.className = 'body';
    body.innerHTML = '<div class="meta"><div class="name">' + esc(m.name) + '</div>'
      + '<div class="sub"><span title="' + esc(m.pack) + '">' + esc(shortPack(m.pack)) + '</span><span>' + m.triangles.toLocaleString() + ' tris</span></div>'
      + '<div class="sub"><span title="width x depth x height (X x Y x Z), metres">' + metres(m) + '</span></div></div>'
      + '<div class="details">' + details(m) + '</div>';
    card.appendChild(body);
    var info = document.createElement('button');
    info.type = 'button';
    info.className = 'info';
    info.textContent = 'i';
    info.title = 'Details';
    info.setAttribute('aria-label', 'Details for ' + m.name);
    info.setAttribute('aria-expanded', 'false');
    // A button turns Enter and Space into a click by itself, so this one listener serves mouse and keyboard.
    info.addEventListener('click', function (e) {
      e.stopPropagation();
      info.setAttribute('aria-expanded', String(card.classList.toggle('open')));
    });
    card.appendChild(info);
    // Selecting a path inside the details must not also copy the asset.
    body.querySelector('.details').addEventListener('click', function (e) { e.stopPropagation(); });
    onActivate(card, function () { copyText(m.asset); });
    return card;
  }

  var sectionsEl = $('#sections');
  var typeBlocks = new Map();
  DATA.groups.forEach(function (pair) {
    var block = document.createElement('div');
    block.className = 'type';
    var head = document.createElement('h2');
    head.className = 'type-head';
    head.innerHTML = esc(pair[0]) + '<span class="count"></span>';
    block.appendChild(head);
    sectionsEl.appendChild(block);
    typeBlocks.set(pair[0], { el: block, count: head.querySelector('.count'), total: pair[1] });
  });
  var sections = new Map();
  DATA.categories.forEach(function (row) {
    var name = row[0], total = row[1], type = typeBlocks.get(row[2]);
    var sec = document.createElement('section');
    sec.className = 'cat';
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sec';
    btn.setAttribute('aria-expanded', 'true');
    btn.innerHTML = '<span class="caret"></span><span class="label">' + esc(name) + '</span><span class="count"></span>';
    var grid = document.createElement('div');
    grid.className = 'grid';
    collapsible(btn, grid);
    sec.appendChild(btn);
    sec.appendChild(grid);
    (type ? type.el : sectionsEl).appendChild(sec);
    sections.set(name, { sec: sec, grid: grid, count: btn.querySelector('.count'), total: total, group: row[2] });
  });
  var cards = DATA.meshes.map(function (m) {
    return { m: m, el: makeCard(m), hay: (m.name + ' ' + m.pack + ' ' + m.asset).toLowerCase() };
  });
  cards.forEach(function (c) {
    var s = sections.get(c.m.category);
    if (s) { s.grid.appendChild(c.el); }
  });

  // ---- prefab cards
  var pgrid = $('#prefab-grid');
  var pnote = $('#prefab-note');
  var pcount = $('#prefab-count');
  collapsible($('#prefabs .sec'), pgrid);
  var prefabs = DATA.prefabs.map(function (p) {
    var el = document.createElement('article');
    el.className = 'card prefab';
    el.tabIndex = 0;
    el.title = 'Click to copy ' + p.ref + (p.purpose ? '\n' + p.purpose : '');
    var strip = document.createElement('div');
    strip.className = 'strip';
    var thumbs = p.thumbs.length ? p.thumbs : [{ name: p.error ? 'unreadable' : 'no parts', thumb: null }];
    strip.style.gridTemplateColumns = 'repeat(' + Math.min(2, thumbs.length) + ', 1fr)';
    thumbs.forEach(function (t) { strip.appendChild(thumbNode(t, 'mini')); });
    el.appendChild(strip);
    var body = document.createElement('div');
    body.className = 'body';
    body.innerHTML = '<div class="meta"><div class="name">' + esc(p.name) + '</div>'
      + '<div class="sub"><span>' + esc(p.category) + '</span><span>' + p.parts + ' parts &middot; ' + p.lights + ' lights</span></div>'
      + (p.error ? '<div class="err">' + esc(p.error) + '</div>' : '') + '</div>';
    el.appendChild(body);
    onActivate(el, function () { copyText(p.ref); });
    pgrid.appendChild(el);
    return { p: p, el: el, hay: (p.ref + ' ' + p.purpose + ' ' + p.assets.join(' ')).toLowerCase() };
  });
  function applyPrefabs(tokens) {
    if (!prefabs.length) {
      pnote.textContent = 'no prefabs yet';
      pnote.hidden = false;
      pcount.textContent = '0';
      return;
    }
    var n = 0;
    prefabs.forEach(function (x) {
      var ok = tokens.every(function (t) { return x.hay.indexOf(t) !== -1; });
      x.el.hidden = !ok;
      if (ok) { n++; }
    });
    pnote.textContent = 'no prefabs match';
    pnote.hidden = n > 0;
    pcount.textContent = n === prefabs.length ? String(n) : n + ' / ' + prefabs.length;
  }

  // ---- filtering and sorting: cards are built once; a filter pass hides and reorders them
  var byName = function (a, b) { return a.m.name.localeCompare(b.m.name); };
  var sorters = {
    name: byName,
    size: function (a, b) { return (b.m.radius - a.m.radius) || byName(a, b); },
    triangles: function (a, b) { return (b.m.triangles - a.m.triangles) || byName(a, b); }
  };
  function apply() {
    var tokens = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    var sorted = cards.slice().sort(sorters[state.sort] || byName);
    var shown = new Map();
    sorted.forEach(function (c) {
      var ok = tokens.every(function (t) { return c.hay.indexOf(t) !== -1; })
        && (!state.types.size || state.types.has(c.m.group))
        && (!state.cats.size || state.cats.has(c.m.category))
        && (!state.pack || c.m.pack === state.pack);
      c.el.hidden = !ok;
      var s = sections.get(c.m.category);
      if (!s) { return; }
      s.grid.appendChild(c.el);   // re-appending moves the node, so the grid follows the sort order
      if (ok) { shown.set(c.m.category, (shown.get(c.m.category) || 0) + 1); }
    });
    var visible = 0;
    var perType = new Map();
    sections.forEach(function (s, name) {
      var n = shown.get(name) || 0;
      visible += n;
      perType.set(s.group, (perType.get(s.group) || 0) + n);
      s.sec.hidden = n === 0;
      s.count.textContent = n === s.total ? String(n) : n + ' / ' + s.total;
    });
    typeBlocks.forEach(function (t, name) {
      var n = perType.get(name) || 0;
      t.el.hidden = n === 0;
      t.count.textContent = n === t.total ? String(n) : n + ' / ' + t.total;
    });
    $('#visible').textContent = visible === cards.length ? cards.length + ' parts' : visible + ' of ' + cards.length + ' parts';
    applyPrefabs(tokens);
  }

  // ---- controls
  var chips = $('#chips');
  function chip(label, count, key) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'chip';
    b.setAttribute('data-key', key);
    b.innerHTML = esc(label) + '<span class="n">' + count + '</span>';
    return b;
  }
  var typeChips = $('#types');
  var typeTotals = new Map(DATA.groups);
  function toggle(set, name) {
    if (set.has(name)) { set.delete(name); } else { set.add(name); }
  }
  function syncChips() {
    var i, key;
    var all = typeChips.querySelectorAll('.chip');
    for (i = 0; i < all.length; i++) {
      key = all[i].getAttribute('data-key');
      all[i].classList.toggle('on', key === '' ? !state.types.size : state.types.has(key));
    }
    // With types chosen, only their categories are offered, and 'All' counts what those types hold.
    var within = 0;
    state.types.forEach(function (t) { within += typeTotals.get(t) || 0; });
    all = chips.querySelectorAll('.chip');
    for (i = 0; i < all.length; i++) {
      key = all[i].getAttribute('data-key');
      all[i].classList.toggle('on', key === '' ? !state.cats.size : state.cats.has(key));
      if (key === '') {
        all[i].querySelector('.n').textContent = state.types.size ? within : cards.length;
      } else {
        all[i].hidden = state.types.size > 0 && !state.types.has(all[i].getAttribute('data-group'));
      }
    }
  }
  var allTypes = chip('All types', cards.length, '');
  allTypes.addEventListener('click', function () { state.types.clear(); syncChips(); apply(); });
  typeChips.appendChild(allTypes);
  DATA.groups.forEach(function (pair) {
    var name = pair[0];
    var b = chip(name, pair[1], name);
    b.addEventListener('click', function () {
      toggle(state.types, name);
      // A category chosen earlier that the types now on offer do not hold would filter everything away unseen.
      state.cats.forEach(function (c) {
        var s = sections.get(c);
        if (state.types.size && s && !state.types.has(s.group)) { state.cats.delete(c); }
      });
      syncChips();
      apply();
    });
    typeChips.appendChild(b);
  });
  var allChip = chip('All', cards.length, '');
  allChip.addEventListener('click', function () { state.cats.clear(); syncChips(); apply(); });
  chips.appendChild(allChip);
  DATA.categories.forEach(function (row) {
    var name = row[0];
    var b = chip(name, row[1], name);
    b.setAttribute('data-group', row[2]);
    b.addEventListener('click', function () {
      toggle(state.cats, name);
      syncChips();
      apply();
    });
    chips.appendChild(b);
  });
  var packSel = $('#pack');
  DATA.packs.forEach(function (pair) {
    var o = document.createElement('option');
    o.value = pair[0];
    o.textContent = pair[0] + ' (' + pair[1] + ')';
    packSel.appendChild(o);
  });
  packSel.addEventListener('change', function () { state.pack = packSel.value; apply(); });
  $('#sort').addEventListener('change', function (e) { state.sort = e.target.value; apply(); });
  var search = $('#q');
  search.addEventListener('input', function () { state.q = search.value; apply(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== search) {
      e.preventDefault();
      search.focus();
      search.select();
    } else if (e.key === 'Escape' && document.activeElement === search && search.value) {
      search.value = '';
      state.q = '';
      apply();
    }
  });
  syncChips();
  apply();
})();
</script>
</body>
</html>
"""


def render(data):
    counts = '{} parts · {} categories · {} packs · {} prefabs · catalogue {} ({})'.format(
        len(data['meshes']), len(data['categories']), len(data['packs']), len(data['prefabs']),
        data['generated'] or 'undated', data['engine'] or 'unknown engine')
    return PAGE.replace('__COUNTS__', html.escape(counts)).replace('__DATA__', json_for_script(data))


def build(root):
    """Write the gallery next to the catalogue; returns the numbers the caller wants to report.

    'skipped' counts the recipes whose cards are empty because the file could not be used, and 'notes'
    says why, one line each, for the log of whoever called.
    """
    root = Path(root)
    data = gallery_data(root)
    out = root / LIBRARY / 'index.html'
    out.write_text(render(data), encoding='utf-8', newline='\n')
    notes = [f'{p["path"]}: {p["error"]}' for p in data['prefabs'] if p['error']]
    return {'cards': len(data['meshes']), 'types': len(data['groups']), 'categories': len(data['categories']),
            'prefabs': len(data['prefabs']), 'skipped': len(notes), 'path': str(out), 'notes': notes}


if __name__ == '__main__':
    # Accept the Blender-style '--' separator too, so the same command line works from either host.
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description='Write Artifacts/PrefabLibrary/index.html from the catalogue and prefabs.')
    ap.add_argument('--project', default=str(Path(__file__).resolve().parents[2]), help='project root (default: this repo)')
    args = ap.parse_args(argv)
    print('GALLERY_OK ' + json.dumps(build(Path(args.project))))
