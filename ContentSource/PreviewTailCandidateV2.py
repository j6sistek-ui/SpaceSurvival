"""Fresh-import deformation and paired source renders for TailCandidateV2.

Does not modify any GLB, ship source, or Unreal package. Before means the separate
unadopted TailCandidate v1, not the current runtime PilotMesh.
"""
import hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'ContentSource/TailCandidateV2Preview'
sys.path.insert(0,str(ROOT/'ContentSource'))
import InspectTailStrip as setup
import GenerateDisembark as anim
import GenerateTailCandidate as g


def pose(rig,clip,time):
    doc,binary=CLIPS[clip];anim.apply_animation(rig,doc,binary,time);bpy.context.view_layer.update()


def coords(mesh):
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=evaluated.to_mesh();values=np.empty(len(data.vertices)*3,dtype=np.float32);data.vertices.foreach_get('co',values);evaluated.to_mesh_clear();return values.reshape((-1,3))


def import_pair():
    scene,before,rig,camera=setup.setup();prior=set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'ContentSource/Animation/TailCandidateV2.glb'))
    added=[obj for obj in scene.objects if obj not in prior];after=next(obj for obj in added if obj.type=='MESH');other=next(obj for obj in added if obj.type=='ARMATURE')
    assert all(max(abs(other.data.bones[b.name].matrix_local[r][c]-b.matrix_local[r][c]) for r in range(4) for c in range(4))<1e-6 for b in rig.data.bones)
    world=after.matrix_world.copy();after.parent=rig;after.matrix_world=world
    for modifier in after.modifiers:
        if modifier.type=='ARMATURE':modifier.object=rig
    bpy.data.objects.remove(other,do_unlink=True);after.hide_render=True
    return scene,before,after,rig,camera


def capture(scene):
    temporary=ROOT/'.agent/local/TailCandidateV2Render.png';scene.render.filepath=str(temporary);bpy.ops.render.render(write_still=True)
    image=bpy.data.images.load(str(temporary),check_existing=False);width,height=image.size;values=np.empty(width*height*4,dtype=np.float32);image.pixels.foreach_get(values);bpy.data.images.remove(image);return values.reshape((height,width,4))


def save_sheet(name,tiles):
    values=np.concatenate(tiles,axis=1);image=bpy.data.images.new(name,width=values.shape[1],height=values.shape[0],alpha=True);image.pixels.foreach_set(values.reshape(-1));image.filepath_raw=str(OUT/(name+'.png'));image.file_format='PNG';image.save();bpy.data.images.remove(image)


def label(scene,camera):
    data=bpy.data.curves.new('CandidateLabel','FONT');data.size=.047;data.align_x='CENTER';obj=bpy.data.objects.new('CandidateLabel',data);scene.collection.objects.link(obj)
    material=bpy.data.materials.new('CandidateLabelWhite');material.use_nodes=True;bsdf=material.node_tree.nodes['Principled BSDF'];bsdf.inputs['Base Color'].default_value=(.7,.8,.9,1);bsdf.inputs['Emission Color'].default_value=(.7,.8,.9,1);bsdf.inputs['Emission Strength'].default_value=.4;data.materials.append(material)
    return obj


def chase_comparison():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'ContentSource/AcornShipCandidate/AcornShipCandidate.blend'))
    scene=bpy.context.scene;scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.cycles.samples=32
    camera=scene.camera;camera.location=(-7.6,-4.65,3.2);camera.rotation_euler=(Vector((-.15,0,.4))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=50
    pairs=[]
    for source in ('TailCandidate','TailCandidateV2'):
        prior=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/('ContentSource/Animation/'+source+'.glb')))
        added=[obj for obj in scene.objects if obj not in prior];rig=next(obj for obj in added if obj.type=='ARMATURE');mesh=next(obj for obj in added if obj.type=='MESH');rig.animation_data_clear()
        for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
        doc,binary=anim.read_glb(ROOT/'ContentSource/Animation/Pilot.glb');anim.apply_animation(rig,doc,binary,1)
        rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,np.pi/2);rig.scale=(1.5,1.5,1.5);rig.location=(-.15,0,.72);pairs.append(mesh)
    text=label(scene,camera);text.data.size=.027;text.rotation_euler=camera.rotation_euler;text.location=camera.location+camera.rotation_euler.to_quaternion()@Vector((0,-.39,-2))
    tiles=[]
    for title,visible in [('Prior candidate - source studio',pairs[0]),('V2 precise strip repair - source studio',pairs[1])]:
        for mesh in pairs:mesh.hide_render=mesh!=visible
        text.data.body=title;bpy.context.view_layer.update();tiles.append(capture(scene))
    save_sheet('ChaseComparison',tiles)
    print('TAIL_V2_CHASE_SOURCE_OK')


