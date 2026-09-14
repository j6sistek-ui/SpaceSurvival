"""Create a private basic volume graph from the owner's actual 3D cloud texture.
New-only; lead runs in Unreal. No vendor mutation, custom HLSL or shader-function dependency.
"""
from pathlib import Path
import json
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
TARGET='/Game/SpaceSurvival/Licensed/Atmosphere/M_SpaceDustVolume'
TEXTURE='/Game/Asteroid_Library/Textures/Volume/T_VOLUME_CloudCavernous_1'

def main():
 lib=u.MaterialEditingLibrary;assets=u.EditorAssetLibrary
 assert not assets.does_asset_exist(TARGET),'Inspect existing derivative rather than overwrite'
 texture=u.load_asset(TEXTURE);assert isinstance(texture,u.VolumeTexture),'Actual volume texture missing'
 material=u.AssetToolsHelpers.get_asset_tools().create_asset('M_SpaceDustVolume',TARGET.rsplit('/',1)[0],u.Material,u.MaterialFactoryNew())
 assert material
 material.set_editor_property('material_domain',u.MaterialDomain.MD_VOLUME)
 material.set_editor_property('blend_mode',u.BlendMode.BLEND_ADDITIVE)
 nodes=[]
 def node(cls,x,y):
  value=lib.create_material_expression(material,cls,x,y);assert value;nodes.append(value);return value
 def wire(a,b,pin,out=''):
  names=lib.get_material_expression_input_names(b)
  if pin not in names and len(names)==1: pin=names[0]
  assert lib.connect_material_expressions(a,out,b,pin),str((a,b,pin,out,names))
 def scalar(value,x,y):
  result=node(u.MaterialExpressionConstant,x,y);result.set_editor_property('r',value);return result
 def binary(cls,a,b,x,y):
  result=node(cls,x,y);wire(a,result,'A');wire(b,result,'B');return result
 world=node(u.MaterialExpressionWorldPosition,-1500,-200)
 center=node(u.MaterialExpressionObjectPositionWS,-1500,0)
 bounds=node(u.MaterialExpressionObjectBounds,-1500,200)
 local=binary(u.MaterialExpressionSubtract,world,center,-1250,-100)
 diameter=binary(u.MaterialExpressionMultiply,bounds,scalar(2,-1500,400),-1250,250)
 normalized=binary(u.MaterialExpressionDivide,local,diameter,-1000,-100)
 uv=binary(u.MaterialExpressionAdd,normalized,scalar(.5,-1100,100),-800,-100)
 sample=node(u.MaterialExpressionTextureSampleParameterVolume,-550,-300)
 sample.set_editor_property('parameter_name','CloudVolume')
 sample.set_editor_property('texture',texture)
 sample.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR if texture.get_editor_property("srgb") else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
 wire(uv,sample,'UVs')
 # normalized is centered coordinates. Spherical zero at radius .5 keeps all
 # six cube boundaries empty; smoothstep over outer .15 removes hard silhouette.
 length=node(u.MaterialExpressionLength,-800,300);wire(normalized,length,'Input')
 inward=binary(u.MaterialExpressionSubtract,scalar(.5,-800,500),length,-550,300)
 ramp=binary(u.MaterialExpressionDivide,inward,scalar(.15,-550,500),-300,300)
 edge=node(u.MaterialExpressionSaturate,-50,300);wire(ramp,edge,'Input')
 squared=binary(u.MaterialExpressionMultiply,edge,edge,180,300)
 twice=binary(u.MaterialExpressionMultiply,edge,scalar(2,0,600),180,500)
 smoothfactor=binary(u.MaterialExpressionSubtract,scalar(3,180,700),twice,400,500)
 smooth=binary(u.MaterialExpressionMultiply,squared,smoothfactor,620,300)
 cloud=node(u.MaterialExpressionMultiply,850,0);wire(sample,cloud,'A','R');wire(smooth,cloud,'B')
 density=node(u.MaterialExpressionScalarParameter,850,250)
 density.set_editor_property('parameter_name','Density');density.set_editor_property('default_value',.00001)
 extinction=binary(u.MaterialExpressionMultiply,cloud,density,1100,50)
 assert lib.connect_material_property(extinction,'',u.MaterialProperty.MP_SUBSURFACE_COLOR)
 tint=node(u.MaterialExpressionVectorParameter,850,-400)
 tint.set_editor_property('parameter_name','NebulaEmission');tint.set_editor_property('default_value',u.LinearColor(.01,.03,.06,1))
 emission=binary(u.MaterialExpressionMultiply,cloud,tint,1100,-250)
 assert lib.connect_material_property(emission,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 black=scalar(0,1100,350)
 assert lib.connect_material_property(black,'',u.MaterialProperty.MP_BASE_COLOR)
 lib.recompile_material(material)
 assert assets.save_loaded_asset(material,only_if_is_dirty=False)
 out=ROOT/'Artifacts/EnvironmentVFX';out.mkdir(parents=True,exist_ok=True)
 (out/'SpaceDustVolumeAuthor.json').write_text(json.dumps({'status':'AUTHORED_REQUIRES_SHADER_COMPILE_AND_NATIVE_RENDER','material':TARGET,'volume_texture':TEXTURE,'node_count':len(nodes),'density_default':.00001,'emission_default':[.01,.03,.06],'edge':'smoothstep 0..1 over centered normalized radius .5 to .35; zero on cube boundary','albedo':0,'requires':'volumetric fog, unrotated cube and supported volume-material mesh voxelization'},indent=2)+'\n')
 u.log('SPACE_DUST_VOLUME_AUTHORED '+TARGET)
if __name__=='__main__':main()
