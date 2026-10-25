"""Small reusable observatory modules; centimetres, explicit convex collision."""
import bpy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'SourceAssets/EntertainmentObservatory/Modules'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = .01
rows = []

def arc(name, inner, outer, bottom, top, degrees=11.25, segments=4, collision=True):
    angle = math.radians(degrees)
    vertices = [(radius*math.cos(-angle/2+angle*i/segments),
                 radius*math.sin(-angle/2+angle*i/segments), z)
                for z in (bottom, top) for radius in (inner, outer)
                for i in range(segments+1)]
    n=segments+1
    faces=[]
    for i in range(segments):
        faces += [(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),
                  (i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)]
    faces += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    if collision:
        for i in range(segments):
            angles=[-angle/2+angle*j/segments for j in (i,i+1)]
            v=[(r*math.cos(a),r*math.sin(a),z) for z in (bottom,top)
               for r in (inner,outer) for a in angles]
            m=bpy.data.meshes.new('Collision')
            m.from_pydata(v,[],[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)])
            m.update();h=bpy.data.objects.new('UCX_'+name+'_'+str(i),m)
            bpy.context.collection.objects.link(h);h.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,
        object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',bake_anim=False)
    rows.append({'name':name,'inner_cm':inner,'outer_cm':outer,'bottom':bottom,'top':top,
                 'collision_hulls':segments if collision else 0})
    for item in list(bpy.context.selected_objects):item.hide_set(True)

arc('SM_Obs_InnerDeck',420,1770,-24,0)
arc('SM_Obs_OuterDeck',1770,2300,-24,0)
arc('SM_Obs_Wall',2280,2320,0,580)
arc('SM_Obs_Roof',420,2300,0,22)
arc('SM_Obs_Crown',350,720,0,30)
arc('SM_Obs_Collar',350,390,0,15)
arc('SM_Obs_Rail',422,428,0,6)
arc('SM_Obs_FloorTrim',430,440,0,2,collision=False)
arc('SM_Obs_OuterTrim',2230,2240,0,3,collision=False)
arc('SM_Obs_Stair',1830,2050,0,15,degrees=.90,segments=1)
arc('SM_Obs_StairRail',1825,1831,0,6,degrees=.90,segments=1)
arc('SM_Obs_Glass',348,350,0,1160,segments=4,collision=False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Observatory_Modules.blend'))
(OUT/'Modules.json').write_text(json.dumps(rows,indent=2))
print('OBSERVATORY_MODULES',len(rows),flush=True)
