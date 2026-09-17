"""Self-test of Send to Unreal, Edit Mesh and Open Scene / Apply, editor side, headless, with real files.

  UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser \
      "-ExecutePythonScript=<abs path>/Scripts/TestSendScenes.py"

Needs Blender (5.2, else 5.1, else the one SS_BLENDER names): the sends it imports are made by the real
add-on, run headless through Tools/SSLiveLink/test_send_helper.py, once per step.

  send    A shape with no symmetry and two materials is sent into the category '_SelfTest'; import_outbox()
          must land it at the documented path with Blender's size (metres x 100, within 1 cm), mirrored in Y
          as ss_send.py promises and as nothing else (each material's faces where they belong, facing out,
          wound as the engine's own cube), both slots filled, and import nothing the second time. The new
          mesh gets a row in the parts catalogue (a scratch copy of it). The object is then made longer and
          sent again: the same asset must take the new size, and the file it replaced must be kept, byte
          for byte, under Backups.
  edit    A real pack mesh is duplicated (the pack asset is read, never written; its file hash is checked),
          export_for_edit() writes its GLB, Blender raises its top and adds a material slot, and the fix goes
          back through the Outbox: geometry changed, every old slot with its old material, the new slot named,
          the file as it was kept as a backup. Once for a mesh outside /Game/Blender (materials kept by
          default), once inside it with keep_materials=True. A sidecar that names a pack asset without
          being an Edit Mesh fix is refused, and an import that fails over an existing asset leaves the
          asset as its file has it.
  scenes  check_recipe() accepts the real PitStopLayout.json and refuses a part in the flight lane, a
          missing mesh, malformed numbers and a recipe with no parts, by name; fill_transforms() agrees
          with the engine's own transform maths; apply_station_recipe(target=<scratch>) builds the real
          recipe, and the same recipe as matrices only, into a scratch Blueprint whose every part sits where
          the recipe says. A copy is never built over an asset that is not an earlier copy, nor over the
          owner's layout under another spelling; a layout changed outside a recipe is refused without
          force. BP_StationVisualLayout.uasset must be byte for byte what it was (sha256), and the layout
          in memory must be the saved one again.
  clean   Every asset, Outbox and Edit file, backup, folder and receipt the test made is removed (a receipt
          only when its Request.json names one of the test's own targets: never one an open editor wrote
          meanwhile), and git status must read as it did before.

Nothing the test makes lies under /Game/SpaceSurvival, which is always cooked: a run that is killed leaves its
assets under Content/Blender and Content/_SSSelfTest, where the next run removes them.

Prints one line: SENDSCENES_TEST_OK {json} or SENDSCENES_TEST_FAIL {json}.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Content' / 'Python'))
import ss_prefabs  # noqa: E402
import ss_scenes  # noqa: E402
import ss_send  # noqa: E402

LIB = u.EditorAssetLibrary
HELPER = ROOT / 'Tools' / 'SSLiveLink' / 'test_send_helper.py'
BLENDERS = [os.environ.get('SS_BLENDER', ''), r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe',
            r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe']
BASE = ss_send.BLENDER_BASE
SENT_FOLDER = 'SelfTest'   # send.category_folder('_SelfTest'): a folder name never begins with an underscore
WEDGE = f'{BASE}/{SENT_FOLDER}/SM_SSTestWedge'
INSIDE = f'{BASE}/_SelfTest'                 # test assets under BLENDER_BASE
OUTSIDE = '/Game/_SSSelfTest'                # and outside it, where a fix keeps the asset's materials by default; not under the always-cooked /Game/SpaceSurvival
TEST_DIRS = [f'{BASE}/{SENT_FOLDER}', INSIDE, OUTSIDE]
PROBES = ['/Game/StarterBundle/ModularScifiProps/Meshes/SM_GlassDoor_A', '/Game/StarterBundle/ModularScifiProps/Meshes/SM_Wall_A_Glass',
          '/Game/SpaceSurvival/Meshes/SM_Console']
RECIPE = ROOT / '.agent' / 'local' / 'StationVisualPass' / 'PitStopLayout.json'
LAYOUT_FILE = ss_scenes._disk(ss_scenes.PACKAGE)
SCRATCH_BP = f'{INSIDE}/BP_StationLayoutScratch'
SCRATCH_BP_MATRIX = f'{INSIDE}/BP_StationLayoutScratchMatrix'

failures, results = [], {}


def check(ok, what, detail=None):
    """Record one check; the run goes on, so one log shows everything that is wrong."""
    if not ok:
        failures.append(what if detail is None else f'{what}: {detail}')
        u.log_warning(f'SENDSCENES check failed: {what}: {detail}')
    return bool(ok)


def stage(name):
    def wrap(fn):
        try:
            results[name] = fn()
        except Exception as e:
            failures.append(f'{name} stopped: {type(e).__name__}: {e}')
            results[name + '_traceback'] = traceback.format_exc()
            u.log_warning(f'SENDSCENES stage {name} stopped:\n{traceback.format_exc()}')
        return fn
    return wrap


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None


def disk_file(package):
    return ROOT / 'Content' / (package[len('/Game/'):] + '.uasset')


def git_status():
    try:
        done = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain'], capture_output=True, text=True, timeout=120)
        return sorted(done.stdout.splitlines()) if done.returncode == 0 else None
    except Exception:
        return None


def blender():
    return next((b for b in BLENDERS if b and Path(b).is_file()), None)


def run_helper(work, mode, *extra):
    out = work / f'{mode}.json'
    if out.exists():
        out.unlink()
    command = [blender(), '--background', '--factory-startup', '--python', str(HELPER), '--', '--project', str(ROOT),
               '--mode', mode, '--blend', str(work / 'wedge.blend'), '--out', str(out)] + list(extra)
    done = subprocess.run(command, capture_output=True, text=True, timeout=600)
    if not out.exists():
        raise RuntimeError(f'Blender wrote no result for {mode}: exit {done.returncode}: {(done.stdout or "")[-1500:]} {(done.stderr or "")[-500:]}')
    result = json.loads(out.read_text(encoding='utf-8'))
    if not result.get('ok'):
        raise RuntimeError(f'Blender {mode} failed: {result.get("error")}\n{result.get("traceback", "")}')
    return result


# ---------------------------------------------------------------- reading a mesh
def bounds_of(mesh):
    b = mesh.get_bounds()
    return [b.origin.x, b.origin.y, b.origin.z], [b.box_extent.x, b.box_extent.y, b.box_extent.z]


def nanite_of(mesh):
    return bool(mesh.get_editor_property('nanite_settings').get_editor_property('enabled'))


def slots_of(mesh):
    return [(str(s.material_slot_name), s.material_interface.get_path_name() if s.material_interface else '') for s in mesh.static_materials]


def sections_of(mesh):
    """Per section of LOD 0: its material's name, the box of its vertices, whether every vertex normal points away
    from that box's centre, and the winding: the sign of (triangle's geometric normal . its vertex normals)."""
    rows = []
    for section in range(mesh.get_num_sections(0)):
        verts, tris, normals = u.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, section)[:3]
        pts = [(v.x, v.y, v.z) for v in verts]
        nrm = [(n.x, n.y, n.z) for n in normals]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        centre = [(lo[i] + hi[i]) / 2 for i in range(3)]
        outward = all(sum(nrm[k][i] * (pts[k][i] - centre[i]) for i in range(3)) > 0 for k in range(len(pts)))
        signs = set()
        for t in range(0, len(tris), 3):
            a, b, c = (pts[tris[t + k]] for k in range(3))
            e1, e2 = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
            face = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
            mean = [sum(nrm[tris[t + k]][i] for k in range(3)) for i in range(3)]
            signs.add(1 if sum(face[i] * mean[i] for i in range(3)) > 0 else -1)
        material = mesh.get_material(u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_lod_material_slot(mesh, 0, section))
        rows.append({'material': material.get_name() if material else None, 'lo': lo, 'hi': hi, 'outward': outward, 'winding': sorted(signs)})
    return rows


def ue_box(lo_m, hi_m):
    """A Blender local box in metres as (lo, hi) in Unreal centimetres, by the rule ss_send.py documents: x100, Y mirrored."""
    return [lo_m[0] * 100, -hi_m[1] * 100, lo_m[2] * 100], [hi_m[0] * 100, -lo_m[1] * 100, hi_m[2] * 100]


def near(a, b, tolerance):
    return all(abs(x - y) <= tolerance for x, y in zip(a, b))


def check_shape(label, mesh, sent):
    """The mesh against what Blender measured before it sent it. Returns what was read, for the result line."""
    origin, extent = bounds_of(mesh)
    lo, hi = ue_box(sent['lo_m'], sent['hi_m'])
    size_cm = [d * 100 for d in sent['dimensions_m']]
    check(near([2 * e for e in extent], size_cm, 1.0), f'{label}: size in cm is Blender\'s dimensions x 100', ([2 * e for e in extent], size_cm))
    check(near(origin, [(lo[i] + hi[i]) / 2 for i in range(3)], 1.0), f'{label}: bounds centre is Blender\'s, Y mirrored (pivot kept, no world transform)',
          (origin, [(lo[i] + hi[i]) / 2 for i in range(3)]))
    check(near(origin, sent['sidecar_bounds_cm']['origin'], 1.0) and near(extent, sent['sidecar_bounds_cm']['extent'], 1.0),
          f'{label}: the sidecar\'s bounds_cm are the asset\'s', (origin, extent, sent['sidecar_bounds_cm']))
    return {'origin_cm': [round(v, 3) for v in origin], 'extent_cm': [round(v, 3) for v in extent]}


def check_sections(label, mesh, sent, cube_winding, own_materials=True):
    """Each material's faces against where Blender had them. own_materials: the materials came with the send, so
    the section at a slot's box must also wear the material of that name."""
    sections = sections_of(mesh)
    for slot in [s for s in sent['slots'] if s['faces']]:
        lo, hi = ue_box(slot['lo_m'], slot['hi_m'])
        found = [s for s in sections if near(s['lo'], lo, 1.0) and near(s['hi'], hi, 1.0)]
        if check(len(found) >= 1, f'{label}: the faces of {slot["material"]} are where Blender had them, Y mirrored', (lo, hi, sections)):
            check(all(f['winding'] == cube_winding for f in found), f'{label}: {slot["material"]} is wound as the engine\'s cube (not inside out)', (found, cube_winding))
            if own_materials:
                check([f['material'] for f in found] == [slot['material']], f'{label}: those faces wear {slot["material"]}', found)
    return sections


