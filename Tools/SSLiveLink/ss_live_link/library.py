"""The parts library as the panel sees it: the scene state, thumbnail previews, the filtered list, the
picture-grid picker, and the operators that load the catalogue and place a part.

SSLinkState (scene.ss_link) is the add-on's shared UI state; the other modules read it from the scene
and need no import of this module for that.

The filter is type AND category AND pack AND name, and it is one filter: the list, the picture grid and
every count on the panel go through part_visible(). groups.py draws the type buttons and the name field;
the state and the rules are here, because the list and the grid are.

The filter is scene data and the menus and counts made from it are not, so whatever puts scene data back
without the update callbacks (undo, redo, File > Open) is followed by resync(), from state_restored().
"""
import zlib

import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty

from . import core

PICK_CAP = 600   # pictures in the grid popup; past that it stops being a quick pick, and the list still has everything


# ---------------------------------------------------------------- thumbnails
_previews = {'collection': None, 'missing': set()}   # the icon cache, and the thumbs known not to exist yet


def preview_collection():
    """The preview collection holding thumbnail icons, made on first use so registering stays cheap."""
    if _previews['collection'] is None:
        _previews['collection'] = bpy.utils.previews.new()
    return _previews['collection']


def get_icon(thumb):
    """The icon id for a thumbnail path relative to the library, loaded once; 0 while there is no file to show."""
    if not thumb:
        return 0
    pcoll = preview_collection()
    if thumb in pcoll:
        return pcoll[thumb].icon_id
    if thumb in _previews['missing']:
        return 0
    lib = core.library_dir()
    path = (lib / thumb) if lib else None
    if not path or not path.exists():
        # Remember the miss: the list asks on every redraw, and a stat per row per redraw adds up.
        _previews['missing'].add(thumb)
        return 0
    return pcoll.load(thumb, str(path), 'IMAGE').icon_id


def clear_previews():
    """Drop every cached icon so freshly rendered thumbnails are read from disk on the next draw."""
    if _previews['collection'] is not None:
        bpy.utils.previews.remove(_previews['collection'])
    _previews.update(collection=None, missing=set())


def size_label(entry):
    """'W x D x H m' from the catalogue's half extents in centimetres: the size a builder thinks in."""
    return ' x '.join(f'{2 * e / 100.0:.2f}' for e in entry['extent']) + ' m'


# ---------------------------------------------------------------- types
# The types above the categories, which is how the owner reaches for things: "all building materials",
# "all decorations". The catalogue names each mesh's type since ss_prefabs learnt them; this copy of its
# GROUPS covers a catalogue written before that, and gives the type buttons their order.
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


def group_of(category, group_categories=None):
    """The type a category belongs to: by the catalogue's own map when it carries one, then by GROUPS."""
    for group, categories in list((group_categories or {}).items()) + list(GROUPS):
        if category in categories:
            return group
    return MISC


def part_group(item):
    """A part's type. Parts kept in a .blend saved before the add-on knew types carry none: work it out."""
    return item.group or group_of(item.category)


def type_order(parts, group_categories=None):
    """Every type to offer, in button order: the catalogue's and GROUPS' own, any other the parts name, Misc last."""
    order = list(group_categories or {}) + [g for g, _ in GROUPS]
    order += sorted({part_group(it) for it in parts} - set(order))
    order = [g for g in dict.fromkeys(order) if g != MISC]
    return order + [MISC]


# ---------------------------------------------------------------- UI state
# An enum is stored as its item's number. The type, category and pack menus are relisted and relabelled as
# the filter moves (the category menu shrinks to the chosen type's), so an item's place in its list cannot be
# its number. Nor can the order the names were met in: that differs from one session to the next, and a
# .blend saved with Doors chosen would reopen with Walls chosen. The number comes from the name, so it is
# the same in every session; the table only keeps two names from sharing one. 'All' is 0, the default.
_numbers = {'groups': {'All': 0}, 'categories': {'All': 0}, 'packs': {'All': 0}}
NUMBER_SPAN = 0x7FFFFF   # numbers stay under 2**24: buttons carry an enum's value as a float


def _numbered(kind, ident):
    taken = _numbers[kind]
    if ident not in taken:
        n = zlib.crc32(ident.encode('utf-8')) % NUMBER_SPAN + 1
        while n in taken.values():
            n = n % NUMBER_SPAN + 1
        taken[ident] = n
    return taken[ident]


