"""The live connection to the open Unreal editor: remote execution, push, pull and the live timer.

Transport is the engine's own remote_execution.py, loaded from the engine install; the editor side of
every call is Content/Python/ss_prefabs.py.
"""
import json
import time
import uuid

import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty

from . import core


class EditorLink:
    """One remote-execution connection to the open editor, made on demand."""

    def __init__(self):
        self.module = None
        self.rex = None
        self.node = None
        self.last_error = ''

    def _load_module(self):
        if self.module:
            return self.module
        root = core.engine_root()
        if not root:
            raise RuntimeError('engine not found; set the engine root in the add-on preferences')
        self.module = core.import_by_path('ue_remote_execution', root / core.REMOTE_EXEC)
        return self.module

    def connect(self, timeout=4.0):
        mod = self._load_module()
        self.disconnect()
        rex = mod.RemoteExecution()
        rex.start()
        deadline = time.time() + timeout
        nodes = []
        while time.time() < deadline:
            nodes = rex.remote_nodes
            if nodes:
                break
            time.sleep(0.1)
        if not nodes:
            rex.stop()
            raise RuntimeError('Unreal editor not found: open the project in Unreal, then press Connect '
                               '(the first time after these tools arrived, Unreal has to be restarted once)')
        node = next((n for n in nodes if 'SpaceSurvival' in str(n.get('project_name', ''))), nodes[0])
        rex.open_command_connection(node['node_id'])
        self.rex, self.node = rex, node
        return node

    def disconnect(self):
        if self.rex:
            try:
                self.rex.stop()
            except Exception:
                pass
        self.rex = self.node = None

    @property
    def connected(self):
        return bool(self.rex and self.rex.has_command_connection())

    def run(self, code):
        """Run code in the editor; returns the last line it printed (JSON by convention)."""
        if not self.connected:
            self.connect()
        try:
            result = self.rex.run_command(code, unattended=True, exec_mode=self.module.MODE_EXEC_FILE)
        except Exception as e:
            self.disconnect()
            raise RuntimeError(f'editor link dropped: {e}')
        if not result.get('success'):
            raise RuntimeError('editor error: ' + '\n'.join(o.get('output', '') for o in result.get('output', []) if o.get('type') != 'Info'))
        lines = [o['output'].strip() for o in result.get('output', []) if o.get('type') == 'Info' and o.get('output', '').strip()]
        return lines[-1] if lines else ''

    def call(self, expr):
        """Evaluate an ss_prefabs expression in the editor and return its JSON result."""
        out = self.run('import json, ss_prefabs\nprint(json.dumps(' + expr + '))')
        try:
            return json.loads(out)
        except ValueError:
            return out


link = EditorLink()
_last_sent = core.pushed_links   # link id -> (asset, matrix signature); core.linked_objects asks it, so core holds it


@persistent
def file_loaded(*_):
    """After File > Open, New and Revert: forget what was pushed, and switch Live off.

    What was pushed is remembered so that Live can remove the actor of a part deleted here. It is this
    session's memory of THIS file: carried into another .blend, none of the first file's links exist
    there, and the first Live tick would read every one as deleted and remove its actor from the open
    level. Forgotten, the worst a reopened file does is move its own actors to where its parts are.
    Live itself is saved with the scene while its timer is not, so a file saved with Live on would
    reopen showing it pressed and doing nothing.
    """
    core.pushed_links.clear()
    _remove_asked['links'] = None
    for scene in bpy.data.scenes:
        try:
            if scene.ss_link.live:
                scene.ss_link.live = False
                scene.ss_link.status = 'live off (a file was opened)'
        except AttributeError:   # the state is not registered, or not yet
            pass


def hook_file_loads(on):
    """Hang file_loaded on load_post, or take it off; by name, as library.hook_restores does and for its reason."""
    handlers = bpy.app.handlers.load_post
    for h in [h for h in handlers if (getattr(h, '__module__', None), getattr(h, '__name__', None)) == (__name__, 'file_loaded')]:
        handlers.remove(h)
    if on:
        handlers.append(file_loaded)


def link_payload(objects):
    out = []
    owners = {}
    for candidate in sorted(core.tagged_objects(), key=lambda obj: obj.name):
        if candidate.get(core.PROP_LINK):
            owners.setdefault(candidate[core.PROP_LINK], candidate)
    for o in objects:
        if not o.get(core.PROP_LINK) or owners.get(o[core.PROP_LINK], o) != o:
            o[core.PROP_LINK] = uuid.uuid4().hex
            owners[o[core.PROP_LINK]] = o
        row = {'link': o[core.PROP_LINK], 'asset': o[core.PROP_ASSET], 'name': o.name, 'matrix': core.to_ue_rows(o.matrix_world)}
        if o.get(core.PROP_MATERIALS):
            row['materials'] = json.loads(o[core.PROP_MATERIALS])
        from . import surfaces
        surfaces.add_to_record(o, row)
        out.append(row)
    return out


def push(objects, remove=()):
    payload = {'objects': link_payload(objects), 'remove': list(remove)}
    if bpy.context.scene.get('ss_target_map'):
        payload['target_map'] = bpy.context.scene['ss_target_map']
    summary = link.call('ss_prefabs.apply_link(' + repr(json.dumps(payload)) + ')')
    for row in payload['objects']:
        _last_sent[row['link']] = signature(row)
    for r in remove:
        _last_sent.pop(r, None)
    return summary


def signature(row):
    return (row['asset'], tuple(round(v, 4) for r in row['matrix'] for v in r), row.get('name'),
            json.dumps(row.get('materials', []), sort_keys=True), json.dumps(row.get('surface_overrides', {}), sort_keys=True))


