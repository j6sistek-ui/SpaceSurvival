"""Build an editable Blender scene from the private Unreal sandbox's linked mesh export.

Run in background Blender with --project ROOT --input JSON --output BLEND.
Unreal keeps lights, effects and Blueprint logic; this file carries mesh placements.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).parent))
from ss_live_link import core


def build(root, source, output):
    if output.exists():
        raise FileExistsError(f'Keep your edits: choose a new output file, {output} exists')
    data = json.loads(source.read_text(encoding='utf-8'))
    core.project_root = lambda: root
    catalog = core.load_catalog(force=True)
    entries = {row['asset']: row for row in catalog['meshes']}
    missing = sorted({row['asset'] for row in data['objects']
                      if row['asset'] not in ('/Engine/BasicShapes/Cube.Cube', '/Engine/BasicShapes/Plane.Plane') and
                      (row['asset'] not in entries or not entries[row['asset']].get('proxy'))})
    if missing:
        raise RuntimeError(f'Refresh the library before building this scene: {missing}')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # The engine plane is 100 cm square, not the generic missing-proxy cube.
    plane = bpy.data.meshes.new('SSProxy:/Engine/BasicShapes/Plane.Plane')
    plane.from_pydata([(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)], [], [(0, 1, 2, 3)])
    plane.use_fake_user = True
    # Import each proxy before thousands of placements make Blender operators expensive.
    for asset in sorted({row['asset'] for row in data['objects']}):
        if asset in entries:
            core.proxy_mesh(entries[asset])
    scene = bpy.context.scene
    scene.name = 'Building Sandbox'
    scene['ss_target_map'] = data['target_map']
    scene['ss_sandbox_source'] = str(source)
    scene.unit_settings.system = 'METRIC'
    for index, row in enumerate(data['objects']):
        col = core.ensure_collection(row.get('area', 'Sandbox'))
        core.add_part(row['asset'], core.from_ue_rows(row['matrix']), col,
                      name=row['name'], link=row['link'], materials=row.get('materials'))
        if index % 250 == 0:
            print(f'SS_SANDBOX_BLEND_PROGRESS {index}/{len(data["objects"])}', flush=True)
    note = bpy.data.texts.new('START HERE')
    note.write('Building sandbox: mesh placements linked to ' + data['target_map'] + '\n'
               'Open that level in Unreal, then SS Link > Connect. Select changed parts and Push.\n'
               'Save this .blend and save the Unreal level after review. Keep Live off initially.\n'
               'Unreal retains Blueprint actors, lights, effects and original materials.\n'
               'Blender proxies are for layout; use Unreal to judge final lighting/materials.\n')
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.clip_end = 10000
                area.spaces.active.region_3d.view_distance = 100
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
    print('SS_SANDBOX_BLEND_OK ' + json.dumps({'objects': len(data['objects']),
          'target_map': data['target_map'], 'output': str(output)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    build(args.project.resolve(), args.input, args.output)