# ---------------------------------------------------------------- the outbox, shared with the owner
def outbox_only(mine):
    """None when the Outbox holds nothing but this test's sends, so import_outbox() runs exactly as the add-on
    calls it; else the test's own names, so what the owner has queued stays queued."""
    foreign = [name for name, glb, side in ss_send.queued()
               if not {glb.parent.name, f'{glb.parent.name}/{name}'} & set(mine)]
    results.setdefault('outbox_foreign', foreign)
    return list(mine) if foreign else None


def main():
    work = Path(tempfile.mkdtemp(prefix='ss_sendscenes_'))
    layout_before = sha256(LAYOUT_FILE)
    layout_mtime = LAYOUT_FILE.stat().st_mtime if LAYOUT_FILE.is_file() else None
    git_before = git_status()
    existed = {p: p.exists() for p in (ss_send.LINK, ss_send.OUTBOX, ss_send.OUTBOX / ss_send_edits(), ss_send.EDIT, ss_send.RECORD,
                                       disk_file(BASE + '/x').parent, disk_file(OUTSIDE + '/x').parent)}
    record_before = ss_send._read_record()
    receipts_before = {p.name for p in ss_scenes.RECEIPTS.glob('EditableLayout-*')} if ss_scenes.RECEIPTS.exists() else set()
    my_sends = [SENT_FOLDER]
    my_files = []   # Outbox and Edit files to take away again
    results.update(blender=blender(), engine=u.SystemLibrary.get_engine_version(), layout_sha256=layout_before)
    # The backups go to the temp folder, and the parts catalogue the editor side adds a sent mesh to is a copy in
    # there too: the owner's catalogue must never list a test mesh, and its file must be what it was afterwards.
    real_places = (ss_send.BACKUPS, ss_prefabs.LIBRARY, ss_prefabs.CATALOG, ss_prefabs.PROXIES)
    catalog_before = sha256(ss_prefabs.CATALOG)
    ss_send.BACKUPS = work / 'Backups'
    ss_prefabs.LIBRARY = work / 'PrefabLibrary'
    ss_prefabs.CATALOG, ss_prefabs.PROXIES = ss_prefabs.LIBRARY / 'catalog.json', ss_prefabs.LIBRARY / 'proxies'
    ss_prefabs.LIBRARY.mkdir(parents=True)
    if real_places[2].is_file():
        shutil.copy2(real_places[2], ss_prefabs.CATALOG)
    try:
        check(blender() is not None, 'Blender found', BLENDERS)
        check(layout_before is not None, 'BP_StationVisualLayout.uasset is on disk', str(LAYOUT_FILE))
        remove_assets()   # what a run that was killed may have left
        shutil.rmtree(ss_send.OUTBOX / SENT_FOLDER, ignore_errors=True)
        cube = u.load_asset('/Engine/BasicShapes/Cube')
        cube_winding = sections_of(cube)[0]['winding']
        check(len(cube_winding) == 1, 'the engine cube is wound one way', cube_winding)

        # ------------------------------------------------------------ a. Send to Unreal
        @stage('send')
        def _():
            out = {}
            first = run_helper(work, 'new')['sent']
            my_files.extend([first['glb'], first['sidecar']])
            check(first['target'] == WEDGE and first['asset'] == f'{WEDGE}.SM_SSTestWedge', 'the add-on targets BLENDER_BASE/<category folder>/SM_<name>', first['target'])
            check(Path(first['glb']).parent == ss_send.OUTBOX / SENT_FOLDER, 'the GLB is in the Outbox folder the editor reads', first['glb'])
            check('SSTestWedge' in ss_send.pending(), 'pending() lists the new send', ss_send.pending())
            summary = ss_send.import_outbox(only=outbox_only(my_sends))
            check(summary['imported'] == ['SSTestWedge'] and not summary['failed'], 'import_outbox() imports the send', summary)
            if not check(LIB.does_asset_exist(WEDGE), 'the static mesh exists at the documented path', WEDGE):
                return out
            mesh = u.load_asset(WEDGE)
            check(isinstance(mesh, u.StaticMesh) and disk_file(WEDGE).is_file(), 'it is a static mesh, saved', str(disk_file(WEDGE)))
            out['first'] = check_shape('send', mesh, first)
            out['sections'] = check_sections('send', mesh, first, cube_winding)
            check(all(s['outward'] for s in out['sections']), 'send: every normal points out of its box', out['sections'])
            slots = slots_of(mesh)
            check([n for n, _ in slots] == first['sidecar_materials'] and all(m.startswith(f'{BASE}/{SENT_FOLDER}/') for _, m in slots),
                  'send: both material slots are there, each with its own material beside the mesh', slots)
            check(mesh.get_num_triangles(0) == first['triangles'] == 24, 'send: the triangle count is Blender\'s', mesh.get_num_triangles(0))
            check(u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_simple_collision_count(mesh) >= 1, 'send: a collision box was added')
            check(not nanite_of(mesh), 'send: 24 triangles are not built as Nanite')
            out['slots'] = slots
            check(ss_send._read_record().get(WEDGE, {}).get('backup') is None, 'a first import replaces nothing, so it keeps nothing')
            # The mesh just sent is a part: the editor's catalogue lists it at once, so Blender finds it by type and picture.
            if ss_prefabs.CATALOG.is_file():
                row = next((m for m in ss_prefabs.load_catalog()['meshes'] if m['asset'] == f'{WEDGE}.SM_SSTestWedge'), None)
                if check(row is not None, 'the new mesh has a row in the parts catalogue'):
                    check(row['pack'] == 'Blender' and near(row['extent'], out['first']['extent_cm'], 1.0) and row['triangles'] == 24, 'with its pack and bounds', row)
                    check(not hasattr(u, 'GLTFExporter') or (ss_prefabs.LIBRARY / row.get('proxy', 'none')).is_file(), 'and a proxy for Blender', row.get('proxy'))
                    out['catalogue_row'] = {k: row.get(k) for k in ('pack', 'group', 'category', 'proxy', 'thumb')}
            check(ss_prefabs.classify('/Game/Blender/Pipes_Cables/SM_Anything.SM_Anything') == 'Pipes & Cables' and
                  ss_prefabs.classify('/Game/Blender/Doors/SM_Bracket.SM_Bracket') == 'Doors', 'a sent mesh is catalogued under the category the owner filed it in')
            saved = disk_file(WEDGE).stat().st_mtime_ns
            first_sha = sha256(disk_file(WEDGE))
            again = ss_send.import_outbox(only=outbox_only(my_sends))
            check(again['imported'] == [] and 'SSTestWedge' in again['kept'] and not again['failed'], 'a second import_outbox() with nothing changed imports nothing', again)
            check(disk_file(WEDGE).stat().st_mtime_ns == saved and 'SSTestWedge' not in ss_send.pending(), 'and leaves the asset file alone')

            second = run_helper(work, 'resend')['sent']
            check(second['target'] == WEDGE and second['hi_m'][0] > first['hi_m'][0] + 0.9, 'the changed object is sent to the same asset', (second['target'], second['hi_m']))
            summary = ss_send.import_outbox(only=outbox_only(my_sends))
            check(summary['imported'] == ['SSTestWedge'] and not summary['failed'], 'import_outbox() imports the changed send', summary)
            record = ss_send._read_record().get(WEDGE, {})
            check(record.get('status') == 'reimported' and record.get('asset') == f'{WEDGE}.SM_SSTestWedge', 'the record says it went over the asset', record)
            check(summary.get('backups') == [['SSTestWedge', record.get('backup')]] and sha256(record.get('backup') or '') == first_sha and
                  Path(record['backup']).is_relative_to(ss_send.BACKUPS), 'the file it replaced is kept under Backups, byte for byte, and Blender is told where', summary)
            if ss_prefabs.CATALOG.is_file():
                rows = [m for m in ss_prefabs.load_catalog()['meshes'] if m['asset'] == f'{WEDGE}.SM_SSTestWedge']
                check(len(rows) == 1 and abs(rows[0]['extent'][0] - 150.0) <= 1.0, 'the catalogue row took the new bounds, and is still one row', rows)
            meshes = [a for a in LIB.list_assets(f'{BASE}/{SENT_FOLDER}', recursive=True, include_folder=False) if isinstance(u.load_asset(a), u.StaticMesh)]
            check(meshes == [f'{WEDGE}.SM_SSTestWedge'], 'there is still one static mesh: over the asset, never beside it', meshes)
            mesh = u.load_asset(WEDGE)
            out['second'] = check_shape('resend', mesh, second)
            check_sections('resend', mesh, second, cube_winding)
            check(abs(out['second']['extent_cm'][0] - 150.0) <= 1.0 and abs(out['first']['extent_cm'][0] - 100.0) <= 1.0, 'the same asset path has the new bounds', out)
            check([n for n, _ in slots_of(mesh)] == second['sidecar_materials'] and all(m for _, m in slots_of(mesh)), 'resend: both slots still filled', slots_of(mesh))
            return out

        # ------------------------------------------------------------ b. Edit Mesh
        @stage('edit')
        def _():
            out = {}
            source = next((p for p in PROBES if LIB.does_asset_exist(p)), None)
            if not check(source is not None, 'a pack mesh to copy exists', PROBES):
                return out
            pack_file, pack_sha = disk_file(source), sha256(disk_file(source))
            leaf = source.rsplit('/', 1)[-1]
            outside, inside = f'{OUTSIDE}/{leaf}', f'{INSIDE}/{leaf}'
            for target in (outside, inside):
                check(LIB.duplicate_asset(source, target) is not None and LIB.save_asset(target, only_if_is_dirty=False), f'duplicated {leaf} to {target}')
            as_duplicated = {target: sha256(disk_file(target)) for target in (outside, inside)}
            original = u.load_asset(source)
            was_origin, was_extent = bounds_of(original)
            was_slots = slots_of(original)
            out.update(source=source, slots_before=was_slots, bounds_before=[was_origin, was_extent], nanite_before=nanite_of(original))
            check(len(was_slots) >= 2 and all(m for _, m in was_slots), 'the pack mesh has two or more filled slots', was_slots)

            answer = ss_send.export_for_edit(f'{outside}.{leaf}')
            glb = Path(answer['glb'])
            my_files.append(str(glb))
            check(glb.is_file() and glb.parent == ss_send.EDIT and glb.stat().st_size > 2000 and glb.read_bytes()[:4] == b'glTF',
                  'export_for_edit() wrote a real GLB into Artifacts/LiveLink/Edit', (str(glb), glb.stat().st_size if glb.is_file() else None))
            check(answer['triangles'] == original.get_num_triangles(0), 'export_for_edit() reports the mesh it exported', answer)
            out['edit_glb_bytes'] = glb.stat().st_size

            fix = run_helper(work, 'edit', '--asset', f'{outside}.{leaf}', '--glb', str(glb))
            sent = fix['sent']
            my_files.extend([sent['glb'], sent['sidecar']])
            stem = Path(sent['glb']).stem
            my_sends.append(f'{Path(sent["glb"]).parent.name}/{stem}')
            out['arrived_in_blender'] = fix['arrived']
            check(sent['target'] == outside and Path(sent['glb']).parent.name == ss_send_edits(), 'the fix is addressed to the asset it came from, in the Outbox\'s _Edits', sent['target'])
            # What Blender got is the asset, mirrored in Y and in metres: the same rule, read the other way.
            lo, hi = ue_box(fix['arrived']['lo_m'], fix['arrived']['hi_m'])
            check(near([(lo[i] + hi[i]) / 2 for i in range(3)], was_origin, 1.0) and near([(hi[i] - lo[i]) / 2 for i in range(3)], was_extent, 1.0),
                  'Edit Mesh shows Blender the asset\'s own shape and pivot', ((lo, hi), (was_origin, was_extent)))
            check(len(fix['arrived']['materials']) == len(was_slots), 'Edit Mesh brings every material slot', fix['arrived'])

            summary = ss_send.import_outbox(only=outbox_only(my_sends))
            check(summary['imported'] == [stem] and not summary['failed'], 'import_outbox() imports the fix', summary)
            out['outside'] = check_fixed('fix outside BLENDER_BASE', outside, sent, was_origin, was_extent, was_slots, fix['raised_m'], cube_winding)
            record = ss_send._read_record().get(outside, {})
            check(record.get('status') == 'reimported', 'the fix went over the duplicate', record)
            check(sha256(record.get('backup') or '') == as_duplicated[outside] and sha256(disk_file(outside)) != as_duplicated[outside],
                  'the mesh as it was before the fix is kept, byte for byte: the only way back for a git-ignored pack asset', record.get('backup'))
            check(record.get('empty_slots') == ['M_SSTestAdded'], 'the record names the added slot as the one without a material', record)

            receipt = ss_send.import_mesh(sent['glb'], inside, keep_materials=True)
            check(receipt['status'] == 'reimported' and receipt['kept_materials'] is True, 'import_mesh(keep_materials=True) under BLENDER_BASE', receipt)
            check(receipt['nanite'] is nanite_of(original) and nanite_of(u.load_asset(inside)) is nanite_of(original) and nanite_of(u.load_asset(outside)) is nanite_of(original),
                  'a fix leaves Nanite as the asset had it', (receipt['nanite'], nanite_of(u.load_asset(inside)), nanite_of(u.load_asset(outside)), nanite_of(original)))
            out['inside'] = check_fixed('fix inside BLENDER_BASE', inside, sent, was_origin, was_extent, was_slots, fix['raised_m'], cube_winding)
            check(receipt['empty_slots'] == ['M_SSTestAdded'], 'the receipt names the added slot as the one without a material', receipt['empty_slots'])
            check(sha256(receipt.get('backup') or '') == as_duplicated[inside], 'import_mesh says where it kept the file it replaced', receipt.get('backup'))

            # An import that fails over an existing asset: a GLB with no mesh in it. The asset must be what its file holds.
            fixed_sha, fixed_bounds = sha256(disk_file(inside)), bounds_of(u.load_asset(inside))
            hollow = work / 'NoMesh.glb'
            body = json.dumps({'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': []}]}).encode('ascii')
            body += b' ' * (-len(body) % 4)
            hollow.write_bytes(b'glTF' + (2).to_bytes(4, 'little') + (20 + len(body)).to_bytes(4, 'little') + len(body).to_bytes(4, 'little') + b'JSON' + body)
            try:
                ss_send.import_mesh(hollow, inside)
                check(False, 'a GLB that holds no mesh is refused')
            except Exception as e:
                out['failed_import'] = str(e)
                check(isinstance(e, RuntimeError) and 'was not saved' in str(e) and 'reloaded from its saved file' in str(e) and 'kept at' in str(e),
                      'a failed import over an asset says the asset was put back, and where the copy is', str(e)[:400])
            check(sha256(disk_file(inside)) == fixed_sha and bounds_of(u.load_asset(inside)) == fixed_bounds, 'and the asset is as its file has it, on disk and in memory')

            # Only a fix made by Edit Mesh may go over an asset outside /Game/Blender. A sidecar that names the pack's own
            # mesh from an ordinary Outbox folder (a copy of an edit object sent by an old add-on, a stale or hand-made
            # file) is refused by name, and so is one that claims to be an edit from the wrong folder.
            wedge_glb = ss_send.OUTBOX / SENT_FOLDER / 'SSTestWedge.glb'
            thieves = {'SSTestThief': {'target': source, 'edit': False}, 'SSTestLiar': {'target': source, 'edit': True}}
            for name, side in thieves.items():
                shutil.copy2(wedge_glb, wedge_glb.with_name(name + '.glb'))
                wedge_glb.with_name(name + '.json').write_text(json.dumps(dict(side, name=name, category='Misc')), encoding='utf-8')
                my_files.extend([str(wedge_glb.with_name(name + '.glb')), str(wedge_glb.with_name(name + '.json'))])
            ghost = ss_send.OUTBOX / ss_send_edits() / 'SSTestGhost.json'
            ghost.write_text(json.dumps({'target': f'{OUTSIDE}/SM_NeverWas', 'edit': True, 'name': 'SSTestGhost'}), encoding='utf-8')
            shutil.copy2(wedge_glb, ghost.with_suffix('.glb'))
            my_files.extend([str(ghost), str(ghost.with_suffix('.glb'))])
            said = ss_send.import_outbox(only=[f'{SENT_FOLDER}/{n}' for n in thieves] + [f'{ss_send_edits()}/SSTestGhost'])
            reasons = dict(said['failed'])
            check(said['imported'] == [] and set(reasons) == set(thieves) | {'SSTestGhost'}, 'none of them is imported', said)
            check(all('outside /Game/Blender' in reasons.get(n, '') and 'Edit Mesh' in reasons.get(n, '') for n in thieves), 'a pack asset is not replaced from an ordinary Outbox folder', reasons)
            check('not there to be fixed' in reasons.get('SSTestGhost', ''), 'and a fix for an asset that does not exist creates nothing', reasons)
            check(not LIB.does_asset_exist(f'{OUTSIDE}/SM_NeverWas'), 'nothing was made for it')

            check(sha256(pack_file) == pack_sha and slots_of(u.load_asset(source)) == was_slots and bounds_of(u.load_asset(source)) == (was_origin, was_extent),
                  'the pack asset itself is untouched, on disk and in memory', source)
            return out

        # ------------------------------------------------------------ c. Scenes
        @stage('scenes')
        def _():
            return scenes_checks(work, layout_before)

    finally:
        ss_send.BACKUPS, ss_prefabs.LIBRARY, ss_prefabs.CATALOG, ss_prefabs.PROXIES = real_places
        results['cleanup'] = cleanup(work, my_files, existed, record_before, receipts_before)
    check(sha256(ss_prefabs.CATALOG) == catalog_before, 'the owner\'s parts catalogue is byte for byte what it was', str(ss_prefabs.CATALOG))
    layout_after = sha256(LAYOUT_FILE)
    check(layout_after == layout_before, 'BP_StationVisualLayout.uasset is byte for byte what it was',
          (layout_before, layout_after, 'its modified time moved too' if LAYOUT_FILE.is_file() and LAYOUT_FILE.stat().st_mtime != layout_mtime else 'same modified time'))
    git_after = git_status()
    if check(git_before is not None and git_after is not None, 'git status could be read'):
        check(git_after == git_before, 'git status reads as it did before the test', {'gone': sorted(set(git_before) - set(git_after)), 'new': sorted(set(git_after) - set(git_before))})
    results['git_status_lines'] = len(git_after or [])


