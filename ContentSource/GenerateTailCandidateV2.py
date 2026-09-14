"""Repair only fur components identified by reviewed seated screen rays.

Produces a separate TailCandidateV2.glb. Original source, PilotMesh and the first
TailCandidate remain unchanged. UVs, material, topology and skeleton are retained.
"""
import hashlib,json,sys,struct,copy
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ContentSource'))
import GenerateTailCandidate as g
import GenerateDisembark as a


def main():
    source=ROOT/'model-rigged.glb';prior=ROOT/'ContentSource/Animation/TailCandidate.glb';folder=ROOT/'ContentSource/TailCandidateV2Preview'
    selection=json.loads((folder/'RaySelection.json').read_text());protected={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,prior,ROOT/'ContentSource/Animation/Pilot.glb',ROOT/'ContentSource/Animation/PilotMesh.glb')}
    assert protected['model-rigged.glb']==selection['source_sha256'] and protected[str(prior.relative_to(ROOT))]==selection['candidate_sha256']
    original,original_binary=g.read_glb(source);previous,previous_binary=g.read_glb(prior);document=copy.deepcopy(original);binary=bytearray(original_binary)
    attrs=document['meshes'][0]['primitives'][0]['attributes'];prior_attrs=previous['meshes'][0]['primitives'][0]['attributes']
    arrays={name:g.accessor(previous,previous_binary,prior_attrs[name]).copy() for name in ('POSITION','NORMAL','JOINTS_0','WEIGHTS_0')}
    originals={name:g.accessor(original,original_binary,attrs[name]).copy() for name in arrays}
    already=np.any(arrays['POSITION']!=originals['POSITION'],axis=1);assert already.sum()==144133
    selected=np.zeros(len(already),dtype=bool)
    for component in selection['selected_components']:
        assert component['component']!=9607,'Backpack strap must stay unchanged'
        if component['already_selected']==0:selected[component['indices']]=True
        else:assert component['already_selected']==component['vertices'],'Selection must contain whole uniformly classified components'
    assert selected.sum()==1959 and not np.any(selected&already)
    residual_path=folder/'RaySelectionResidual.json'
    if residual_path.is_file() and '--initial-mask-only' not in sys.argv:
        residual=json.loads(residual_path.read_text());first=json.loads((folder/'V2FirstPass.json').read_text())
        assert residual['candidate_sha256']==first['sha256'] and residual['source_sha256']==selection['source_sha256']
        for component in residual['selected_components']:
            assert component['component'] not in (8388,9607),'Backpack hardware must stay unchanged'
            if component['already_selected']==0:selected[component['indices']]=True
        assert selected.sum()==2631,'Residual ray mask differs from reviewed672 new fur vertices'
    assert not np.any(selected&already)
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(ROOT/'ContentSource/Animation/Pilot.glb'))
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
    for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
    pilot_doc,pilot_bin=a.read_glb(ROOT/'ContentSource/Animation/Pilot.glb');a.apply_animation(rig,pilot_doc,pilot_bin,1)
    skin=rig.pose.bones['Pelvis'].matrix@rig.data.bones['Pelvis'].matrix_local.inverted();repair=skin.inverted()@Matrix.Translation((0,0,.12));normal_repair=repair.to_3x3().inverted().transposed()
    pelvis_node=next(i for i,node in enumerate(document['nodes']) if node.get('name')=='Pelvis');pelvis_index=document['skins'][0]['joints'].index(pelvis_node)
    for index in np.flatnonzero(selected):
        p=originals['POSITION'][index];v=repair@Vector((float(p[0]),-float(p[2]),float(p[1])));arrays['POSITION'][index]=(v.x,v.z,-v.y)
        n=originals['NORMAL'][index];normal=(normal_repair@Vector((float(n[0]),-float(n[2]),float(n[1])))).normalized();arrays['NORMAL'][index]=(normal.x,normal.z,-normal.y)
    arrays['JOINTS_0'][selected]=(pelvis_index,0,0,0);arrays['WEIGHTS_0'][selected]=(1,0,0,0)
    for name,array in arrays.items():assert np.array_equal(array[~selected],g.accessor(previous,previous_binary,prior_attrs[name])[~selected]),'Altered preserved candidate vertex '+name
    tail=selected|already;body=~tail
    for name,array in arrays.items():assert np.array_equal(array[body],originals[name][body]),'Altered original body '+name
    for name,component,kind in [('POSITION',5126,'VEC3'),('NORMAL',5126,'VEC3'),('JOINTS_0',5123,'VEC4'),('WEIGHTS_0',5126,'VEC4')]:attrs[name]=g.append_accessor(document,binary,arrays[name].astype('<u2' if component==5123 else '<f4'),component,kind,name=='POSITION')
    document.pop('animations',None)
    for name in ('nodes','skins','materials','images','textures','samplers'):assert document.get(name)==original.get(name)
    assert document['meshes'][0]['primitives'][0]['indices']==original['meshes'][0]['primitives'][0]['indices']
    for name in ('TEXCOORD_0',):assert np.array_equal(g.accessor(document,binary,attrs[name]),g.accessor(original,original_binary,original['meshes'][0]['primitives'][0]['attributes'][name]))
    assert binary[:len(original_binary)]==original_binary
    document['buffers'][0]['byteLength']=len(binary);encoded=json.dumps(document,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);binary.extend(b'\0'*((-len(binary))%4))
    output=ROOT/'ContentSource/Animation/TailCandidateV2.glb';output.write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)
    record={'status':'SEPARATE_PRECISE_TAIL_REPAIR_SOURCE_REQUIRES_DEFORMATION_REVIEW','sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,'prior_candidate_sha256':selection['candidate_sha256'],'ray_selection_sha256':hashlib.sha256((folder/'RaySelection.json').read_bytes()).hexdigest(),'residual_selection_sha256':hashlib.sha256(residual_path.read_bytes()).hexdigest() if residual_path.is_file() and '--initial-mask-only' not in sys.argv else None,'new_vertices_changed':int(selected.sum()),'total_tail_vertices':int(tail.sum()),'original_body_vertices_preserved':int(body.sum()),'prior_candidate_vertices_preserved':int((~selected).sum()),'indices':np.flatnonzero(selected).tolist(),'joint':'Pelvis','target_tail_translation_m':[0,0,.12],'source_index_transport_verified':True,'preserved':['All original UVs and triangle indices','Original material/images/textures/samplers','Original nodes/skins','All original BIN bytes as unchanged prefix','Every prior candidate vertex outside the recorded exact component mask','All remaining original body positions/normals/joints/weights','Rejected232-vertex backpack strap and124-vertex curved attachment'],'protected_sources':protected,'limitations':['Only source asset generated; no Unreal import','Rigid pelvis tail has no secondary dynamics','Direct ray mask may miss occluded strips; comparisons required before adoption']}
    output.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    if '--initial-mask-only' in sys.argv:
        (folder/'V2FirstPass.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    for name,digest in protected.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    print('TAIL_V2_SOURCE_OK',json.dumps({k:record[k] for k in ('sha256','new_vertices_changed','original_body_vertices_preserved')}))


if __name__=='__main__':main()
