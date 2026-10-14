"""Bounded display luminance correction after actual native Capture3 review.

Duplicates only seven agent-owned display materials. Artwork, source graphs,
Time/UV logic, room lighting and architecture remain intact. Smoked glass gains
a bounded opacity floor for content readability. Lead saves.
"""
import hashlib
import math
import re
from pathlib import Path
from RefineStationBarPresentation import _one,_path,_require
from RefineStationLoungeCeiling import _snapshot
from StationRefinementSupport import transform_record

MAP='/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
SOURCE='/Game/OutpostSandbox/StationRefinement/BarDisplays20261006/Materials/'
BASE='/Game/OutpostSandbox/StationRefinement/BarDisplayReadability20261006'
OLD_PANE='Engineering/Bay S1/Glass'
OLD_HEADING='Refine/SocialAtmosphereFollowup/Screen DigitalPanel/Heading'
OLD_GRAPHIC='/Game/OutpostSandbox/StationRefinement/SocialAtmosphereFollowup/Materials/MI_Lounge_DigitalPanel'
NAMES=('05_Drinks_Menu','06_Kitchen_Menu','07_DrinksTablet','08_FoodTablet','09_VenueBanner','TV0','TV1')

def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def apply(ctx,expected_map_sha256):
 import unreal as u
 root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 map_file=root/('Content/'+MAP[6:]+'.umap')
 _require(re.fullmatch('[0-9a-f]{64}',expected_map_sha256) and _sha(map_file)==expected_map_sha256 and
   world.get_path_name().split('.')[0]==MAP,'Require exact reviewed saved display scene')
 actors=list(ctx.eas.get_all_level_actors());before={a.get_path_name():_snapshot(a,u) for a in actors}
 edit=u.MaterialEditingLibrary;dirty=[];sources={};replacements={};materials=[];allow=set()
 def guard(asset):
  path=_path(asset);_require(path.startswith('/Game/'),'Unexpected display source')
  sources[path]=_sha(root/('Content/'+path[6:]+'.uasset'));return path
 for name in NAMES:
  original=ctx.asset(SOURCE+'M_'+name);source_path=guard(original)
  destination=BASE+'/M_'+name
  _require(not u.EditorAssetLibrary.does_asset_exist(destination),'Preserve prior readability asset '+destination)
  source_custom=[n for n in edit.get_material_expressions(original) if isinstance(n,u.MaterialExpressionCustom)]
  _require(len(source_custom)==1,'Expected one verified artwork shader')
  shader=source_custom[0].get_editor_property('code');glass='Tablet' in name
  expected='*0.9,a);' if glass else 'return float4(c*0.82,1.0);'
  _require(shader.endswith(expected),'Reviewed current display emission changed')
  target_gain=7. if glass else 6.;old_gain=.9 if glass else .82
  result=u.EditorAssetLibrary.duplicate_asset(source_path,destination);_require(result,'Private display copy failed')
  root_node=edit.get_material_property_input_node(result,u.MaterialProperty.MP_EMISSIVE_COLOR)
  _require(isinstance(root_node,u.MaterialExpressionComponentMask),'Unexpected source emissive connection')
  scalar=edit.create_material_expression(result,u.MaterialExpressionScalarParameter)
  scalar.set_editor_property('parameter_name','DisplayBrightness');scalar.set_editor_property('default_value',target_gain/old_gain)
  multiply=edit.create_material_expression(result,u.MaterialExpressionMultiply)
  _require(edit.connect_material_expressions(root_node,'',multiply,'A') and
    edit.connect_material_expressions(scalar,'',multiply,'B') and
    edit.connect_material_property(multiply,'',u.MaterialProperty.MP_EMISSIVE_COLOR),'Display brightness wiring failed')
  if glass:
   alpha=edit.get_material_property_input_node(result,u.MaterialProperty.MP_OPACITY)
   _require(isinstance(alpha,u.MaterialExpressionComponentMask),'Unexpected glass opacity source')
   opacity=edit.create_material_expression(result,u.MaterialExpressionScalarParameter)
   opacity.set_editor_property('parameter_name','GlassOpacityFloor');opacity.set_editor_property('default_value',.68)
   maximum=edit.create_material_expression(result,u.MaterialExpressionMax)
   _require(edit.connect_material_expressions(alpha,'',maximum,'A') and
     edit.connect_material_expressions(opacity,'',maximum,'B') and
     edit.connect_material_property(maximum,'',u.MaterialProperty.MP_OPACITY),'Smoked glass readability wiring failed')
  custom=[n for n in edit.get_material_expressions(result) if isinstance(n,u.MaterialExpressionCustom)]
  _require(len(custom)==1 and custom[0].get_editor_property('code')==shader,'Source ad loop/opacity/UV shader changed')
  _require(result.get_editor_property('blend_mode')==original.get_editor_property('blend_mode') and
    result.get_editor_property('two_sided')==original.get_editor_property('two_sided'),'Display surface behavior changed')
  edit.layout_material_expressions(result);errors=edit.recompile_material(result)
  _require(not errors,'Native readability shader failed: '+str(errors))
  _require(abs(scalar.get_editor_property('default_value')-target_gain/old_gain)<.00001,'Luminance scalar differs')
  dirty.append(result.get_path_name());replacements[source_path]=result
  materials.append({'original':source_path,'private':result.get_path_name(),'old_linear_gain':old_gain,
    'new_linear_gain':target_gain,'scalar_multiplier':float(scalar.get_editor_property('default_value')),
    'native_compile_errors':list(errors),'original_time_opacity_uv_shader_preserved':True,
    'additional_opacity_floor':.68 if glass else None})
 assignments=[]
 for actor in actors:
  for component in actor.get_components_by_class(u.StaticMeshComponent):
   for slot in range(component.get_num_materials()):
    old=_path(component.get_material(slot))
    if old not in replacements:continue
    _require(actor.get_actor_label().startswith('Refine/BarDisplays/'),'A display source escaped reviewed actor scope')
    component.set_material(slot,replacements[old]);allow.add(actor.get_path_name())
    assignments.append({'actor':transform_record(actor),'component':component.get_name(),'slot':slot,
      'before_material':old,'after_material':replacements[old].get_path_name()})
 _require(len(assignments)==7 and len(allow)==7,'Expected exactly seven existing display surfaces')
 pane=_one(actors,OLD_PANE);heading=_one(actors,OLD_HEADING)
 component=pane.get_component_by_class(u.StaticMeshComponent)
 _require(component and component.static_mesh.get_name().endswith('_V2_Part2_DigitalWindow') and
   all(_path(m)==OLD_GRAPHIC for m in component.get_materials()),'Displaced background pane identity differs')
 guard(component.static_mesh)
 for material in component.get_materials():guard(material)
 _require(isinstance(heading,u.TextRenderActor),'Displaced duplicate heading is not the expected text')
 arcade=[_one(actors,'Refine/Social/Arcade/Identity/'+part) for part in ('Name','Backing')]
 _require(isinstance(arcade[0],u.TextRenderActor) and
   math.dist(arcade[1].get_actor_location().to_tuple(),(5005.,-4440.,300.))<.01,
   'Displaced old arcade name/backing no longer matches the reviewed placement')
 to_retire=(pane,heading,*arcade)
 retired=[]
 for actor in to_retire:
  components=actor.get_components_by_class(u.PrimitiveComponent)
  collisions=[c.get_collision_enabled() for c in components]
  actor.set_actor_hidden_in_game(True);actor.set_is_temporarily_hidden_in_editor(True)
  for c in components:c.set_visibility(False);c.set_hidden_in_game(True)
  _require(collisions==[c.get_collision_enabled() for c in components],'Retiring artwork changed wall collision')
  retired.append(transform_record(actor))
 retired_paths={a.get_path_name() for a in to_retire}
 for actor in actors:
  path=actor.get_path_name();old=before[path];now=_snapshot(actor,u)
  if path in allow:
   _require(all(now[k]==old[k] for k in old if k!='materials'),'Readability edit changed pose/light/visibility')
  elif path in retired_paths:
   _require(all(now[k]==old[k] for k in ('location','rotation','scale','materials','lights')),'Displaced graphic edit changed protected fields')
  else:_require(now==old,'Unrelated room actor changed '+actor.get_actor_label())
 _require(_sha(map_file)==expected_map_sha256 and all(_sha(root/('Content/'+p[6:]+'.uasset'))==h for p,h in sources.items()),
   'Readability helper cannot save or mutate source assets')
 return {'dirty_assets':dirty,'source_sha256':sources,'materials':materials,'assignments':assignments,
   'retired_duplicate_graphics':retired,'new_light_count':0,'created_actor_count':0,
   'protected_existing_layout_animation_lighting_preserved':True,
   'limits':'Display-only luminance/smoked-glass correction. Source art, graph timing, UVs and all lighting unchanged. Four displaced graphics retire; architecture and collision preserved. Actual new pixels still require review.'}
