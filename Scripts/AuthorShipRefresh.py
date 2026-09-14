"""Fit owner Ludo ship candidate to Unreal +X forward, metre GLB units.
Existing Blender background only; writes ignored derivative, originals untouched.
"""
from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Artifacts/ShipRefresh'
SOURCE=Path(r'C:/Users/j6sis/.codex/codex-remote-attachments/01a098e5-0cdc-74c1-9db3-dd2a1d072db0/576BACFE-9E54-45DE-9E8F-6C0139600763/1-ship-dec-at-1.glb')
def main():
 OUT.mkdir(parents=True,exist_ok=True);digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(SOURCE))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
 m=meshes[0];bpy.context.view_layer.objects.active=m;m.select_set(True)
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 lo=Vector([min(v.co[i] for v in m.data.vertices) for i in range(3)]);hi=Vector([max(v.co[i] for v in m.data.vertices) for i in range(3)]);center=(lo+hi)/2;scale=4.2/(hi.x-lo.x)
 for v in m.data.vertices:
  p=(v.co-center)*scale;v.co=(p.x,p.y,p.z+.2)
 m.name='SM_LudoStarter';m.data.name='SM_LudoStarter';m.location=(0,0,0)
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 target=OUT/'LudoStarter.glb';bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_animations=False)
 bounds=[[min(v.co[i] for v in m.data.vertices)*100 for i in range(3)],[max(v.co[i] for v in m.data.vertices)*100 for i in range(3)]]
 report={'source_sha256':digest,'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'triangles':sum(len(p.vertices)-2 for p in m.data.polygons),'vertices':len(m.data.vertices),'bounds_cm':bounds,'forward':'+X','scale_uniform':scale,'pilot_limitation':'Closed molded canopy; existing open-cockpit pilot at (-15,0,72) will clip. Needs conditional visual hide or separately fitted pilot; do not change disembark source pose blindly.','materials_preserved':True,'textures':[{'name':i.name,'size':list(i.size)}for i in bpy.data.images]}
 (OUT/'Report.json').write_text(json.dumps(report,indent=2));assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100;s.world=bpy.data.worlds.new('World');s.world.color=(.14,.14,.14)
 for loc in [(3,-5,6),(-4,3,4)]:
  d=bpy.data.lights.new('Key','AREA');d.energy=1500;d.size=6;o=bpy.data.objects.new('Key',d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Camera');o=bpy.data.objects.new('Camera',d);s.collection.objects.link(o);s.camera=o;d.type='ORTHO';d.ortho_scale=5.8
 for name,loc in [('chase',(-6,-3,3)),('front',(6,-3,3))]:
  o.location=loc;o.rotation_euler=(Vector((0,0,.2))-o.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 print(json.dumps(report))
if __name__=='__main__':main()