# Blender keeps pointers into the item lists an EnumProperty callback returns, so they live at module level.
_enum_cache = {'groups': [('All', 'All', '', 0)] + [(g, g, ', '.join(c), _numbered('groups', g)) for g, c in GROUPS] + [(MISC, MISC, '', _numbered('groups', MISC))],
               'categories': [('All', 'All', '', 0)], 'packs': [('All', 'All', '', 0)], 'prefabs': [('', '(none)', '')]}
_pick_items = [('', '(load the catalogue)', '', 0, 0)]   # the picture grid
# What the last recount found, for the panel: parts per type, parts shown, the types in button order, and what
# was counted (which scene, how many parts, under which filter; None until there has been a recount).
_counts = {'groups': {}, 'shown': 0, 'counted': None, 'order': [g for g, _, _, _ in _enum_cache['groups'][1:]]}


def group_items(self, context):
    return _enum_cache['groups']


def category_items(self, context):
    return _enum_cache['categories']


def pack_items(self, context):
    return _enum_cache['packs']


def prefab_items(self, context):
    return _enum_cache['prefabs']


def pick_items(self, context):
    return _pick_items


def refresh_prefab_items():
    files = core.prefab_files()
    _enum_cache['prefabs'] = [(core.prefab_ref(f), core.prefab_ref(f), str(f)) for f in files] or [('', '(no prefabs yet)', '')]


def search_words(text):
    """The name filter as the words a part's name must all contain, in any order and any case."""
    return tuple(text.lower().split())


def name_matches(item, words):
    """Every word in the part's name. A word that begins with '/' is an asset path, or a piece of one, and is
    looked for in the part's path instead: a card clicked in the visual browser copies its path, and pasted
    into the name field that path finds its part."""
    if not words:
        return True
    name, asset = item.name.lower(), item.asset.lower()
    return all((w in asset) if w.startswith('/') else (w in name) for w in words)


def part_visible(item, category, pack, group='All', words=()):
    """Whether a part passes the filter: its type AND category AND pack AND every word of the name filter."""
    if group != 'All' and part_group(item) != group:
        return False
    if (category != 'All' and item.category != category) or (pack != 'All' and item.pack != pack):
        return False
    return name_matches(item, words)


def current_filter(st):
    """The panel's filter as part_visible's arguments: part_visible(item, *current_filter(st)).

    A choice is stored as a number and reads as '' while its menu does not list it (the menus are one set for
    the whole add-on, and until resync() or a filter callback relists them they may be another scene's); that
    is no choice, not a choice nothing can match.
    """
    return st.category or 'All', st.pack or 'All', st.group or 'All', search_words(st.search)


def type_categories(st, group):
    """The categories the catalogue has parts of under a type; under 'All', every category."""
    return sorted({it.category for it in st.parts if group == 'All' or part_group(it) == group})


def refresh_filters(st):
    """Recount the parts and relabel the type, category and pack menus, so every number is what a click shows.

    A menu counts under the other filters, not its own: a type's number ignores the chosen type and category
    (or every type but the chosen one would read 0), a category's ignores the chosen category, a pack's the
    chosen pack; all of them honour the name filter. The category menu lists only the chosen type's
    categories, which is the point of choosing a type first.
    """
    category, pack, group, words = current_filter(st)
    members, groups, cats, packs, shown = {}, {}, {}, {}, 0
    for it in st.parts:
        g = part_group(it)
        in_group, in_category, in_pack = group in ('All', g), category in ('All', it.category), pack in ('All', it.pack)
        # What a menu lists does not depend on the counts: a category or pack with nothing to show reads (0).
        members.setdefault(g, set()).add(it.category)
        packs.setdefault(it.pack, 0)
        if in_group:
            cats.setdefault(it.category, 0)
        if not name_matches(it, words):
            continue
        if in_pack:
            groups[g] = groups.get(g, 0) + 1
            if in_group:
                cats[it.category] += 1
        if in_group and in_category:
            packs[it.pack] += 1
            shown += 1 if in_pack else 0
    order = _counts['order'] + sorted(set(members) - set(_counts['order']))
    _enum_cache['groups'] = [('All', f'All ({sum(groups.values())})', 'Every type', 0)] + \
        [(g, f'{g} ({groups.get(g, 0)})', f'{groups.get(g, 0)} parts: ' + (', '.join(sorted(members.get(g, ()))) or 'none in this catalogue'),
          _numbered('groups', g)) for g in order]   # the tooltip repeats the count: a narrow sidebar cuts the label short
    _enum_cache['categories'] = [('All', f'All ({sum(cats.values())})', '', 0)] + \
        [(c, f'{c} ({n})', '', _numbered('categories', c)) for c, n in sorted(cats.items())]
    _enum_cache['packs'] = [('All', 'All packs', '', 0)] + [(p, f'{p} ({n})', '', _numbered('packs', p)) for p, n in sorted(packs.items())]
    # Under the filter as it was read above: had a stale menu hidden a choice, this count is not of what it says now.
    _counts.update(groups=groups, shown=shown, counted=(st.id_data.name_full, len(st.parts), (category, pack, group, words)), order=order)


