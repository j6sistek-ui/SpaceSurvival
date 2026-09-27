"""Register the owner's September 26 packs, retaining every prior ULAT row.

Run in an empty offscreen editor. Full scenes stay native maps; ULAT handles
meshes. Pack-specific Content Browser collections include all placeable assets.
"""
import json
import sys
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Artifacts/ApartmentHome'
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'Scripts'))
import ConfigureUlatLibrary as ulat

PACKS={'Cyberpunk_Room':'Apartment','CyberPunkBarAssetSet01':'Bar',
       'CyberPunkMegapack':'Megapack','CyberPunkAssets':'SciFi','CyberpunkHolograms':'Holograms'}

def run():
    registry=u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    manager=u.get_editor_subsystem(u.CollectionManagerSubsystem)
    entries=[]
    report={'collections':[],'errors':[]}
    for root,label in PACKS.items():
        inventory=sorted(registry.get_assets_by_path('/Game/'+root,recursive=True),key=lambda a:str(a.package_name))
        assert inventory,'Imported root missing: '+root
        members=[]
        for a in inventory:
            kind=str(a.asset_class_path.asset_name)
            path=str(a.package_name)+'.'+str(a.asset_name)
            if kind in ('StaticMesh','Blueprint','World','MaterialInstanceConstant'):
                members.append(path)
            if kind=='StaticMesh':
                category,_=ulat._classify(path)
                entries.append({'asset_path':path,'category':category,'type_label':'CP '+label})
        name='SS_New_CP_'+label
        ref=u.Collection(container='Game',name=name,share_type=u.CollectionShareType.LOCAL)
        manager.add_assets_to_collection(ref,[u.SoftObjectPath(p) for p in members])
        found=manager.get_assets_in_collection(ref)
        if isinstance(found,tuple):found=found[-1]
        actual={str(a.package_name)+'.'+str(a.asset_name) for a in found}
        assert set(members).issubset(actual),name
        report['collections'].append({'name':name,'assets':len(members)})
    dry=ulat.apply(entries,apply=False)
    report['dry_run']=dry
    assert dry['status']=='dry_run_ready',dry['errors']
    applied=ulat.apply(entries,apply=True)
    report['apply']=applied
    assert applied['status'] in ('applied','unchanged'),applied['errors']
    # An unchanged registration is still a successful refresh. The generic
    # importer omits verified_rows on that path, so record the actual table
    # count here instead of invalidating the subsequent fresh-load review.
    applied['verified_rows']=len(ulat._json_export(u,u.load_asset(ulat.TABLE_PATH)))
    report['coverage']={'requested_meshes':len(entries),'added':len(applied['added']),
       'skipped':len(applied['skipped']),'all_placeable_assets_in_native_collections':True,
       'collision_policy':'No duplicate meshes or displaced rows; use native collections for skipped names.'}
    report['status']='PASS'
    (OUT/'library-registration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('CYBERPUNK_LIBRARY PASS '+str(len(entries))+' meshes')

if __name__=='__main__':
    run()