def pull():
    from . import surfaces
    data = link.call('ss_prefabs.pull_selection()')
    # Every tagged object, a game scene's included: an actor pulled back must move the part that carries its
    # link, not arrive as a second copy of it.
    by_link = {o[core.PROP_LINK]: o for o in core.tagged_objects() if o.get(core.PROP_LINK)}
    made, moved = 0, 0
    col = core.ensure_collection('SS Pulled')
    for row in data.get('objects', []):
        m = core.from_ue_rows(row['matrix'])
        o = by_link.get(row['link'])
        if o and o[core.PROP_ASSET] == row['asset']:
            o.matrix_world = m
            moved += 1
        else:
            o = core.add_part(row['asset'], m, col, name=row.get('name'), link=row['link'], materials=row.get('materials'))
            made += 1
        o[core.PROP_MATERIALS] = json.dumps(row.get('materials') or [])
        for slot in o.material_slots:
            if slot.material and slot.material.get(surfaces.MARKER):
                slot.link = 'DATA'
        surfaces.restore(o, row.get('surface_overrides'))
    for row in data.get('objects', []):
        _last_sent[row['link']] = signature(dict(row, matrix=core.to_ue_rows(core.from_ue_rows(row['matrix']))))
    return {'created': made, 'moved': moved}


LIVE_REMOVE_CAP = 12                # actors one Live tick removes without asking
_remove_asked = {'links': None}     # the missing links Live stopped over; pressing Live again is the owner's yes to exactly those


def live_tick():
    st = bpy.context.scene.ss_link
    if not st.live:
        return None
    try:
        objects = core.linked_objects()
        present = {o[core.PROP_LINK] for o in objects if o.get(core.PROP_LINK)}
        changed = [o for o in objects if signature(link_payload([o])[0]) != _last_sent.get(o.get(core.PROP_LINK))]
        gone = [l for l in list(_last_sent) if l not in present]
        # Deleting a part here removes its actor there, which is the point of Live; but nothing asks, and the only
        # sign is '-N' in the status line. A tick that would remove many at once stops and says so first: whatever
        # made that many parts vanish (a wrong Delete, a collection unlinked) may not have meant the level.
        if len(gone) > LIVE_REMOVE_CAP and _remove_asked['links'] != sorted(gone):
            _remove_asked['links'] = sorted(gone)
            st.live = False
            st.status = (f'live stopped: {len(gone)} pushed parts are no longer in this file. Press Live again to remove their actors '
                         f'from the Unreal level too; or undo (Ctrl+Z) to bring the parts back first')
            return None
        _remove_asked['links'] = None
        if changed or gone:
            s = push(changed, gone)
            st.status = f'live: +{s.get("created", 0)} ~{s.get("moved", 0)} -{s.get("removed", 0)}  ({time.strftime("%H:%M:%S")})'
    except Exception as e:
        st.live = False
        st.status = f'live stopped: {e}'
        return None
    return 0.5


# ---------------------------------------------------------------- operators
class SSLINK_OT_connect(bpy.types.Operator):
    bl_idname = 'ss_link.connect'
    bl_label = 'Connect'
    bl_description = 'Find the open editor over Python remote execution'

    def execute(self, context):
        st = context.scene.ss_link
        try:
            node = link.connect()
            st.status = f'connected: {node.get("project_name", "?")} on {node.get("machine", "?")}'
        except Exception as e:
            st.status = str(e)
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}


class SSLINK_OT_push(bpy.types.Operator):
    bl_idname = 'ss_link.push'
    bl_label = 'Push'
    bl_description = 'Create or move the matching actors in the open level'
    selected_only: BoolProperty(default=True)

    def execute(self, context):
        st = context.scene.ss_link
        objects = core.linked_objects(self.selected_only)
        if not objects:
            self.report({'ERROR'}, 'no tagged parts selected')
            return {'CANCELLED'}
        try:
            s = push(objects)
        except Exception as e:
            st.status = str(e)
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        st.status = f'pushed {len(objects)}: +{s.get("created", 0)} ~{s.get("moved", 0)}' + (f' errors {s["errors"]}' if s.get('errors') else '')
        return {'FINISHED'}


class SSLINK_OT_pull(bpy.types.Operator):
    bl_idname = 'ss_link.pull'
    bl_label = 'Pull Selection'
    bl_description = "Mirror the editor's selected actors here as proxies"

    def execute(self, context):
        st = context.scene.ss_link
        try:
            s = pull()
        except Exception as e:
            st.status = str(e)
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        st.status = f'pulled: +{s["created"]} ~{s["moved"]}'
        return {'FINISHED'}


class SSLINK_OT_live(bpy.types.Operator):
    bl_idname = 'ss_link.live'
    bl_label = 'Live'
    bl_description = 'Keep the editor in step with this scene while on'

    def execute(self, context):
        st = context.scene.ss_link
        st.live = not st.live
        if st.live:
            try:
                if not link.connected:
                    link.connect()
            except Exception as e:
                st.live = False
                st.status = str(e)
                self.report({'ERROR'}, str(e))
                return {'CANCELLED'}
            if not bpy.app.timers.is_registered(live_tick):
                bpy.app.timers.register(live_tick, first_interval=0.2)
            st.status = 'live'
        else:
            st.status = 'live off'
        return {'FINISHED'}


classes = (SSLINK_OT_connect, SSLINK_OT_push, SSLINK_OT_pull, SSLINK_OT_live)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    core.pushed_links.clear()   # a re-enabled add-on starts as a new session does
    hook_file_loads(True)


def unregister():
    hook_file_loads(False)
    link.disconnect()
    if bpy.app.timers.is_registered(live_tick):
        bpy.app.timers.unregister(live_tick)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