def type_count(group):
    """Parts of a type under the current pack and name filter, as of the last recount."""
    return _counts['groups'].get(group, 0)


def counts_known(st):
    """False while the counts are not of this scene, these parts and this filter.

    The parts and the filter are saved with the scene and the counts are not, and drawing may not recount (it
    cannot touch the scene). resync() recounts after a file is opened and after undo and redo; whatever else
    moves the filter behind the callbacks' back (another scene shown, a script) must not leave the panel
    greying a type out over a stale 0, or naming a number of parts the list does not show.
    """
    return _counts['counted'] == (st.id_data.name_full, len(st.parts), current_filter(st))


def shown_label(st):
    """'79 of 458 parts' for the panel, from the last recount."""
    return f'{_counts["shown"]} of {len(st.parts)} parts' if counts_known(st) else f'{len(st.parts)} parts'


def grid_note(st):
    """'' while the picture grid shows every part the filter leaves, else the line that says it stops early.

    The parts are sorted by category, so a grid cut at the cap loses whole categories from the end of the
    alphabet (Walls, Wreckage), and nothing else on the panel would say why a wall cannot be found in it."""
    if counts_known(st) and _counts['shown'] > PICK_CAP:
        return f'pictures: the first {PICK_CAP} of {_counts["shown"]}. Choose a type or category to see the rest; the list has them all'
    return ''


def refresh_pick_items(st):
    """Rebuild the picture grid from the parts under the current filter, then keep grid and list on one part.

    Each item's number is the part's index in the list, so choosing a picture is a list selection. When the
    filter hides the active row the first visible part becomes active, so what is highlighted is always in view.
    """
    items = []
    visible = current_filter(st)
    for i, it in enumerate(st.parts):
        if part_visible(it, *visible):
            items.append((it.asset, it.name, f'{it.pack}   {it.size}   {it.triangles} triangles', get_icon(it.thumb), i))
            if len(items) >= PICK_CAP:
                break
    _pick_items[:] = items or [('', '(no parts match)', '', 0, 0)]
    if items:
        active = st.part_index if any(n == st.part_index for *_, n in items) else items[0][4]
        st.part_pick = st.parts[active].asset
    # With nothing to show, the grid holds only its '(no parts match)' heading and part_pick is left alone:
    # an empty identifier is a heading to Blender, not a value, and assigning '' raises TypeError from inside
    # the filter's update callback. The next filter that shows anything sets it again above.


_hold = {'on': False}   # set while several filter properties are reset together, so the recount runs once, after


def filter_changed(self, context):
    if not _hold['on']:
        refresh_filters(self)
        refresh_pick_items(self)


def group_changed(self, context):
    """A type was chosen: the category menu shrinks to that type's, so a category from another type must go.

    The category is read and reset here, while the menu still lists it: once the menu has been relisted
    without it the property reads as '' and Blender complains about every access until it is set again.
    """
    if self.category != 'All' and self.category not in type_categories(self, self.group):
        self.category = 'All'   # whose own update recounts and refills the grid
    else:
        filter_changed(self, context)


def clear_filters(st):
    """Back to every part: all types, all categories, all packs, no name filter."""
    _hold['on'] = True
    try:
        st.group = st.category = st.pack = 'All'
        st.search = ''
    finally:
        _hold['on'] = False
    filter_changed(st, None)