def ss_send_edits():
    return '_Edits'   # send.EDITS in the add-on: the Outbox folder for fixes to assets outside BLENDER_BASE


def check_fixed(label, package, sent, was_origin, was_extent, was_slots, raised_m, cube_winding):
    """A duplicate of the pack mesh after the fix came back: shape changed as Blender changed it, old slots as they were."""
    mesh = u.load_asset(package)
    origin, extent = bounds_of(mesh)
    lo, hi = [origin[i] - extent[i] for i in range(3)], [origin[i] + extent[i] for i in range(3)]
    was_lo, was_hi = [was_origin[i] - was_extent[i] for i in range(3)], [was_origin[i] + was_extent[i] for i in range(3)]
    check(near(lo, was_lo, 1.0) and near(hi[:2], was_hi[:2], 1.0), f'{label}: X, Y and the underside are the pack mesh\'s own (no mirror, no shift)', ((lo, hi), (was_lo, was_hi)))
    check(abs(hi[2] - (was_hi[2] + raised_m * 100)) <= 1.0, f'{label}: the top is {raised_m * 100:.0f} cm higher', (hi[2], was_hi[2]))
    check_shape(label, mesh, sent)
    check_sections(label, mesh, sent, cube_winding, own_materials=False)
    slots = slots_of(mesh)
    check(len(slots) == len(was_slots) + 1, f'{label}: one slot more than before', slots)
    check([m for _, m in slots[:len(was_slots)]] == [m for _, m in was_slots], f'{label}: every old slot has its old material, in the old order', (slots, was_slots))
    added = [n for n, m in slots if m not in [w for _, w in was_slots]]
    check(added == ['M_SSTestAdded'], f'{label}: the added slot is the one Blender added', slots)
    return {'slots': slots, 'origin_cm': [round(v, 3) for v in origin], 'extent_cm': [round(v, 3) for v in extent]}


