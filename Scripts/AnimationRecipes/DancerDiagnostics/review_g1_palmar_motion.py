"""Opposing views and region pairs for G1 signed-grip controls; no saves."""
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from g1_palmar_motion_control import G1PalmarControl
from validate_g2_contact_recipe import geometry, skin

model=G1PalmarControl('--rigid' not in sys.argv,'--free-profile' in sys.argv,'--continuous-release' in sys.argv,'--pin-orientation' in sys.argv)
scene=model.scene
meshes=geometry(model)
inverse=np.array([model.rest[n].inverted() for n in model.names])
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='OBJECT'
scene.display.shading.show_cavity=False
scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('G1PalmarReviewWorld');scene.world.color=(.035,.045,.055)
scene.render.resolution_x=scene.render.resolution_y=800
scene.render.resolution_percentage=100
for ob in scene.objects:
    if ob.type=='MESH':ob.color=(.55,.55,.55,1)
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.025,depth=5,location=(0,0,2.5))
pole=bpy.context.object;pole.color=(1,.12,0,1)
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=2.6
rows=[]
for seconds in (0.,3.,8.4166667,11.666667,12.25,12.75,13.3333333,18.3333333):
    pose,original,phase=model.pose(seconds)
    for version,p in (('baseline',original),('candidate',pose)):
        mat=np.array([p[n] for n in model.names])@inverse
        groups=[]
        for mesh in meshes:
            name,_,faces,joints,weights,_,_=mesh
            points=skin(mat,mesh)
            dominant=np.array(model.names)[joints[np.arange(len(joints)),weights.argmax(axis=1)]]
            groups.append((name,points,faces,dominant))
        contacts={}
        for name,points,faces,dominant in groups:
            for side in ('l','r'):
                mask=np.array([n.endswith('_'+side) and n.startswith(('lowerarm_','hand_','thumb_','index_','middle_','ring_','pinky_')) for n in dominant])
                arm_faces=faces[np.all(mask[faces],axis=1)]
                if not len(arm_faces):continue
                arm_tree=BVHTree.FromPolygons(points.tolist(),arm_faces.tolist(),all_triangles=True)
                for body_name,body_points,body_faces,body_dominant in groups:
                    mask=np.array([n.startswith(('spine_','pelvis','thigh_','calf_','foot_','ball_','neck_','head')) for n in body_dominant])
                    body_faces=body_faces[np.all(mask[body_faces],axis=1)]
                    if not len(body_faces):continue
                    body_tree=BVHTree.FromPolygons(body_points.tolist(),body_faces.tolist(),all_triangles=True)
                    pairs=arm_tree.overlap(body_tree)
                    if pairs:
                        labels={}
                        for a,b in pairs:
                            label=dominant[arm_faces[a][0]]+'/'+body_dominant[body_faces[b][0]]
                            labels[label]=labels.get(label,0)+1
                        contacts[name+':'+side+'/'+body_name]=labels
        rows.append({'seconds':seconds,'version':version,'region_pairs':contacts,**phase})
        if version=='baseline' and '--baseline' not in sys.argv:continue
        model.apply(p)
        center=(p['pelvis'].translation+p['spine_05'].translation)*.5
        for view,delta in [('front',Vector((4,-6,2))),('back',Vector((-4,6,2)))]:
            camera.location=center+delta
            camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
            scene.render.filepath=str(model.output/f'{version}_t{seconds:.3f}_{view}.png')
            bpy.ops.render.render(write_still=True)
(model.output/'RegionComparison.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
model.assert_guards()
