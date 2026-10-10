"""Complete only the inspected material-only partial169; never replay apply()."""
import unreal as u,json
def complete(r):
 assert r.report['status']=='FAILED_INSPECT_BEFORE_RETRY' and not r.new
 assert r.sha(r.MAP)==r.SHA and len(r.EAS.get_all_level_actors())==9051
 assert not any(a.get_actor_label().startswith(r.PREFIX) for a in r.EAS.get_all_level_actors())
 before=json.loads((r.OUT/'original-actors.json').read_text())
 assert all(r.snapshot(a)==before[a.get_name()] for a in r.original)
 mat=u.load_asset(r.DEST+'/MI_PolishedPole');assert mat and abs(u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mat,'Min Roughness')-.12)<1e-5
 for key,value in {'Min Roughness':.12,'Max Roughness':.24,'Normal Intensity':.3,'Opacity Value (Dirt)':0.,'Opacity (Damage)':0.}.items():
  u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mat,key,value)
  assert abs(u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mat,key)-value)<1e-5,key
 u.MaterialEditingLibrary.update_material_instance(mat);assert u.EditorAssetLibrary.save_loaded_asset(mat)
 bp=u.load_asset(r.JOY+'/BP_JoyLightBlue_Review');assert bp and bp.generated_class()
 joy=r.name(r.EAS.spawn_actor_from_class(bp.generated_class(),u.Vector(7018,5020,-169.5)),'Joy');r.new.append(joy)
 r.animation(joy.get_component_by_class(u.SkeletalMeshComponent),r.JOY+'/Animations/A_Joy_PoleIdle')
 cy=r.name(r.EAS.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(7220,5130,-169.5)),'Cyborg girl');r.new.append(cy)
 cy.set_actor_rotation(u.Rotator(yaw=-30),False);body=cy.skeletal_mesh_component;body.set_skeletal_mesh_asset(u.load_asset(r.CYB+'/Rig/SK_Cyborg'));r.animation(body,r.CYB+'/A_Cyborg_Idle')
 for n,p,d,h,solid in [('Pole/Shaft',(7000,5000,30),4.5,396,True),('Pole/Floor mount',(7000,5000,-168.5),24,3,False),('Pole/Floor collar',(7000,5000,-165),8,5,False),('Pole/Ceiling mount',(7000,5000,229),24,3,False),('Pole/Ceiling collar',(7000,5000,225.5),8,5,False)]:
  r.new.append(r.cylinder(n,p,d,h,mat,solid))
 assert all(r.snapshot(a)==before[a.get_name()] for a in r.original)
 r.report.update(status='PLACED_UNSAVED',new_actors=[{'name':a.get_name(),**r.snapshot(a)} for a in r.new],material=r.DEST+'/MI_PolishedPole',existing_preserved=True,partial169_resolution='Scalar setter returned false although value applied; all five values verified through getters before continuing170.')
 (r.OUT/'receipt.json').write_text(json.dumps(r.report,indent=2))
 return r.save()
