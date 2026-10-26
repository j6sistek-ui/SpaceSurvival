"""Local thumb-pad control; wrist, four fingers and saved sources stay fixed.

This isolates pad orientation from radial distance. It is an unsaved candidate,
not a replacement calibration. Run hidden Blender with -- --fit to evaluate
the bounded contact/orientation control; omit --fit for the preserved baseline.
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
fit = '--fit' in sys.argv
# Reuse the exact signed-palm setup and kinematics, without its old optimizer,
# calibration writes or render loop. The prefix ends before parameter fitting.
sys.argv.extend(['--thumb-axis', '--surface', '--cmc', '--opposition'])
prefix = (CODE/'probe_g2_palmar_grip.py').read_text().split('seed = np.array')[0]
exec(compile(prefix, str(CODE/'probe_g2_palmar_grip.py'), 'exec'))
O = R/'G2PalmarGrip/ThumbPadOrientation'
if fit:
    O = O.with_name('ThumbPadOrientationFit')
assert not O.exists(), 'Preserve prior controls'
O.mkdir()
old_path = R/'G2PalmarGrip/ThumbOppositionControl/StaticControl.json'
old = json.loads(old_path.read_text())
seed = np.array(old['params'])
baseline_pose = posed(seed)
baseline_points = skin(np.array([baseline_pose[n] for n in names])@inverse_rest, local_mesh)
thumb_faces = compact_digit_faces['thumb']
pad_faces = compact_faces[np.sum(pad_masks['thumb'][compact_faces], axis=1) >= 2]
assert len(pad_faces) >= 3
fixed_trees = {d: BVHTree.FromPolygons(baseline_points.tolist(), compact_digit_faces[d].tolist(), all_triangles=True) for d in digits}
thumb_ids = np.flatnonzero(digit_masks['thumb'][ids])


def evaluate(params, detailed=False):
    pose = posed(params)
    pts = skin(np.array([pose[n] for n in names])@inverse_rest, local_mesh)
    gap = float(triangle_radii(pts, thumb_faces).min()-.025)
    tri = pts[pad_faces]
    centers = tri.mean(axis=1)
    normals = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
    areas = np.linalg.norm(normals, axis=1)
    normals /= np.maximum(areas[:, None], 1e-12)
    radial = centers.copy(); radial[:, 2] = 0
    radial /= np.maximum(np.linalg.norm(radial, axis=1)[:, None], 1e-12)
    center_gap = np.linalg.norm(centers[:, :2], axis=1)-.025
    # The external pad faces the pole, opposite its outward radial normal.
    alignment = -np.sum(normals*radial, axis=1)
    nearest = np.argsort(center_gap)[:min(6, len(center_gap))]
    pad_gap = float(np.average(center_gap[nearest], weights=areas[nearest]))
    pad_alignment = float(np.average(alignment[nearest], weights=areas[nearest]))
    tree = BVHTree.FromPolygons(pts.tolist(), thumb_faces.tolist(), all_triangles=True)
    contacts = {d: len(tree.overlap(t)) for d, t in fixed_trees.items()}
    # Millimetre-scaled objective: prioritize nonpenetration and contact, then
    # contact-facing pad and restrained departure from the current thumb.
    score = 20000*min((gap-.00005)*1000, 0)**2 + 100000*sum(contacts.values())
    score += (pad_gap*1000-.5)**2 + 16*(1-pad_alignment)**2
    score += .0001*float(np.sum(np.degrees(params[14:]-seed[14:])**2))
    if detailed:
        return {'score': score, 'surface_gap_mm': gap*1000, 'pad_gap_mm': pad_gap*1000,
                'pad_facing_cosine': pad_alignment, 'cross_digit_pairs': contacts,
                'pad_faces': len(pad_faces), 'thumb_degrees': np.degrees(params[14:]).tolist()}
    return score


params = seed.copy()
history = []
if fit:
    low = np.radians([-55, 0, 0, 0, -15, -80])
    high = np.radians([55, 45, 65, 65, 60, 80])
    for degrees in (4, 2, 1, .5):
        for iteration in range(25):
            changed = False
            for j in range(14, 20):
                best, winner = evaluate(params), None
                for sign in (-1, 1):
                    q = params.copy(); q[j] = np.clip(q[j]+math.radians(degrees)*sign, low[j-14], high[j-14])
                    score = evaluate(q)
                    if score < best-1e-9:
                        best, winner = score, q
                if winner is not None:
                    params, changed = winner, True
            if not changed:
                break
        history.append({'step_degrees': degrees, 'result': evaluate(params, True)})
        print('THUMB_PAD_STEP', history[-1], flush=True)
after = posed(params)
assert np.array_equal(params[:14], seed[:14])
fixed_names = [n for n in names if not n.startswith('thumb_') or not n.endswith('_r')]
unchanged = max(float(np.abs(np.array(after[n])-np.array(baseline_pose[n])).max()) for n in fixed_names)
assert unchanged == 0
apply(after)
evaluated = hands.evaluated_get(bpy.context.evaluated_depsgraph_get())
actual = np.array([tuple(hands.matrix_world@evaluated.data.vertices[int(i)].co) for i in ids])
predicted = skin(np.array([after[n] for n in names])@inverse_rest, local_mesh)
cpu_error = float(np.linalg.norm(actual-predicted, axis=1).max()*1000)
assert cpu_error < .01
report = {'sources': guard, 'previous_control': str(old_path),
          'before': evaluate(seed, True), 'after': evaluate(params, True),
          'params': params.tolist(), 'history': history, 'fixed_bone_error': unchanged,
          'cpu_error_mm': cpu_error, 'status': 'Unsaved thumb-pad candidate; no motion or acceptance claim.'}
(O/'Control.json').write_text(json.dumps(report, indent=2))

s.render.engine = 'BLENDER_WORKBENCH'; s.display.shading.light = 'STUDIO'
s.display.shading.color_type = 'MATERIAL'; s.display.shading.show_cavity = False
s.display.shading.background_type = 'WORLD'; s.world = bpy.data.worlds.new('ThumbPadWorld')
s.world.color = (.035, .045, .055); s.render.resolution_x = s.render.resolution_y = 800
s.render.resolution_percentage = 100
for ob in s.objects:
    if ob.type == 'MESH': ob.hide_render = ob != hands
hands.data.materials.clear()
for name, color in [('Grey', (.55,.55,.55,1)), ('Thumb', (0,.85,1,1)), ('Pad', (1,.65,.02,1))]:
    mat = bpy.data.materials.new(name); mat.diffuse_color = color; hands.data.materials.append(mat)
pad_global = np.zeros(len(points), dtype=bool); pad_global[ids] = pad_masks['thumb']
for face in hands.data.polygons:
    face.material_index = 2 if np.mean(pad_global[list(face.vertices)])>.5 else 1 if np.mean(digit_masks['thumb'][list(face.vertices)])>.5 else 0
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=.025, depth=5, location=(0,0,2.5))
pole = bpy.context.object; mat = bpy.data.materials.new('OrangePole'); mat.diffuse_color=(1,.12,0,1)
pole.data.materials.append(mat)
bpy.ops.object.camera_add(); camera=bpy.context.object; s.camera=camera
camera.data.type='ORTHO'; camera.data.ortho_scale=.27
for state, pose in [('before',baseline_pose),('after',after)]:
    apply(pose)
    for view, direction in [('palm',Vector((.3,-1,.15))),('back',Vector((-.3,1,.15))),('above',Vector((.1,-.2,1)))]:
        center=Vector((0,0,3.015)); camera.location=center+direction.normalized()*3
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        s.render.filepath=str(O/f'{state}_{view}.png'); bpy.ops.render.render(write_still=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guard.items())
print('THUMB_PAD_DONE', report, flush=True)
