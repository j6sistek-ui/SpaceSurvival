"""Preserve the reviewed ship and character; author only a separate upper-grip fit candidate."""
from pathlib import Path
import hashlib,importlib.util,json,math,sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'ContentSource/AcornShipCandidate'
CHANGED={'Pilot control grip -1','Pilot control grip 1','Control illumination -1','Control illumination 1'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def mesh_digest(obj):
 deps=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles();digest=hashlib.sha256()
 for values in [np.array(obj.matrix_world,dtype=np.float32),np.array([tuple(v.co)for v in mesh.vertices],dtype=np.float32),np.array([tuple(t.vertices)for t in mesh.loop_triangles],dtype=np.int32),np.array([t.material_index for t in mesh.loop_triangles],dtype=np.int32),np.array([tuple(n.vector)for n in mesh.corner_normals],dtype=np.float32)]:digest.update(values.tobytes())
 digest.update('|'.join(m.name if m else ''for m in mesh.materials).encode());evaluated.to_mesh_clear();return digest.hexdigest()

def curve_points(obj):return [tuple(p.co)for p in obj.data.splines[0].points]

def character():
 sys.path.insert(0,str(ROOT/'ContentSource'));import GenerateDisembark as animation
 before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'ContentSource/Animation/TailCandidateV2.glb'));added=[o for o in bpy.context.scene.objects if o not in before];rig=next(o for o in added if o.type=='ARMATURE');rig.animation_data_clear()
 for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
 clip,binary=animation.read_glb(ROOT/'ContentSource/Animation/Pilot.glb');animation.apply_animation(rig,clip,binary,0);rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi/2);rig.scale=(1.5,)*3;rig.location=(-.15,0,.72);bpy.context.view_layer.update();return added,rig,animation,clip,binary

