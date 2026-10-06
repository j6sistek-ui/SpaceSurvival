"""Two inspected owner-preview compatibility repairs; the lead owns saving.

No map load/save, vendor asset edits, lighting changes or material graph edits.
The placed additive entrance frame uses the normal raster fallback; the owned
Graphite master records its already-required Nanite usage for non-editor use.
"""
import hashlib
from pathlib import Path

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
FRAME = 'Doors/Main threshold/Frame'
MESH = ('/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'
        'SM_Door400X250_V1_Part1_SM_Door400X250_V1_Part1.'
        'SM_Door400X250_V1_Part1_SM_Door400X250_V1_Part1')
LIGHT = '/Game/StarterBundle/ModularSci_Comm/Materials/M_Base_SolidLight.M_Base_SolidLight'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite.M_OutpostGraphite'
MATERIALS = (LIGHT,
             '/Game/OutpostSandbox/Materials/MI_Balanced_7b7ccec0ddba.MI_Balanced_7b7ccec0ddba',
             LIGHT,
             '/Game/OutpostSandbox/Materials/MI_Balanced_ea0968af1927.MI_Balanced_ea0968af1927',
             LIGHT,
             '/Game/OutpostSandbox/Materials/MI_Balanced_75e8746cd43c.MI_Balanced_75e8746cd43c',
             LIGHT)


def _pose(transform):
    return [list(transform.translation.to_tuple()), list(transform.rotation.to_tuple()),
            list(transform.scale3d.to_tuple())]


def _state(actor, component):
    return {'actor_pose': _pose(actor.get_actor_transform()),
            'component_pose': _pose(component.get_world_transform()),
            'mesh': component.static_mesh.get_path_name(),
            'materials': [m.get_path_name() if m else None for m in component.get_materials()],
            'actor_collision': actor.get_actor_enable_collision(),
            'component_collision': str(component.get_collision_enabled()),
            'hidden': bool(actor.get_editor_property('hidden')),
            'visible': bool(component.get_editor_property('visible'))}


def apply(ctx):
    import unreal as u
    command = u.SystemLibrary.get_command_line().lower()
    if '-renderoffscreen' not in command and '-nullrhi' not in command:
        raise RuntimeError('Compatibility repair requires a dedicated headless editor')
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    if editor.get_game_world() or world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Compatibility repair is restricted to the owner-preview editor map')
    actors = [a for a in ctx.actors if a.get_actor_label() == FRAME]
    if len(actors) != 1:
        raise RuntimeError('Expected the one inspected main-threshold frame')
    actor = actors[0]
    components = list(actor.get_components_by_class(u.StaticMeshComponent))
    if len(components) != 1 or components[0].get_name() != 'StaticMeshComponent0':
        raise RuntimeError('Main-threshold frame component membership changed')
    component = components[0]
    before = _state(actor, component)
    if before['mesh'] != MESH or tuple(before['materials']) != MATERIALS:
        raise RuntimeError('Inspected entrance mesh/material slots changed; stop before editing')
    if not component.static_mesh.get_editor_property('nanite_settings').get_editor_property('enabled'):
        raise RuntimeError('Inspected entrance source is no longer Nanite-enabled')
    additive = ctx.asset(LIGHT)
    graphite = ctx.asset(GRAPHITE)
    if (not isinstance(additive, u.Material)
            or additive.get_editor_property('blend_mode') != u.BlendMode.BLEND_ADDITIVE):
        raise RuntimeError('Inspected entrance material is no longer the additive master')
    if not isinstance(graphite, u.Material) or graphite.get_path_name() != GRAPHITE:
        raise RuntimeError('Expected the project-owned Graphite master, not an instance/vendor asset')

    # All guards precede edits. Caller saves only the owner map and dirty_assets;
    # even the source mesh and additive material files must remain byte-identical.
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    paths = {p: root / ('Content/' + p.split('.')[0][6:] + '.uasset')
             for p in {MESH, *MATERIALS, GRAPHITE}}
    hashes = {p: hashlib.sha256(f.read_bytes()).hexdigest() for p, f in paths.items()}
    was_disallowed = bool(component.get_editor_property('disallow_nanite'))
    edit = u.MaterialEditingLibrary
    usage = u.MaterialUsage.MATUSAGE_NANITE
    had_usage = bool(edit.has_material_usage(graphite, usage))

    component.set_editor_property('disallow_nanite', True)
    edit.set_base_material_usage(graphite, usage, True)
    errors = edit.recompile_material(graphite)
    if errors or not edit.has_material_usage(graphite, usage):
        raise RuntimeError('Owned Graphite Nanite usage compilation/readback failed: ' + repr(errors))
    if not component.get_editor_property('disallow_nanite') or _state(actor, component) != before:
        raise RuntimeError('Entrance compatibility repair failed or changed unrelated component state')
    if any(hashlib.sha256(paths[p].read_bytes()).hexdigest() != digest for p, digest in hashes.items()):
        raise RuntimeError('Compatibility helper unexpectedly changed a source file on disk')
    rows = [{'kind': 'entrance_additive_nanite_fallback', 'actor': FRAME,
             'component': component.get_name(), 'before': was_disallowed, 'after': True,
             'preserved_state': before},
            {'kind': 'owned_graphite_nanite_usage', 'asset': GRAPHITE,
             'before': had_usage, 'after': True, 'material_graph_unchanged': True}]
    ctx.records.extend(rows)
    return {'module': 'station_compatibility', 'changes': rows,
            # Always save: the editor may have auto-enabled this flag in memory.
            'dirty_assets': [GRAPHITE], 'source_sha256_before_save': hashes,
            'vendor_assets_unchanged': True, 'lighting_unchanged': True,
            'acceptance': 'Save owned map/material, then confirm warnings absent in a fresh process.'}
