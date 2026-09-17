"""The type filter for the parts library: browse by what a thing is for before what it is called.

The owner reaches for "all building materials" or "all decorations" first, and only then for walls or
lamps. The catalogue puts every category under one type (Building, Decoration, Exterior & Space, Ships,
Characters & Robots, Game Objects, Misc); this module draws them as a row of toggle buttons with counts,
the name filter under them, and how many parts the whole filter leaves.

The state (scene.ss_link.group and .search) and the filter itself live in library.py, next to the list
and the picture grid they narrow; choosing a type there also shrinks the category menu to that type's
categories. What is here is the drawing, and the one button that undoes every filter at once.

The interface every feature module shares:
  register() / unregister()   called with the rest of the add-on, after library.py and before panel.py
                              (unregister in the reverse order).
  draw(layout, context)       called by the panel inside its Parts library box, above the category menu, the
                              picture grid and the list this filter narrows. Draws nothing until a catalogue is
                              loaded.
"""
import bpy

from . import library

COLUMNS = 2   # type buttons per row: 'Characters & Robots (2)' has to stay readable in a narrow sidebar


class SSLINK_OT_clear_filters(bpy.types.Operator):
    bl_idname = 'ss_link.clear_filters'
    bl_label = 'Show Everything'
    bl_description = 'Back to all types, all categories, all packs and no name filter'

    def execute(self, context):
        st = context.scene.ss_link
        try:
            library.clear_filters(st)
        except Exception as e:
            self.report({'ERROR'}, f'{type(e).__name__}: {e}')
            return {'CANCELLED'}
        return {'FINISHED'}


def draw(layout, context):
    st = context.scene.ss_link
    if not st.parts:
        return   # nothing to sort by type before the catalogue is loaded, and no box says that best
    known = library.counts_known(st)
    grid = layout.grid_flow(row_major=True, columns=COLUMNS, even_columns=True, even_rows=True, align=True)
    for ident, *_ in library.group_items(st, context):
        cell = grid.row(align=True)
        # A type the pack and name filter leave nothing of is greyed, but never the chosen one: it is the way out.
        cell.enabled = not known or ident in ('All', st.group) or library.type_count(ident) > 0
        cell.prop_enum(st, 'group', ident)
    layout.prop(st, 'search', text='', icon='VIEWZOOM')
    row = layout.row(align=True)
    row.label(text=library.shown_label(st), icon='FILTER')
    # Apart from the name field, whose own x only empties the name: this one undoes the type, category and pack too.
    undo = row.row(align=True)
    undo.enabled = library.current_filter(st) != ('All', 'All', 'All', ())
    undo.operator('ss_link.clear_filters', text='Show All', icon='LOOP_BACK')


classes = (SSLINK_OT_clear_filters,)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