def main():
 protected_paths=[ROOT/'model-rigged.glb',ROOT/'ContentSource/Animation/Pilot.glb',ROOT/'ContentSource/Animation/TailCandidateV2.glb',ROOT/'ContentSource/Animation/Disembark.glb',BASE/'AcornShipCandidate.blend',BASE/'AcornShipCandidate.obj',BASE/'AcornShipCandidate.glb']
 protected={str(p.relative_to(ROOT)):sha(p)for p in protected_paths};contact=json.loads((OUT/'ContactMeasurement.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(BASE/'AcornShipCandidate.blend'));bpy.context.preferences.filepaths.save_version=0
 spec=importlib.util.spec_from_file_location('ship_source',ROOT/'ContentSource/GenerateAcornShipCandidate.py');author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author);author.OUT=OUT
 author.SHIP=[o for o in bpy.context.scene.objects if o.type in ('MESH','CURVE')and any(m and m.name.startswith('AC01_')for m in o.data.materials)];assert len(author.SHIP)==185
 before={o.name:mesh_digest(o)for o in author.SHIP};old_curves={name:curve_points(bpy.data.objects[name])for name in CHANGED};grips=[]
 for sign,side in [(-1,'R'),(1,'L')]:
  row=contact['hands'][side];patch=row['nearby_palm_patch_candidates'][0];a,b,c=patch['coefficients'];tip=Vector((patch['xy_cm'][0]/100,patch['xy_cm'][1]/100,(c-.05)/100));normal=Vector((-a,-b,1)).normalized();obj=bpy.data.objects['Pilot control grip %s'%sign];spline=obj.data.splines[0];old=[Vector(p.co[:3])for p in spline.points];assert len(old)==2 and abs(obj.data.bevel_depth-.018)<1e-6
  join=old[0].lerp(old[1],.7);control1=join+(old[1]-old[0]).normalized()*.02;stop=tip-normal*.006;control2=stop-normal*.02
  points=[old[0],join]
  for i in range(1,9):
   t=i/8;points.append((1-t)**3*join+3*(1-t)**2*t*control1+3*(1-t)*t*t*control2+t**3*stop)
  points.append(tip)
  spline.points.add(len(points)-2)
  for point,co in zip(spline.points,points):point.co=(*co,1);point.radius=1
  light=bpy.data.objects['Control illumination %s'%sign];light.location+=tip-old[1]
  grips.append({'side':side,'old_base_cm':list(old[0]*100),'old_tip_cm':list(old[1]*100),'preserved_join70_cm':list(join*100),'new_tip_cm':list(tip*100),'tip_up_normal':list(normal),'radius_cm':1.8,'ring_translation_cm':list((tip-old[1])*100),'centerline_cm':[list(p*100)for p in points]})
 bpy.context.view_layer.update();after={o.name:mesh_digest(o)for o in author.SHIP};changed=[name for name in before if before[name]!=after[name]];assert set(changed)==CHANGED
 reference=json.loads((BASE/'Report.json').read_text());bounds,triangles=author.evaluated_bounds(author.SHIP)
 assert np.max(np.abs(np.array(bounds)-np.array(reference['bounds_cm'])))<.001,'Ship envelope changed'
 author.export_ship()
 for suffix in ('.blend','.glb','.obj','.mtl'):
  source=OUT/('AcornShipCandidate'+suffix);target=OUT/('AcornShipGripFit'+suffix);source.replace(target)
 objpath=OUT/'AcornShipGripFit.obj';objtext=objpath.read_text().replace('mtllib AcornShipCandidate.mtl','mtllib AcornShipGripFit.mtl');objpath.write_text(objtext,encoding='utf-8')
 added,rig,animation,clip,binary=character();hero=next(o for o in added if o.type=='MESH');bpy.context.view_layer.update();tree=BVHTree.FromObject(hero,bpy.context.evaluated_depsgraph_get());inverse=hero.matrix_world.inverted();surface_checks=[]
 for grip in grips:
  xy=np.array(grip['new_tip_cm'][:2])/100;origin=Vector((xy[0],xy[1],.70));direction=Vector((0,0,1));hit,normal,index,distance=tree.ray_cast(inverse@origin,(inverse.to_3x3()@direction).normalized());assert hit is not None;world_hit=hero.matrix_world@hit;surface_checks.append({'side':grip['side'],'blender_under_glove_ray_hit_cm':list(world_hit*100),'evaluated_polygon_index':index,'grip_tip_cm':grip['new_tip_cm']})
 scene=bpy.context.scene;scene.render.engine='CYCLES';prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices();gpu=[device for device in prefs.devices if device.type=='OPTIX'];assert gpu,'Installed OptiX GPU unavailable';
 for device in prefs.devices:device.use=device in gpu
 scene.cycles.device='GPU';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;camera=scene.camera
 views=[('AfterCockpit',(1.65,-1.65,1.85),(.12,0,.94),57,0),('LeftContact',(1.05,1.0,1.35),(.20,.22,.94),65,0),('RightContact',(1.02,-1.05,1.35),(.16,-.20,.95),65,0),('PilotPeak',(1.65,-1.65,1.85),(.12,0,.94),57,1)]
 for name,pos,target,lens,seconds in views:
  animation.apply_animation(rig,clip,binary,seconds);bpy.context.view_layer.update();camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 # Matched original grip geometry at identical overview settings; everything else stays authored.
 for name,points in old_curves.items():
  obj=bpy.data.objects[name];obj.location=(0,0,0);obj.data.splines.clear();spline=obj.data.splines.new('POLY');spline.points.add(len(points)-1)
  for point,co in zip(spline.points,points):point.co=co
  spline.use_cyclic_u=name.startswith('Control illumination')
 animation.apply_animation(rig,clip,binary,0);bpy.context.view_layer.update();camera.location=views[0][1];camera.rotation_euler=(Vector(views[0][2])-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=57;scene.render.filepath=str(OUT/'BeforeCockpit.png');bpy.ops.render.render(write_still=True)
 for path,digest in protected.items():assert sha(ROOT/path)==digest,'Protected source changed'
 result={'status':'UPPER_GRIP_FIT_CANDIDATE_SOURCE_RENDERED_NOT_UNREAL_OR_OWNER_ACCEPTANCE','changed_authored_parts':changed,'unchanged_authored_parts':181,'unchanged_part_fingerprints':{k:before[k]for k in before if k not in CHANGED},'bounds_cm':bounds,'triangles':triangles,'materials':reference['materials'],'pilot_transform':reference['pilot_transform'],'grips':grips,'blender_surface_checks':surface_checks,'protected_sha256':protected,'outputs':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(OUT.iterdir())if p.suffix in ('.blend','.glb','.obj','.mtl','.png')],'limits':['Four parts changed, no main hull/nacelle/rig/material edits.','Static grips cannot exactly follow breathing; quantitative contact and exit clearance remain review conditions.','Source renders do not establish native appearance or grasp animation.']}
 (OUT/'Report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('GRIP_FIT_SOURCE_FINISHED')
if __name__=='__main__':main()
