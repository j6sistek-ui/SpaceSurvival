"""The sidebar panel: 3D Viewport > Sidebar (N) > SS Link.

The panel draws the add-on's own boxes (editor, parts library, visual browser, prefabs) and then hands
each feature module a box of its own to draw into. The type filter (groups.py) is a feature module too, but
it draws inside the Parts library box, right above the list and the picture grid it narrows: browsing by
type is the first thing the library is for, and three boxes further down it filtered a list out of sight.
"""
import bpy

from . import core, library, groups, send, scenes

# Feature modules in the order their boxes appear: (module, box title, title icon).
FEATURES = ((send, 'Send to Unreal', 'EXPORT'), (scenes, 'Scenes', 'SCENE_DATA'))


class LazyBox:
    """A feature's titled box, made only when the feature draws into it.

    Blender draws a box the moment it is asked for, so handing a feature a real box would leave an empty
    frame in the panel whenever it has nothing to show (a stub never has). This stands in for the box and
    makes the real one, title first, on the first use of any layout attribute; from then on everything
    goes straight through to it.
    """

    def __init__(self, parent, title, icon):
        # Through __dict__, because __setattr__ below belongs to the layout.
        self.__dict__.update(_parent=parent, _title=title, _icon=icon, _box=None)

    @property
    def drawn(self):
        return self._box is not None

    def real(self):
        """The real UILayout box, for the rare call that needs one as an argument."""
        if self._box is None:
            box = self._parent.box()
            box.label(text=self._title, icon=self._icon)
            self.__dict__['_box'] = box
        return self._box

    def __getattr__(self, name):
        # Only reached for names this object lacks, which is everything a UILayout has. Python's own
        # dunder probes (copy, pickle, ...) must not conjure a box.
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self.real(), name)

    def __setattr__(self, name, value):
        setattr(self.real(), name, value)


def draw_features(layout, context):
    """Each feature's draw() in its own box; returns the titles of the boxes that were drawn."""
    drawn = []
    for module, title, icon in FEATURES:
        box = LazyBox(layout, title, icon)
        try:
            module.draw(box, context)
        except Exception as e:
            # One feature failing must not take the boxes below it off the panel; say so where it would have been.
            box.real().label(text=f'{type(e).__name__}: {e}', icon='ERROR')
        if box.drawn:
            drawn.append(title)
    return drawn


class SSLINK_PT_panel(bpy.types.Panel):
    bl_label = 'SpaceSurvival Live Link'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SS Link'

    def draw(self, context):
        st = context.scene.ss_link
        lay = self.layout
        root = core.project_root()
        if not root:
            lay.label(text='Set the project root in Preferences > Add-ons', icon='ERROR')
        stale = core.version_note()
        if stale:
            core.draw_wrapped(lay.box(), stale, context, icon='ERROR')
        box = lay.box()
        box.label(text='Editor', icon='LINKED')
        row = box.row(align=True)
        row.operator('ss_link.connect', icon='PLUGIN')
        row.operator('ss_link.live', icon='PLAY' if not st.live else 'PAUSE', depress=st.live)
        row = box.row(align=True)
        row.operator('ss_link.push', text='Push Selected').selected_only = True
        row.operator('ss_link.push', text='Push All').selected_only = False
        box.operator('ss_link.pull', icon='IMPORT')
        box.label(text=st.status)
        box = lay.box()
        box.label(text='Parts library', icon='ASSET_MANAGER')
        box.operator('ss_link.load_catalog', icon='FILE_REFRESH')
        try:
            groups.draw(box, context)   # the type buttons, the name field and '79 of 458 parts'; nothing before a catalogue is loaded
        except Exception as e:
            box.label(text=f'{type(e).__name__}: {e}', icon='ERROR')
        col = box.column(align=True)
        col.prop(st, 'category', text='')
        col.prop(st, 'pack', text='')
        box.template_icon_view(st, 'part_pick', show_labels=True, scale=5.0, scale_popup=7.0)
        note = library.grid_note(st)
        if note:
            core.draw_wrapped(box, note, context, icon='INFO')
        box.template_list('SSLINK_UL_parts', '', st, 'parts', st, 'part_index', rows=8)
        if st.parts and st.part_index < len(st.parts):
            it = st.parts[st.part_index]
            info = box.box()
            icon_id = library.get_icon(it.thumb)
            if icon_id:
                info.template_icon(icon_value=icon_id, scale=7.0)
            info.label(text=it.name, icon='MESH_CUBE' if it.proxy else 'CUBE')
            col = info.column(align=True)
            col.label(text=it.pack, icon='PACKAGE')
            col.label(text=it.size, icon='FIXED_SIZE')
            col.label(text=f'{it.triangles:,} triangles', icon='MESH_DATA')
            if it.in_game:
                col.label(text='in game: the game loads this mesh by name', icon='CHECKMARK')
        box.operator('ss_link.add_part', icon='ADD')
        # Also in the Send to Unreal box; here it sits under the list it can read its part from.
        box.operator('ss_link.edit_mesh', icon='EDITMODE_HLT')
        box = lay.box()
        box.label(text='Visual browser', icon='IMAGE_DATA')
        row = box.row(align=True)
        row.operator('ss_link.open_browser', icon='URL')
        row.operator('ss_link.build_browser', text='', icon='FILE_REFRESH')
        row = box.row(align=True)
        row.operator('ss_link.render_thumbnails', icon='RENDER_STILL')
        row.operator('ss_link.reload_thumbnails', text='', icon='FILE_REFRESH')
        box = lay.box()
        box.label(text='Prefabs', icon='OUTLINER_COLLECTION')
        row = box.row(align=True)
        row.prop(st, 'prefab', text='')
        row.operator('ss_link.refresh_prefabs', text='', icon='FILE_REFRESH')
        box.operator('ss_link.load_prefab', icon='IMPORT')
        col = box.column(align=True)
        col.prop(st, 'save_category')
        col.prop(st, 'save_name')
        box.operator('ss_link.save_prefab', icon='EXPORT')
        draw_features(lay, context)
        version = '.'.join(str(v) for v in core.running_version())
        lay.label(text=f'SS Live Link v{version}' + ('' if not stale else ' (out of date)'))


classes = (SSLINK_PT_panel,)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