# ---------------------------------------------------------------- scenes
def engine_rows(location, rotation, scale):
    """The layout library's own FTransform(FRotator(pitch, yaw, roll), location, scale), as matrix rows."""
    return ss_prefabs.matrix_rows(u.Transform(u.Vector(*location), u.Rotator(roll=rotation[2], pitch=rotation[0], yaw=rotation[1]), u.Vector(*scale)))


def rows_near(a, b, turn=1e-4, place=1e-2):
    return all(abs(a[i][j] - b[i][j]) <= (place if i == 3 else turn * max(1.0, abs(b[i][j]))) for i in range(4) for j in range(3))


def parse_transform(text):
    """FTransform::ToString: 'X,Y,Z|Pitch,Yaw,Roll|SX,SY,SZ'."""
    location, rotation, scale = ([float(v) for v in chunk.split(',')] for chunk in text.split('|'))
    return location, rotation, scale


def refused(recipe, work, name, target, layout_before):
    """apply_station_recipe on a bad recipe: must raise RuntimeError before anything is built. Returns the message."""
    path = work / f'{name}.json'
    path.write_text(recipe if isinstance(recipe, str) else json.dumps(recipe), encoding='utf-8')
    try:
        ss_scenes.apply_station_recipe(str(path), target=target)
    except RuntimeError as e:
        check(not LIB.does_asset_exist(target) and sha256(LAYOUT_FILE) == layout_before, f'{name}: refused with nothing built or changed')
        return str(e)
    except Exception as e:
        check(False, f'{name}: refused with a reason, not a traceback', f'{type(e).__name__}: {e}')
        return ''
    check(False, f'{name}: apply_station_recipe refuses it')
    return ''


