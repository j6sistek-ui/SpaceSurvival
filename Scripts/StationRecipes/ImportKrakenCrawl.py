"""Import the separately reviewed Kraken animation without replacing its mesh or skeleton."""
import unreal as u,json,hashlib
from pathlib import Path
P=Path(u.Paths.project_dir()).resolve();R=P/'.agent/local/KrakenMotion_20261021'
root='/Game/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015/Crawl_20261021'
skpath='/Game/SpaceSurvival/Licensed/StationAssets/KrakenRefresh_20261015/SK_Kraken_Skeleton'
sk=u.load_asset(skpath);assert sk
skfile=P/('Content/'+skpath.removeprefix('/Game/')+'.uasset')
before=hashlib.sha256(skfile.read_bytes()).hexdigest()
name='A_Kraken_IndependentCrawl_24s';assert not u.EditorAssetLibrary.does_asset_exist(root+'/'+name)
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
t=u.AssetImportTask();t.filename=str(R/'Kraken_IndependentCrawl_24s.fbx');t.destination_path=root;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=False;t.factory=u.FbxFactory()
o=u.FbxImportUI();o.import_mesh=False;o.import_as_skeletal=True;o.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION;o.automated_import_should_detect_type=False;o.import_animations=True;o.skeleton=sk;o.import_materials=False;o.import_textures=False
o.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);o.anim_sequence_import_data.set_editor_property('custom_sample_rate',25);t.options=o
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);a=u.load_asset(root+'/'+name)
assert isinstance(a,u.AnimSequence) and a.get_editor_property('skeleton')==sk
assert abs(a.sequence_length-24)<.001
assert hashlib.sha256(skfile.read_bytes()).hexdigest()==before
(R/'Imported.json').write_text(json.dumps({'path':a.get_path_name(),'skeleton':skpath,'source_skeleton_unchanged':True,'length':a.sequence_length,'objects':list(t.imported_object_paths)},indent=2))
