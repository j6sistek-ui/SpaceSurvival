import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only comparison of the vendor Blender source and assembled Vexa rig."""
import bpy, json
from pathlib import Path
P=R.parents[2]; O=R/'VexaNativeMaster'; O.mkdir(exist_ok=True)
rows=[]
for name in ('F3_Body_Master.blend','Vexa_Character_Options.blend'):
    path=P/'SourceAssets/CharacterWorkshop_20261021'/name
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
    row={'file':name,'scene_frame':bpy.context.scene.frame_current,'objects':[],'rigs':[]}
    for o in bpy.context.scene.objects:
        if o.type not in ('MESH','ARMATURE'): continue
        item={'name':o.name,'type':o.type,'visible':o.visible_get(),'hide_render':o.hide_render,'parent':o.parent.name if o.parent else None,'matrix_world':[list(x) for x in o.matrix_world]}
        if o.type=='MESH':
            item.update(vertices=len(o.data.vertices),groups=len(o.vertex_groups),bounds=[list(o.matrix_world@__import__('mathutils').Vector(c)) for c in o.bound_box],modifiers=[])
            for m in o.modifiers:
                d={'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render}
                for k in ('use_deform_preserve_volume','vertex_group','factor','iterations','object'):
                    if hasattr(m,k):
                        v=getattr(m,k);d[k]=v.name if hasattr(v,'name') else v
                item['modifiers'].append(d)
            keys=o.data.shape_keys
            item['shapes']=[k.name for k in keys.key_blocks] if keys else []
            item['shape_drivers']=[{'path':d.data_path,'expression':d.driver.expression} for d in keys.animation_data.drivers] if keys and keys.animation_data else []
        else:
            bones=[]
            for b in o.data.bones:
                pb=o.pose.bones[b.name]
                bones.append({'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform,'bbone_segments':b.bbone_segments,'constraints':[{'type':c.type,'name':c.name,'influence':c.influence} for c in pb.constraints]})
            row['rigs'].append({'name':o.name,'bones':bones,'drivers':[{'path':d.data_path,'expression':d.driver.expression} for d in o.animation_data.drivers] if o.animation_data else []})
        row['objects'].append(item)
    rows.append(row)
(O/'Inventory.json').write_text(json.dumps(rows,indent=2))
print('NATIVE_MASTER_AUDIT',json.dumps([{'file':r['file'],'meshes':len([o for o in r['objects'] if o['type']=='MESH']),'rigs':[{'name':v['name'],'bones':len(v['bones']),'constraints':sum(len(b['constraints']) for b in v['bones']),'drivers':len(v['drivers'])} for v in r['rigs']]} for r in rows]),flush=True)
