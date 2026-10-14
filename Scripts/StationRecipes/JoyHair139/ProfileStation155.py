import unreal as u,json,collections
from pathlib import Path
OUT=Path(__file__).resolve().parents[3]/'.agent/local/StationRefinement/JoyHair139/StationProfile155';OUT.mkdir(exist_ok=False)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
meshes={};skeletal=[];grooms=[];lights=collections.Counter()
for a in actors:
 for c in a.get_components_by_class(u.SkeletalMeshComponent):
  mesh=c.get_editor_property('skeletal_mesh_asset')
  if not mesh:continue
  p=mesh.get_path_name()
  if p not in meshes:meshes[p]={'lods':u.SkeletalMeshEditorSubsystem.get_lod_count(mesh),'materials':len(mesh.materials),'lod0_vertices':u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem).get_num_verts(mesh,0),'instances':0}
  meshes[p]['instances']+=1
  skeletal.append({'actor':a.get_actor_label(),'class':a.get_class().get_name(),'mesh':p,'location':list(a.get_actor_location().to_tuple()),'hidden':a.is_hidden_ed()})
 for c in a.get_components_by_class(u.GroomComponent):
  g=c.get_editor_property('groom_asset')
  if g:grooms.append({'actor':a.get_actor_label(),'groom':g.get_path_name(),'groups':[x.export_text() for x in g.get_editor_property('hair_groups_info')],'hidden':a.is_hidden_ed()})
 for c in a.get_components_by_class(u.LightComponent):lights[c.get_class().get_name()]+=1
cvars={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ('r.RayTracing','r.Lumen.HardwareRayTracing','r.HairStrands.Strands','r.TextureStreaming','r.Streaming.PoolSize','r.ScreenPercentage','sg.ViewDistanceQuality','sg.ShadowQuality','sg.TextureQuality','sg.EffectsQuality','sg.GlobalIlluminationQuality','sg.ReflectionQuality')}
report={'kind':'Editor-open asset/VRAM baseline; not 4K runtime FPS','actors':len(actors),'skeletal_components':skeletal,'skeletal_meshes':meshes,'groom_components':grooms,'lights':dict(lights),'cvars':cvars,'dirty_maps':[x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'dirty_content':[x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
(OUT/'Inventory.json').write_text(json.dumps(report,indent=2)+'\n')
u.SystemLibrary.execute_console_command(world,'memreport -full')
u.SystemLibrary.execute_console_command(world,'rhi.DumpResourceMemory')
print(json.dumps({'actors':len(actors),'skeletal_components':len(skeletal),'unique_skeletal_meshes':len(meshes),'grooms':len(grooms),'lights':dict(lights),'cvars':cvars}))
