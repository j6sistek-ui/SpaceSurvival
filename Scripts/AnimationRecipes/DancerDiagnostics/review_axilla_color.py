import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only material/lighting comparison on the unchanged balanced proof."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
P=R.parents[2]
proof=P/'SourceAssets/DanceRefinement_20261025/Vexa_AxillaLocal_Proof.blend'
source=P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (proof,source)}
bpy.ops.wm.open_mainfile(filepath=str(proof),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
targets={o.name:o for o in s.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(source),link=False) as (available,loaded):
 names=tuple(n for n in targets if n in available.objects);loaded.objects=list(names)
materials={};indices={};clay=bpy.data.materials['NapeCPUClay']
for name,orig in zip(names,loaded.objects):
 ob=targets[name]
 assert len(ob.data.polygons)==len(orig.data.polygons) and len(ob.data.vertices)==len(orig.data.vertices),name
 assert all(tuple(a.vertices)==tuple(b.vertices) for a,b in zip(ob.data.polygons,orig.data.polygons)),name
 materials[name]=list(orig.data.materials);indices[name]=[p.material_index for p in orig.data.polygons]
 bpy.data.objects.remove(orig,do_unlink=True)
def appearance(textured):
 for name,ob in targets.items():
  ob.data.materials.clear()
  for mat in materials[name] if textured else [clay]:ob.data.materials.append(mat)
  for poly,index in zip(ob.data.polygons,indices[name]):poly.material_index=index if textured else 0
 # Keep hair hidden in both controls so it cannot hide the shoulder defect.
 targets['Eden_Pink_Hair.001'].hide_render=True
for o in list(s.objects):
 if o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=True
s.render.threads_mode='FIXED';s.render.threads=4
s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
assert any(d.type=='OPTIX' for d in prefs.devices)
for d in prefs.devices:d.use=d.type=='OPTIX'
s.world=bpy.data.worlds.new('ComparisonWorld');s.world.use_nodes=True
background=s.world.node_tree.nodes.get('Background');background.inputs['Color'].default_value=(.07,.08,.10,1);background.inputs['Strength'].default_value=.3
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.95
lights=[]
for energy,size in ((100,1.4),(55,1.8),(35,.6)):
 bpy.ops.object.light_add(type='AREA');li=bpy.context.object;li.data.energy=energy;li.data.shape='DISK';li.data.size=size;lights.append(li)
out=R/'VexaAxillaColor';out.mkdir(exist_ok=True)
report={'source_hashes':before,'geometry':'Private local axilla candidate; same baseline rig with 24 baked correction curves','materials':'Existing packed character textures and Blender approximation of Unreal shaders; no native skin shader parity claim','hair':'Hidden equally in all controls','views':[]}
for sec in (4,9.033333):
 s.frame_set(round(1+sec*60));bpy.context.view_layer.update()
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
 center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
 cam.location=center+chest@Vector((-2,-2,.15));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 for li,offset in zip(lights,(Vector((-1,-1.5,1.7)),Vector((1,-1,1)),Vector((0,1,.8)))):
  li.location=center+chest@offset;li.rotation_euler=(center-li.location).to_track_quat('-Z','Y').to_euler()
 for style,textured in [('clay_neutral',False),('texture_neutral',True),('texture_bar',True)]:
  appearance(textured)
  colors=[(1,.96,.9),(.9,.95,1),(1,1,1)] if style!='texture_bar' else [(1,.22,.6),(.18,.48,1),(.65,.15,1)]
  for li,color in zip(lights,colors):li.data.color=color
  s.render.filepath=str(out/f'{sec:g}_{style}.png');bpy.ops.render.render(write_still=True)
  report['views'].append({'seconds':sec,'style':style,'file':s.render.filepath})
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in before.items())
(out/'Report.json').write_text(json.dumps(report,indent=2));print('COLOR_COMPARISON_DONE')