def resync(st):
    """Bring the menus, the counts and the picture grid back to a filter that moved without its callbacks.

    Undo, redo and File > Open put the type, category, pack and name back and run no update callback, while
    the menus, counts and grid are module state that only those callbacks rebuild. Left alone the panel shows
    one filter's menus and numbers over another filter's list, and the next click does not mend it.
    """
    # A choice is stored as a number and reads as '' while its menu does not list it, so before anything is
    # read every menu lists everything these parts name. refresh_filters narrows and counts them again below.
    _counts['order'] = type_order(st.parts, dict.fromkeys(_counts['order']))
    _enum_cache['groups'] = [('All', 'All', '', 0)] + [(g, g, '', _numbered('groups', g)) for g in _counts['order']]
    for kind, names in (('categories', {it.category for it in st.parts}), ('packs', {it.pack for it in st.parts})):
        _enum_cache[kind] = [('All', 'All', '', 0)] + [(n, n, '', _numbered(kind, n)) for n in sorted(names)]
    _hold['on'] = True
    try:
        for choice in ('group', 'pack', 'category'):
            if not getattr(st, choice):
                setattr(st, choice, 'All')   # these parts no longer name it; left blank it filters nothing and warns on every redraw
        if st.category != 'All' and st.category not in type_categories(st, st.group):
            st.category = 'All'   # the rule group_changed keeps, for a state that did not come through it
    finally:
        _hold['on'] = False
    filter_changed(st, None)


@persistent
def state_restored(*_):
    """After File > Open, undo and redo: every scene's filter is looked at again, the one on screen last.

    The menus and counts are one set for the whole add-on, so the last scene recounted is the one they are
    of, and that has to be the scene the panel draws. Persistent, or opening a file would drop the handler.
    """
    current = getattr(bpy.context, 'scene', None)
    for scene in sorted(bpy.data.scenes, key=lambda s: s == current):
        try:
            resync(scene.ss_link)
        except Exception as e:   # one scene's trouble must not leave the others stale, and a handler has nowhere to report
            print(f'SS Link: the part filter of scene {scene.name!r} could not be recounted: {type(e).__name__}: {e}')


def hook_restores(on):
    """Hang state_restored on File > Open, undo and redo, or take every one of them off again.

    Off goes by name: after Reload Scripts the function in the lists is the old module's, not this one.
    """
    for handlers in (bpy.app.handlers.load_post, bpy.app.handlers.undo_post, bpy.app.handlers.redo_post):
        if on:
            handlers.append(state_restored)
            continue
        for h in [h for h in handlers if (getattr(h, '__module__', None), getattr(h, '__name__', None)) == (__name__, 'state_restored')]:
            handlers.remove(h)


def pick_changed(self, context):
    """A picture was chosen: make that part the list's active row, which Add at Cursor reads."""
    chosen = self.part_pick
    idx = next((n for ident, *_, n in _pick_items if ident == chosen), None) if chosen else None
    if idx is not None and idx != self.part_index:
        self.part_index = idx


def index_changed(self, context):
    """A list row was chosen: show it in the picture grid when the filter includes it."""
    if self.part_index < len(self.parts):
        asset = self.parts[self.part_index].asset
        if any(ident == asset for ident, *_ in _pick_items):
            self.part_pick = asset


def fill_row(it, m, group_categories=None):
    it.name, it.asset, it.category, it.pack, it.proxy = m['name'], m['asset'], m['category'], m['pack'], m.get('proxy', '')
    it.thumb, it.size, it.triangles = m.get('thumb', ''), size_label(m), int(m.get('triangles', 0))
    # A catalogue written before ss_prefabs knew types names none: the category decides.
    it.group = m.get('group') or group_of(m['category'], group_categories)
    it.in_game = core.loaded_by_game(m['asset'])


def show_row(st, m):
    """Put one catalogue or sent row in the list (or renew the row it has), and make it the highlighted part.

    For Send to Unreal: a mesh that has just become an asset is a part from that moment, without the owner
    pressing Load Catalogue again and losing the filter they had."""
    index = next((i for i, it in enumerate(st.parts) if it.asset == m['asset']), None)
    if index is None:
        index = len(st.parts)
        st.parts.add()
    fill_row(st.parts[index], m, (core._catalog['data'] or {}).get('group_categories'))
    filter_changed(st, None)
    if part_visible(st.parts[index], *current_filter(st)):
        st.part_index = index
    return index


class SSPartItem(bpy.types.PropertyGroup):
    asset: StringProperty()
    group: StringProperty()       # the type above the category: Building, Decoration, ...
    category: StringProperty()
    pack: StringProperty()
    proxy: StringProperty()
    thumb: StringProperty()       # thumbnail path relative to the library, once one is rendered
    size: StringProperty()        # 'W x D x H m'
    triangles: IntProperty()
    in_game: BoolProperty()       # the game's C++ loads this mesh by name: fixing it changes what a player sees


