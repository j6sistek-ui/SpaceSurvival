import os
import bpy
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(os.environ['SS_HERO_SOURCE']);O=P/'UnrealUnits';O.mkdir(exist_ok=True)
for filename in ['SquirrelHero_SoftFur.fbx']+['Tail_'+n+'.fbx' for n in ['Idle','Walk','Run','JumpStart','JumpAir','JumpLand']]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(P/filename),use_anim=filename.startswith('Tail_'));bpy.context.view_layer.update()
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');world=rig.matrix_world.copy();meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];S=Matrix.Scale(100,4)
 bones=[(b.name,b.parent.name if b.parent else None,S@world@b.head_local,S@world@b.tail_local,(world@b.matrix_local).to_3x3().col[2].copy()) for b in rig.data.bones]
 action=rig.animation_data.action if rig.animation_data else None
 geom=[]
 for ob in meshes:
  data=ob.data.copy();data.transform(S@ob.matrix_world);groups=[(g.name,[(v.index,next((w.weight for w in v.groups if w.group==g.index),0)) for v in ob.data.vertices]) for g in ob.vertex_groups];geom.append((ob.name,data,groups))
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 data=bpy.data.armatures.new('SquirrelCentimeterRig');new=bpy.data.objects.new('Armature',data);bpy.context.collection.objects.link(new);new.select_set(True);bpy.context.view_layer.objects.active=new;bpy.ops.object.mode_set(mode='EDIT')
 for name,parent,head,tail,roll in bones:
  b=data.edit_bones.new(name);b.head=head;b.tail=tail;b.align_roll(roll)
  if parent:b.parent=data.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT')
 for name,data,groups in geom:
  ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
  for name,weights in groups:
   g=ob.vertex_groups.new(name=name)
   for i,w in weights:
    if w:g.add([i],w,'REPLACE')
  mod=ob.modifiers.new('Skin','ARMATURE');mod.object=new;ob.select_set(True)
 if action:
  action=action.copy()
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      if fc.data_path.endswith('location'):
       for k in fc.keyframe_points:k.co.y*=100;k.handle_left.y*=100;k.handle_right.y*=100
  new.animation_data_create();new.animation_data.action=action
  bpy.context.scene.frame_start=round(action.frame_range[0]);bpy.context.scene.frame_end=round(action.frame_range[1])
 bpy.context.scene.unit_settings.scale_length=.01;bpy.context.view_layer.update()
 bpy.ops.export_scene.fbx(filepath=str(O/filename),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=bool(action),bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=False,path_mode='RELATIVE')
 print('UE_UNITS_EXPORT',filename,[(b[0],list(b[2])) for b in bones[:2]],flush=True)