def scenes_checks(work, layout_before):
    out = {}
    recipe = json.loads(RECIPE.read_text(encoding='utf-8-sig'))
    lane = ss_scenes.lane_rules()
    check(lane is not None and lane['max'][2] == 967.5, 'the flight lane rule is read from the add-on\'s context file', lane)
    problems = ss_scenes.check_recipe(recipe)
    check(problems == [], 'check_recipe() accepts the real PitStopLayout.json', problems[:6])
    out.update(parts=len(recipe['static_meshes']), lights=len(recipe['point_lights']))

    def with_part(**part):
        bad = json.loads(json.dumps(recipe))
        row = {'name': 'SelfTest_Part', 'asset': recipe['static_meshes'][0]['asset'], 'location': [0, 1500, 300], 'rotation': [0, 0, 0], 'scale': [1, 1, 1]}
        row.update(part)
        bad['static_meshes'].append(row)
        return bad

    check(ss_scenes.check_recipe(with_part()) == [], 'a sound extra part beside the lane is accepted', ss_scenes.check_recipe(with_part())[:3])
    beside = with_part(name='SelfTest_Turned', location=[0, -760, 300])
    check(ss_scenes.check_recipe(beside) == [], 'and so is one set against the edge of the lane, unturned', ss_scenes.check_recipe(beside)[:3])
    cases = {
        'in_lane': (with_part(name='SelfTest_InLane', location=[0, 0, 300]), ["'SelfTest_InLane'", 'in the flight lane', 'move it']),
        # The same place is clear of the lane until the part is turned about its pivot: the rule follows the rotation.
        'turned_into_lane': (with_part(name='SelfTest_Turned', location=[0, -760, 300], rotation=[0, 180, 0]), ["'SelfTest_Turned'", 'in the flight lane']),
        'missing_asset': (with_part(name='SelfTest_NoMesh', asset='/Game/SpaceSurvival/NoSuch/SM_NoSuch.SM_NoSuch'), ["'SelfTest_NoMesh'", 'SM_NoSuch', 'did not load']),
        'text_for_a_number': (with_part(name='SelfTest_Text', location=['left', 1500, 300]), ["'SelfTest_Text'", 'location', 'three finite numbers']),
        'two_numbers': (with_part(name='SelfTest_Short', scale=[1, 1]), ["'SelfTest_Short'", 'scale', 'three finite numbers']),
        'not_a_number': (with_part(name='SelfTest_NaN', rotation=[0, float('nan'), 0]), ["'SelfTest_NaN'", 'rotation', 'three finite numbers']),
        'zero_scale': (with_part(name='SelfTest_Flat', scale=[1, 0, 1]), ["'SelfTest_Flat'", 'zero scale']),
        'bad_matrix': ({**recipe, 'static_meshes': recipe['static_meshes'] + [{'name': 'SelfTest_Matrix', 'asset': recipe['static_meshes'][0]['asset'],
                                                                              'matrix': [[1, 0, 0, 0], [0, 'one', 0, 0], [0, 0, 1, 0], [0, 1500, 300, 1]]}]},
                       ["'SelfTest_Matrix'", 'matrix']),
        'duplicate_name': (with_part(name=recipe['static_meshes'][3]['name'].upper()), ['duplicate name']),
    }
    bad_light = json.loads(json.dumps(recipe))
    bad_light['point_lights'].append({'name': 'SelfTest_Light', 'location': [0, 0, 900], 'color': [1, 1, 1], 'intensity': 'bright', 'attenuation_radius': 1000})
    cases['light_intensity'] = (bad_light, ["'SelfTest_Light'", 'intensity', 'not a number'])
    out['refusals'] = {}
    for name, (bad, words) in cases.items():
        said = ss_scenes.check_recipe(bad)
        check(len(said) == 1 and all(w in said[0] for w in words), f'check_recipe() refuses {name}, naming the part and the fault', said[:3])
        out['refusals'][name] = said[0] if said else None
    # The same through apply: refused before the Blueprint is touched, as a reason and never as a traceback.
    for name in ('in_lane', 'missing_asset', 'text_for_a_number', 'not_a_number', 'bad_matrix'):
        said = refused(cases[name][0], work, 'apply_' + name, SCRATCH_BP, layout_before)
        check('recipe refused, Blueprint untouched' in said and cases[name][1][0] in said, f'apply refuses {name} by name', said[:300])
    said = refused('{"static_meshes": [', work, 'apply_broken_json', SCRATCH_BP, layout_before)
    check('is not JSON' in said, 'apply refuses a file that is not JSON, saying so', said[:200])
    # A recipe with no parts is one wrong Delete in Blender, or the wrong file; the layout library would build it.
    for name, empty in (('empty_object', {}), ('no_parts', dict(recipe, static_meshes=[]))):
        check(any('no parts' in line for line in ss_scenes.check_recipe(empty)), f'check_recipe() refuses {name}', ss_scenes.check_recipe(empty)[:2])
        said = refused(empty, work, 'apply_' + name, SCRATCH_BP, layout_before)
        check('recipe refused, Blueprint untouched' in said and 'no parts' in said, f'apply refuses {name}', said[:200])

    # ---- what a copy may replace, and what stands between a recipe and work done elsewhere
    # A copy goes to a free path or over an earlier copy. Any other asset at the target was deleted and replaced.
    if LIB.does_asset_exist(WEDGE):
        wedge_sha = sha256(disk_file(WEDGE))
        try:
            ss_scenes.apply_station_recipe(str(RECIPE), target=WEDGE)
            check(False, 'a copy is never built over an asset that is not a layout')
        except RuntimeError as e:
            check('not a copy of the station layout' in str(e), 'a copy is never built over an asset that is not a layout', str(e)[:200])
        check(LIB.does_asset_exist(WEDGE) and sha256(disk_file(WEDGE)) == wedge_sha and isinstance(u.load_asset(WEDGE), u.StaticMesh), 'and that asset is untouched')
    # The owner's layout under another spelling is the owner's layout (Unreal's paths ignore case), and a layout that
    # something other than a recipe has changed is not rebuilt unless that is asked for. Both are met before anything
    # is touched; the stand-in says 'changed' so that this test never reaches the rebuild of the real layout.
    real_guard = ss_scenes.changed_outside_recipe
    ss_scenes.changed_outside_recipe = lambda *a, **k: ss_scenes.STALE + ': (said by the test)'
    try:
        for spelling in (ss_scenes.PACKAGE.lower(), ss_scenes.PACKAGE.upper().replace('/GAME/', '/Game/'), ss_scenes.PACKAGE + '.BP_StationVisualLayout'):
            try:
                ss_scenes.apply_station_recipe(str(RECIPE), target=spelling)
                check(False, 'a layout changed outside a recipe is refused without force')
            except RuntimeError as e:
                check(str(e).startswith(ss_scenes.STALE), f'{spelling}: the owner layout whatever the spelling, and refused because it was changed elsewhere', str(e)[:200])
            check(sha256(LAYOUT_FILE) == layout_before, 'nothing was touched')
    finally:
        ss_scenes.changed_outside_recipe = real_guard
    # The guard itself, against receipts made up for it: the newest receipt ABOUT THE LAYOUT decides.
    fake = work / 'Receipts'
    for k, (about, digest) in enumerate(((ss_scenes.PACKAGE, 'old'), (ss_scenes.PACKAGE, layout_before), (SCRATCH_BP, 'a copy is not the layout'))):
        folder = fake / f'EditableLayout-{k}'
        folder.mkdir(parents=True)
        (folder / 'Authoring.json').write_text(json.dumps({'blueprint': about, 'sha256': digest}), encoding='utf-8')
        os.utime(folder / 'Authoring.json', (1_700_000_000 + k, 1_700_000_000 + k))
    check(ss_scenes.last_authored_sha(receipts=fake) == layout_before and ss_scenes.changed_outside_recipe(receipts=fake) == '',
          'a layout whose file is the one the newest receipt recorded was not changed elsewhere', ss_scenes.changed_outside_recipe(receipts=fake))
    (fake / 'EditableLayout-1' / 'Authoring.json').write_text(json.dumps({'blueprint': ss_scenes.PACKAGE, 'sha256': 'saved by something else since'}), encoding='utf-8')
    said = ss_scenes.changed_outside_recipe(receipts=fake)
    check(said.startswith(ss_scenes.STALE) and 'Station Workshop' in said and 'Apply Anyway' in said, 'one whose file is another is, and the refusal says what to press', said)
    check(ss_scenes.changed_outside_recipe(receipts=work / 'NoReceipts').startswith(ss_scenes.STALE), 'and so is one no receipt speaks for')
    out['layout_is_as_last_recipe_left_it'] = ss_scenes.changed_outside_recipe() == ''   # said, not checked: the owner may have worked on it

    # ---- fill_transforms against the engine's own maths
    worst = 0.0
    samples = [([10, 20, 30], [30, -45, 12], [1, 2, 3]), ([-5, 0, 2], [-80, 170, -170], [0.5, 0.5, 0.5]), ([1200.5, -340.25, 88], [0, 90, 0], [1, 1, 1]),
               ([0, 0, 0], [12.5, -135, 60], [-1.5, 1, 2]), ([7, 8, 9], [0, 0, 0], [2, 3, 4]), ([-900, 40, 470], [5, 179.5, -3], [1.25, 0.8, 1.1])]
    for location, rotation, scale in samples:
        rows = engine_rows(location, rotation, scale)
        mine = ss_scenes._rows_from_part({'location': location, 'rotation': rotation, 'scale': scale})
        check(rows_near([r + [0] for r in mine], rows), 'ss_scenes builds a matrix as the engine does', (location, rotation, scale))
        part = {'name': 'RoundTrip', 'asset': 'x', 'matrix': rows}
        filled, disagree = ss_scenes.fill_transforms({'static_meshes': [part]})
        if not check(filled == 1 and not disagree and all(k in part for k in ('location', 'rotation', 'scale')), 'fill_transforms() fills a matrix-only part', part):
            continue
        back = engine_rows(part['location'], part['rotation'], part['scale'])
        check(rows_near(back, rows), 'the filled location/rotation/scale, put through the engine, is the matrix it came from', (location, rotation, scale, part))
        worst = max(worst, max(abs(back[i][j] - rows[i][j]) for i in range(4) for j in range(3)))
        # And the engine's own reading of that matrix says the same: FTransform(FMatrix), mirror into X and all.
        theirs = ss_prefabs.transform_from_rows(rows)
        their_rows = ss_prefabs.matrix_rows(theirs)
        check(rows_near(their_rows, rows) and near([theirs.scale3d.x, theirs.scale3d.y, theirs.scale3d.z], part['scale'], 1e-4),
              'the engine decomposes that matrix to the same scale', ([theirs.scale3d.x, theirs.scale3d.y, theirs.scale3d.z], part['scale']))
        both = dict(part, name='Both')
        check(ss_scenes.fill_transforms({'static_meshes': [both]}) == (0, []), 'a part whose two forms agree is left alone')
        both['location'] = [both['location'][0] + 5.0] + both['location'][1:]
        check(ss_scenes.fill_transforms({'static_meshes': [both]}) == (0, ['Both']), 'a part whose two forms disagree is named')
    out['round_trip_worst'] = worst

    # ---- the real recipe, applied to a scratch Blueprint
    real = LIB.load_asset(ss_scenes.PACKAGE)
    bridge = u.SSStationLayoutAuthoringLibrary
    saved_audit = json.loads(bridge.describe_station_visual_layout(real))
    saved_names = sorted(c['name'] for c in saved_audit.get('components', []))
    check(len(saved_names) > 0, 'the saved layout loads and describes itself', len(saved_names))
    real = None

    def applied(label, path, target, source_recipe):
        result = ss_scenes.apply_station_recipe(str(path), target=target)
        check(result['blueprint'] == target and result.get('layout_reloaded') is True, f'{label}: built at the scratch target, the layout reloaded from its file', result)
        check(LIB.does_asset_exist(target) and disk_file(target).is_file(), f'{label}: the scratch Blueprint is saved', target)
        check(sha256(LAYOUT_FILE) == layout_before, f'{label}: BP_StationVisualLayout.uasset unchanged')
        receipt = json.loads(Path(result['receipt']).read_text(encoding='utf-8'))
        request = json.loads((Path(result['receipt']).parent / 'Request.json').read_text(encoding='utf-8'))
        check(request['target'] == target and request['copy'] is True, f'{label}: the receipt folder says whose it is from the start', request)
        check(sha256(result.get('owner_layout_kept') or '') == layout_before, f'{label}: the owner layout as it was is kept beside the receipt', result.get('owner_layout_kept'))
        audit = {c['name']: c for c in receipt['native_audit']['components']}
        check(receipt['blueprint'] == target and receipt['native_audit']['path'].startswith(target) and receipt['status'] == 'EDITABLE_LAYOUT_COPY_AUTHORED',
              f'{label}: the receipt is about the copy', (receipt['blueprint'], receipt['native_audit'].get('path'), receipt['status']))
        wanted = source_recipe['static_meshes'] + source_recipe['point_lights']
        check(result['components'] == len(audit) >= len(wanted), f'{label}: every part and light became a component', (result['components'], len(wanted)))
        wrong = []
        for row in wanted:
            component = audit.get(row['name'])
            if component is None:
                wrong.append((row['name'], 'missing', [n for n in audit if n.lower().startswith(row['name'].lower()[:7])][:5]))
                continue
            location, rotation, scale = parse_transform(component['transform'])
            if not rows_near(engine_rows(location, rotation, scale), engine_rows(row['location'], row.get('rotation', [0, 0, 0]), row.get('scale', [1, 1, 1])), 1e-3, 0.05):
                wrong.append((row['name'], component['transform'], row['location'], row.get('rotation'), row.get('scale')))
            if 'asset' in row and component.get('mesh') != row['asset']:
                wrong.append((row['name'], component.get('mesh'), row['asset']))
        check(not wrong, f'{label}: every part and light is a component of its own name, where the recipe says, with its mesh', wrong[:4])
        turned = [r['name'] for r in source_recipe['static_meshes'] if any(abs(v) > 1 for v in r.get('rotation', [0, 0, 0])) and any(abs(v - 1) > 0.01 for v in r.get('scale', [1, 1, 1]))]
        check(len(turned) > 0, f'{label}: parts that are both turned and scaled were among them', len(turned))
        return result, audit, len(turned)

    result, audit, turned = applied('apply', RECIPE, SCRATCH_BP, recipe)
    out.update(components=result['components'], turned_and_scaled=turned, harvested=len(audit) - len(recipe['static_meshes']) - len(recipe['point_lights']))
    scratch_sha = sha256(disk_file(SCRATCH_BP))

    # Unsaved work in an open Blueprint editor is the other thing a rebuild would discard: the guard has to see it.
    copy = LIB.load_asset(SCRATCH_BP)
    check(not ss_scenes._dirty(SCRATCH_BP), 'a Blueprint just saved has no unsaved changes')
    copy.modify(True)
    out['unsaved_changes_are_seen'] = ss_scenes._dirty(SCRATCH_BP)
    check(out['unsaved_changes_are_seen'], 'a Blueprint with unsaved changes is seen as such', SCRATCH_BP)
    check(LIB.save_loaded_asset(copy, only_if_is_dirty=False) and not ss_scenes._dirty(SCRATCH_BP) and sha256(LAYOUT_FILE) == layout_before, 'and saved, it is clean again')
    scratch_sha = sha256(disk_file(SCRATCH_BP))
    copy = None

    # The layout in memory must be the saved one again, not the one just built: this is what an open editor would show and save.
    now_names = sorted(c['name'] for c in json.loads(bridge.describe_station_visual_layout(LIB.load_asset(ss_scenes.PACKAGE))).get('components', []))
    check(now_names == saved_names, 'after a scratch apply the layout in memory is the saved one', (len(now_names), len(saved_names)))

    # The same recipe with nothing but matrices: every part must still land where it did (the library reads no matrix).
    matrices = json.loads(json.dumps(recipe))
    for part in matrices['static_meshes']:
        part['matrix'] = engine_rows(part.pop('location'), part.pop('rotation', [0, 0, 0]), part.pop('scale', [1, 1, 1]))
    path = work / 'MatrixOnly.json'
    path.write_text(json.dumps(matrices), encoding='utf-8')
    applied('apply, matrices only', path, SCRATCH_BP_MATRIX, recipe)

    # Again over the scratch Blueprint that now exists: its previous file is backed up first, byte for byte.
    second, _, _ = applied('apply again', RECIPE, SCRATCH_BP, recipe)
    check(second['backup'] and sha256(second['backup']) == scratch_sha, 'a rebuilt target is backed up first, byte for byte', second['backup'])

    # What only the layout library can refuse: a name it harvests from the native station. Its reason must reach the caller.
    harvested = [n for n in audit if n not in {r['name'] for r in recipe['static_meshes'] + recipe['point_lights']}]
    if check(len(harvested) > 0, 'the layout holds components harvested from the native station', len(audit)):
        clash = with_part(name=harvested[0])
        check(ss_scenes.check_recipe(clash) == [], 'a harvested name is not known to check_recipe (it is the library\'s to refuse)')
        path = work / 'Clash.json'
        path.write_text(json.dumps(clash), encoding='utf-8')
        try:
            ss_scenes.apply_station_recipe(str(path), target=f'{INSIDE}/BP_StationLayoutClash')
            check(False, 'the layout library refuses a harvested name used twice')
        except RuntimeError as e:
            out['library_refusal'] = str(e)
            check('native station layout authoring failed' in str(e) and harvested[0] in str(e) and 'duplicate name' in str(e),
                  'the library\'s own reason (read back from the log) reaches the caller', str(e)[:400])
            check('reloaded from disk' in str(e), 'and the half-built layout was reloaded from disk', str(e)[-200:])
        check(not LIB.does_asset_exist(f'{INSIDE}/BP_StationLayoutClash') and sha256(LAYOUT_FILE) == layout_before, 'a refused build leaves nothing behind')
        now_names = sorted(c['name'] for c in json.loads(bridge.describe_station_visual_layout(LIB.load_asset(ss_scenes.PACKAGE))).get('components', []))
        check(now_names == saved_names, 'after a refused build the layout in memory is the saved one', (len(now_names), len(saved_names)))
    return out