class SSLinkState(bpy.types.PropertyGroup):
    parts: CollectionProperty(type=SSPartItem)
    part_index: IntProperty(default=0, update=index_changed)
    part_pick: EnumProperty(name='Part', items=pick_items, update=pick_changed)
    group: EnumProperty(name='Type', items=group_items, update=group_changed,
                        description='Show one type of part; the category menu then lists only the categories of that type')
    category: EnumProperty(name='Category', items=category_items, update=filter_changed)
    pack: EnumProperty(name='Pack', items=pack_items, update=filter_changed)
    # The list has a name filter of its own, but it belongs to the list and nothing else can read it; this
    # one narrows the list, the picture grid and the counts together.
    search: StringProperty(name='Name', update=filter_changed, options={'TEXTEDIT_UPDATE'},
                           description='Show only parts whose name contains every word typed here. An asset path pasted here '
                                       '(click a card in the visual browser to copy one) finds that part')
    prefab: EnumProperty(name='Prefab', items=prefab_items)
    save_category: StringProperty(name='Category', default='Decor')
    save_name: StringProperty(name='Name', default='NewPrefab')
    live: BoolProperty(name='Live', default=False, description='Push moves to the editor twice a second')
    status: StringProperty(default='not connected')


# ---------------------------------------------------------------- operators
class SSLINK_OT_load_catalog(bpy.types.Operator):
    bl_idname = 'ss_link.load_catalog'
    bl_label = 'Load Catalogue'
    bl_description = 'Read Artifacts/PrefabLibrary/catalog.json written by the editor'

    def execute(self, context):
        st = context.scene.ss_link
        try:
            data = core.load_catalog(force=True)
        except RuntimeError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        _previews['missing'].clear()   # thumbnails rendered since the last load may exist now
        core.game_loaded_packages(force=True)
        st.parts.clear()
        # The catalogue's rows and, after them, the meshes sent from here that it does not list yet. Within a
        # category what the game loads comes first: of three look-alike hazard meshes, that is the one to fix.
        rows = core.merged_rows(data)
        for m in sorted(rows, key=lambda r: (r['category'], not core.loaded_by_game(r['asset']), r['name'])):
            fill_row(st.parts.add(), m, data.get('group_categories'))
        _counts['order'] = type_order(st.parts, data.get('group_categories'))
        clear_filters(st)   # which counts the parts, fills the three menus and the picture grid
        refresh_prefab_items()
        thumbs = sum(1 for it in st.parts if it.thumb)
        sent = len(rows) - len(data['meshes'])
        st.status = (f'catalogue: {len(st.parts)} parts, {len(_counts["groups"])} types, {len(_enum_cache["categories"]) - 1} categories, '
                     f'{len(_enum_cache["packs"]) - 1} packs, {thumbs} thumbnails' + (f', {sent} sent from here' if sent else ''))
        return {'FINISHED'}


class SSLINK_OT_add_part(bpy.types.Operator):
    bl_idname = 'ss_link.add_part'
    bl_label = 'Add at Cursor'
    bl_description = 'Place a proxy of the highlighted part at the 3D cursor'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        st = context.scene.ss_link
        if not st.parts or st.part_index >= len(st.parts):
            self.report({'ERROR'}, 'load the catalogue and pick a part')
            return {'CANCELLED'}
        it = st.parts[st.part_index]
        obj = core.add_part(it.asset)
        core.deselect_all(context)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}


# ---------------------------------------------------------------- the list
class SSLINK_UL_parts(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        icon_id = get_icon(item.thumb)
        if icon_id:
            row.label(text=item.name, icon_value=icon_id)
        else:
            row.label(text=item.name, icon='MESH_CUBE' if item.proxy else 'CUBE')
        if item.in_game:
            row.label(text='', icon='CHECKMARK')   # the info box under the list says what the tick means
        row.label(text=item.size)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        st = context.scene.ss_link
        flags = bpy.types.UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, items, 'name') if self.filter_name \
            else [self.bitflag_filter_item] * len(items)
        visible = current_filter(st)
        if visible != ('All', 'All', 'All', ()):
            flags = [f if part_visible(it, *visible) else 0 for f, it in zip(flags, items)]
        return flags, []


classes = (SSPartItem, SSLinkState, SSLINK_OT_load_catalog, SSLINK_OT_add_part, SSLINK_UL_parts)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.ss_link = PointerProperty(type=SSLinkState)
    refresh_prefab_items()
    hook_restores(True)


def unregister():
    hook_restores(False)
    clear_previews()
    del bpy.types.Scene.ss_link
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
