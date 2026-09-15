"""Read-only inspection of already mounted vendor VFX; lead schedules Unreal.
Does not import, copy, alter, save or simulate vendor assets. Missing properties
are recorded as unavailable rather than assumed values.
"""
from pathlib import Path
import json,re
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
PATHS=[
 '/Game/NiagaraExamples/FX_Weapons/Trails/NS_SimpleRibbonTrail',
 '/Game/NiagaraExamples/FX_Weapons/Trails/NS_RocketTrail',
 '/Game/NiagaraExamples/FX_Sparks/NS_Spark_Continuous',
 '/Game/NiagaraExamples/FX_Sparks/NS_Spark_Burst',
 '/Game/NiagaraExamples/FX_Weapons/Impacts/NS_Impact_Metal',
 '/Game/NiagaraExamples/FX_Explosions/NS_Explosion_Small',
 '/Game/RPGEnvironmentVFX/VFX/Niagara/NS_MagicalGlowRays',
 '/Game/RPGEnvironmentVFX/VFX/Niagara/NS_PixieTrail',
 '/Game/RPGEnvironmentVFX/VFX/Niagara/NS_ForgeSparks']
PATHS += [
 '/Game/NERVES/FX/NS_ElectircBeams_Blue',
 '/Game/NERVES/BP/BP_Blue',
 '/Game/NiagaraExamples/FX_Player/NS_Player_Electricity_Looping',
 '/Game/NiagaraExamples/FX_Ribbons/NS_TeslaCoil',
 '/Game/Sci_Fi_Weapons_VFX_AIO/VFX/NS_Lightning_Damage_Land_Mid',
]

def prop(obj,name):
 try:return obj.get_editor_property(name)
 except Exception:return None

def safe(value):
 if value is None or isinstance(value,(str,int,float,bool)):return value
 if isinstance(value,u.Object):return value.get_path_name()
 return str(value)

def main():
 registry=u.AssetRegistryHelpers.get_asset_registry();registry.search_all_assets(True)
 result={'engine':u.SystemLibrary.get_engine_version(),'status':'READ_ONLY_NOT_VISUAL_OR_PERFORMANCE_ACCEPTANCE','assets':[]}
 for path in PATHS:
  obj=u.load_asset(path);row={'path':path,'loaded':obj is not None};result['assets'].append(row)
  if obj is None:continue
  row['class']=obj.get_class().get_name()
  for key in ['fixed_bounds','effect_type','warmup_time','warmup_tick_count','exposed_parameters','emitter_handles']:
   value=prop(obj,key)
   if key=='emitter_handles' and value is not None:
    row['emitter_count']=len(value);row['emitters']=[]
    for h in value:
     entry={k:safe(prop(h,k))for k in ['name','enabled','instance','versioned_instance','id']}
     row['emitters'].append(entry)
   else:row[key]=safe(value)
  deps=registry.get_dependencies(path,u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False))
  row['dependencies']=[str(x)for x in deps]
  row['material_dependencies']=[str(x)for x in deps if '/Materials/' in str(x)]
  # Source names are evidence of available tokens, NOT verified exposed values.
  matches=list((ROOT/'User downloaded assets/VaultCache').glob('*/data/Content/'+path.removeprefix('/Game/')+'.uasset'))
  if matches:
   tokens=[x.decode()for x in re.findall(rb'[ -~]{5,}',matches[0].read_bytes())]
   row['source_user_parameter_tokens']=sorted({x for x in tokens if x.startswith('User.') and len(x)<100})
 out=ROOT/'Artifacts/EnvironmentVFX';out.mkdir(parents=True,exist_ok=True)
 (out/'Inspection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 u.log('Environment VFX read-only inspection written')
if __name__=='__main__':main()