# ---------------------------------------------------------------- clean up
def remove_assets():
    left = []
    for folder in TEST_DIRS:
        if LIB.does_directory_exist(folder):
            LIB.delete_directory(folder)
        if LIB.does_directory_exist(folder) and LIB.list_assets(folder, recursive=True, include_folder=False):
            left.append(folder)
        on_disk = disk_file(folder + '/x').parent
        if on_disk.exists():
            shutil.rmtree(on_disk, ignore_errors=True)
            if on_disk.exists():
                left.append(str(on_disk))
    return left


def cleanup(work, my_files, existed, record_before, receipts_before):
    out = {}
    try:
        left = remove_assets()
        for path in (Path(p) for p in my_files):
            if path.is_file():
                path.unlink()
        shutil.rmtree(ss_send.OUTBOX / SENT_FOLDER, ignore_errors=True)
        # The record of imports: the owner's entries stay, the test's go.
        if ss_send.RECORD.exists():
            record = {k: v for k, v in ss_send._read_record().items() if k in record_before}
            if record or existed[ss_send.RECORD]:
                ss_send.RECORD.write_text(json.dumps(record, indent=1), encoding='utf-8')
            else:
                ss_send.RECORD.unlink()
        # Folders the test made, deepest first, and only when nothing is left in them.
        for folder in sorted((p for p, was in existed.items() if not was and p != ss_send.RECORD), key=lambda p: -len(p.parts)):
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
        # Receipts: only the test's own. An open editor may have applied a scene meanwhile, and its receipt folder
        # holds the only byte copy of the layout it replaced: a folder is removed when its Request.json names a target
        # under the test's folder, and for no other reason.
        made, foreign = [], []
        for folder in (ss_scenes.RECEIPTS.glob('EditableLayout-*') if ss_scenes.RECEIPTS.exists() else []):
            if folder.name in receipts_before:
                continue
            try:
                mine = str(json.loads((folder / 'Request.json').read_text(encoding='utf-8')).get('target', '')).startswith(INSIDE + '/')
            except (OSError, ValueError):
                mine = False
            (made if mine else foreign).append(folder)
        for folder in made:
            shutil.rmtree(folder, ignore_errors=True)
        out['receipts_left_alone'] = [p.name for p in foreign]
        shutil.rmtree(work, ignore_errors=True)
        left += [str(p) for p in my_files if Path(p).exists()] + [str(p) for p in made if p.exists()]
        left += [str(p) for p, was in existed.items() if not was and p.exists()]
        left += [k for k in ss_send._read_record() if k not in record_before]
        check(not left, 'everything the test made is gone again', left)
        out.update(receipts_removed=len(made), left=left)
    except Exception as e:
        check(False, 'cleanup ran to its end', f'{type(e).__name__}: {e}')
        out['traceback'] = traceback.format_exc()
    return out


try:
    main()
except Exception as e:
    failures.append(f'the test itself stopped: {type(e).__name__}: {e}')
    results['traceback'] = traceback.format_exc()
results['failures'] = failures
u.log(('SENDSCENES_TEST_OK ' if not failures else 'SENDSCENES_TEST_FAIL ') + json.dumps(results, default=str))
