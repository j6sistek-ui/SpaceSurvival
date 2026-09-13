"""Trace visible seated-tail defects to original indexed components before repair.

This diagnostic never modifies any GLB or Unreal asset. Pixel coordinates are
recorded against the saved 1200px seated rear reference, then mapped through a
BVH of evaluated triangles to original indexed vertices. No spatial expansion.
"""
import hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ContentSource/TailCandidateV2Preview'
RESIDUAL='--residual-v2' in sys.argv
CANDIDATE=ROOT/('ContentSource/Animation/TailCandidateV2.glb' if RESIDUAL else 'ContentSource/Animation/TailCandidate.glb')
sys.path.insert(0,str(ROOT/'ContentSource'))
import GenerateDisembark as anim
import GenerateTailCandidate as gltf


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(CANDIDATE))
    mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    rig.animation_data_clear()
    for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
    doc,binary=anim.read_glb(ROOT/'ContentSource/Animation/Pilot.glb');anim.apply_animation(rig,doc,binary,1)
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('StripDiagnosticWorld');scene.world.color=(.08,.08,.08)
    for pos,energy,size in [((2,-2,3),450,4),((-2,1,2),500,3),((1,3,2),400,3)]:
        data=bpy.data.lights.new('StripLight','AREA');data.energy=energy;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new('StripLight',data);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('StripCamera');camera=bpy.data.objects.new('StripCamera',data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO';data.ortho_scale=1.5
    camera.location=(1.3,2.2,.8);camera.rotation_euler=(Vector((0,.02,.03))-camera.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    return scene,mesh,rig,camera


def main():
    OUT.mkdir(exist_ok=True)
    if RESIDUAL:
        first=json.loads((OUT/'V2FirstPass.json').read_text())
        assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()==first['sha256'],'Reproduce the first-pass v2 with --initial-mask-only before retracing residuals'
    scene,mesh,rig,camera=setup()
    source_doc,source_bin=gltf.read_glb(ROOT/'model-rigged.glb');candidate_doc,candidate_bin=gltf.read_glb(CANDIDATE)
    original_attrs=source_doc['meshes'][0]['primitives'][0]['attributes'];candidate_attrs=candidate_doc['meshes'][0]['primitives'][0]['attributes']
    original_positions=gltf.accessor(source_doc,source_bin,original_attrs['POSITION']);candidate_positions=gltf.accessor(candidate_doc,candidate_bin,candidate_attrs['POSITION'])
    coords=np.array([v.co[:] for v in mesh.data.vertices]);assert len(coords)==len(candidate_positions)
    assert np.max(np.abs(coords-np.stack((candidate_positions[:,0],-candidate_positions[:,2],candidate_positions[:,1]),axis=1)))<2e-6,'Imported source indices changed'
    original_blender=np.stack((original_positions[:,0],-original_positions[:,2],original_positions[:,1]),axis=1)
    previous=np.any(original_positions!=candidate_positions,axis=1)
    bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();components=[];component_of=np.empty(len(coords),dtype=np.int32)
    for seed in bm.verts:
        if seed.tag:continue
        seed.tag=True;stack=[seed];island=[]
        while stack:
            v=stack.pop();island.append(v.index)
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if not other.tag:other.tag=True;stack.append(other)
        component_of[island]=len(components);components.append(island)
    bm.free()
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=evaluated.to_mesh();data.calc_loop_triangles()
    assert len(data.vertices)==len(coords),'Modifier changed indexed topology'
    verts=[mesh.matrix_world@v.co for v in data.vertices];triangles=[tuple(tri.vertices) for tri in data.loop_triangles]
    bvh=BVHTree.FromPolygons(verts,triangles,all_triangles=True)
    q=camera.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));direction=q@Vector((0,0,-1))
    # Explicit points on the visibly dangling strip in the seated rear reference.
    points=[(774,684),(790,706),(791,744),(812,774),(738,656),(768,636),(691,651),(710,694),(758,718),(795,678),(799,704),(766,749),(787,765),(818,787),(735,669),(720,648)]
    points += [(702,628),(746,638),(759,640),(786,609),(789,631),(796,649),(811,682),(816,706),(800,732),(800,757),(827,789),(780,733),(763,672),(732,658),(730,683),(713,662),(704,643),(781,623),(794,646),(788,665),(760,686),(815,762),(823,780),(827,792)]
    # Densely trace the two visible residual-strip silhouettes, not a 3D region.
    polygons=[[(808,585),(828,585),(840,707),(824,715)],[(742,622),(787,613),(813,651),(820,700),(824,732),(845,787),(832,819),(803,813),(769,765),(764,741),(741,743),(734,714),(699,690),(697,647),(724,635)]]
    def contains(x,y,polygon):
        inside=False
        for i,a in enumerate(polygon):
            b=polygon[i-1]
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        return inside
    points += [(x,y) for y in range(584,821,2) for x in range(696,847,2) if any(contains(x,y,polygon) for polygon in polygons)]
    if RESIDUAL:
        polygons=[[(714,620),(789,622),(821,702),(833,794),(805,800),(785,763),(769,729),(728,680)]]
        points=[(x,y) for y in range(618,802) for x in range(712,835) if any(contains(x,y,polygon) for polygon in polygons)]
    rejected={8388:"Close overlay identifies the curved backpack support attachment, not fur. Preserve124 vertices.",9607:"Visual overlay identified the backpack support strap, not fur. Preserve all232 vertices."}
    hits=[];chosen=set()
    for x,y in points:
        origin=camera.location+right*((x/1200-.5)*1.5)+up*((.5-y/1200)*1.5)
        point,normal,tri_index,distance=bvh.ray_cast(origin,direction,10)
        if tri_index is None:hits.append({'pixel':[x,y],'hit':False});continue
        indices=triangles[tri_index];component=int(component_of[indices[0]]);assert all(component_of[i]==component for i in indices)
        island=components[component]
        if component not in rejected:chosen.add(component)
        hits.append({'pixel':[x,y],'hit':True,'triangle':tri_index,'triangle_source_indices':list(indices),'indexed_component':component,'component_vertices':len(island),'previously_selected':int(previous[island].sum()),'rejected_reason':rejected.get(component),'hit_world_m':list(point),'original_triangle_positions_glTF_m':original_positions[list(indices)].tolist(),'original_triangle_uv':gltf.accessor(source_doc,source_bin,original_attrs['TEXCOORD_0'])[list(indices)].tolist()})
    mask=np.zeros(len(coords),dtype=bool)
    selected_components=[]
    for component in sorted(chosen):
        island=components[component];mask[island]=True;points=original_blender[island]
        selected_components.append({'component':component,'vertices':len(island),'indices':island,'min_rest_blender_m':points.min(axis=0).tolist(),'max_rest_blender_m':points.max(axis=0).tolist(),'already_selected':int(previous[island].sum())})
    evaluated.to_mesh_clear()
    record={'status':'RAY_IDENTIFIED_SELECTION_PENDING_VISUAL_REVIEW_NO_WEIGHT_CHANGE','source_sha256':hashlib.sha256((ROOT/'model-rigged.glb').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((CANDIDATE).read_bytes()).hexdigest(),'reference':('ContentSource/TailCandidateV2Preview/ResidualSeatedRearBefore.png' if RESIDUAL else 'ContentSource/TailCandidatePreview/CandidateTailProposalRear.png'),'camera':{'position_m':list(camera.location),'target_m':[0,.02,.03],'orthographic_scale_m':1.5,'resolution':[1200,1200],'pose':'A_Pilot1s'},'rejected_components':rejected,'screen_polygons':polygons,'ray_step_pixels':1 if RESIDUAL else 2,'rays':hits,'selected_components':selected_components,'selected_vertices':int(mask.sum()),'selected_new_vertices':int((mask&~previous).sum()),'unchanged_source_vertices':len(mask)-int(mask.sum()),'selection_rule':'Only indexed connected components directly hit by recorded rays. No position/UV/proximity expansion.'}
    (OUT/('RaySelectionResidual.json' if RESIDUAL else 'RaySelection.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    scene.render.filepath=str(OUT/('ResidualSeatedRearBefore.png' if RESIDUAL else 'SeatedRearBefore.png'));bpy.ops.render.render(write_still=True)
    mesh.data.materials.clear()
    for name,color in [('PreservedGrey',(.18,.21,.25,1)),('RayHitCyan',(.01,.75,1,1))]:
        material=bpy.data.materials.new(name);material.use_nodes=True;bsdf=material.node_tree.nodes['Principled BSDF'];bsdf.inputs['Base Color'].default_value=color;bsdf.inputs['Roughness'].default_value=.5;mesh.data.materials.append(material)
    for polygon in mesh.data.polygons:polygon.material_index=int(any(mask[i] for i in polygon.vertices))
    for label,pose,pos,target,scale in [('SeatedSelection','pilot',(1.3,2.2,.8),(0,.02,.03),1.5),('RestSelection','rest',(1.5,3,-1.2),(0,.02,-.05),1.25),('WalkSelection','walk',(1.3,2.2,.8),(0,.02,-.10),1.5)]:
        if pose=='rest':rig.data.pose_position='REST'
        if pose=='walk':
            rig.data.pose_position='POSE';doc,binary=anim.read_glb(ROOT/'model-rigged.glb');anim.apply_animation(rig,doc,binary,.308333333)
        camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;bpy.context.view_layer.update()
        scene.render.filepath=str(OUT/(('Residual' if RESIDUAL else '')+label+'.png'));bpy.ops.render.render(write_still=True)
    print('TAIL_STRIP_RAYS',json.dumps({'hits':sum(row['hit'] for row in hits),'components':len(chosen),'vertices':int(mask.sum()),'new':int((mask&~previous).sum())}))


if __name__=='__main__':main()