def main():
    if '--chase-only' in sys.argv:
        chase_comparison();return
    global CLIPS
    CLIPS={name:anim.read_glb(ROOT/path) for name,path in [('Pilot','ContentSource/Animation/Pilot.glb'),('Walk','model-rigged.glb'),('Exit','ContentSource/Animation/Disembark.glb')]}
    metadata=json.loads((ROOT/'ContentSource/Animation/TailCandidateV2.json').read_text());assert hashlib.sha256((ROOT/'ContentSource/Animation/TailCandidateV2.glb').read_bytes()).hexdigest()==metadata['sha256'];scene,before,after,rig,camera=import_pair()
    changed=np.zeros(len(after.data.vertices),dtype=bool);changed[metadata['indices']]=True
    protected=~changed;assert len(changed)==202507 and changed.sum()==metadata['new_vertices_changed']
    max_error=0.0;records=[]
    for name,count in [('Pilot',121),('Walk',75),('Exit',73)]:
        clip_error=0.0;max_change=0.0
        for frame in range(count):
            pose(rig,name,frame/30);a,b=coords(before),coords(after)
            error=float(np.linalg.norm(a[protected]-b[protected],axis=1).max()*100);clip_error=max(clip_error,error);max_error=max(max_error,error)
            max_change=max(max_change,float(np.linalg.norm(a[changed]-b[changed],axis=1).max()*100))
        records.append({'clip':name,'frames':count,'preserved_vertices_max_difference_cm':clip_error,'changed_tail_vertices_max_displacement_vs_prior_cm':max_change})
    assert max_error==0.0,'Unselected posed vertex moved'
    result={'status':'FRESH_SOURCE_DEFORMATION_VERIFIED_VISUAL_REVIEW_REQUIRED','v2_sha256':metadata['sha256'],'prior_sha256':metadata['prior_candidate_sha256'],'total_vertices':len(changed),'changed_vertices':int(changed.sum()),'preserved_vertices':int(protected.sum()),'preserved_posed_vertices_max_error_cm':max_error,'clips':records,'source_only':True,'limitations':['Before is unadopted TailCandidate v1, not runtime PilotMesh','No Unreal import or runtime evaluation','Source rigid tail may still retain occluded unrepaired strips','Existing palms/controls mismatch and body material quality not changed']}
    (OUT/'Deformation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    text=label(scene,camera)
    for name,clip,times,position,target,scale in [('SeatedRearComparison','Pilot',[1],(1.3,2.2,.8),(0,.02,.03),1.5),('SeatedOppositeComparison','Pilot',[1],(-1.3,2.2,.8),(0,.02,.03),1.5),('WalkComparison','Walk',[0,.8,1.6],(2.2,2.2,.6),(0,.0,-.10),1.7),('ExitComparison','Exit',[0,.8,1.6,2.4],(2.2,2.2,.6),(0,.0,-.10),1.7)]:
        scene.render.resolution_x=1200 if len(times)==1 else 480;scene.render.resolution_y=1200 if len(times)==1 else 600
        camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
        text.rotation_euler=camera.rotation_euler;text.location=Vector(target)+camera.rotation_euler.to_quaternion()@Vector((0,-.69 if len(times)==1 else -.78,.2))
        tiles=[]
        for time in times:
            pose(rig,clip,time)
            for title,visible in [('Prior candidate',before),('V2 precise strip repair',after)]:
                before.hide_render=visible!=before;after.hide_render=visible!=after;text.data.body=f'{title} {clip} {time:.2f}s';tiles.append(capture(scene))
        save_sheet(name,tiles)
    # Keep one uncropped1200px exact camera sample for residual-geometry review.
    pose(rig,'Pilot',1);scene.render.resolution_x=scene.render.resolution_y=1200;camera.location=(1.3,2.2,.8);camera.rotation_euler=(Vector((0,.02,.03))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=1.5;text.hide_render=True
    before.hide_render=True;after.hide_render=False;scene.render.filepath=str(OUT/'V2SeatedRear.png');bpy.ops.render.render(write_still=True)
    print('TAIL_V2_PREVIEW_OK',json.dumps(records))
    chase_comparison()


if __name__=='__main__':main()
