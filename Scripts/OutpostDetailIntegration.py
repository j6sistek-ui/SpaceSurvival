"""Integrate the reviewed density and finish pass in the private saved outpost.

No engine launch or map save occurs here. AuthorOutpostSandbox saves its new
private world first, invokes this pass, validates, then saves the completed map.
"""
import json


def apply(api):
    u=api['u']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != api['TARGET'] or api['TARGET'] != '/Game/OutpostSandbox/L_AsteroidOutpost':
        raise RuntimeError('Detail integration requires the saved private outpost')
    report={}
    # Repair existing balanced assets from their native parent. Private deck
    # finishes may wrap those instances; their parent updates remain inherited.
    seen=set()
    for actor in api['EAS'].get_all_level_actors():
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            for slot,current in enumerate(component.get_materials()):
                parent=current
                chain=set()
                while isinstance(parent,u.MaterialInstanceConstant):
                    path=parent.get_path_name()
                    if path in chain:raise RuntimeError('Cyclic material chain: '+path)
                    chain.add(path)
                    if path.startswith('/Game/OutpostSandbox/Materials/MI_Balanced_'):
                        if path not in seen:
                            api['balanced'](parent);seen.add(path)
                        break
                    parent=parent.get_editor_property('parent')
    report['rebalanced_private_materials']=len(seen)
    import OutpostAtriumDetails,OutpostPromenadeDetails
    report['atrium']=OutpostAtriumDetails.build(api)
    report['promenade']=OutpostPromenadeDetails.build(api)
    import OutpostEngineeringBacking
    report['engineering_backing']=OutpostEngineeringBacking.build(api)
    import OutpostLocalLights,OutpostMarketPresentation,OutpostSurfaceFinish
    original=OutpostLocalLights.inventory(api)
    report['vendor_light_policy']=OutpostLocalLights.apply(api,original)
    report['market_presentation']=OutpostMarketPresentation.build(api)
    report['surfaces']=OutpostSurfaceFinish.apply(api)
    import OutpostQuietCeilings
    report['quiet_ceilings']=OutpostQuietCeilings.apply(api)
    import OutpostQuietPromenade,OutpostSatinPanels
    report['quiet_promenade']=OutpostQuietPromenade.apply(api)
    report['satin_panels']=OutpostSatinPanels.apply(api)
    import OutpostTaskAreaLights,OutpostArcadeMaterials,OutpostInteriorFinishPreview
    report['task_lights']=OutpostTaskAreaLights.apply(api)
    report['arcade_material']=OutpostArcadeMaterials.apply(api)
    report['clean_metal']=OutpostInteriorFinishPreview.apply_clean(api)
    import OutpostWorkstationFinish
    report['workstation_finish']=OutpostWorkstationFinish.apply(api)
    import OutpostArchivePresentation
    report['archive_presentation']=OutpostArchivePresentation.apply(api)
    import OutpostDistantWorld
    report['distant_world']=OutpostDistantWorld.apply(api)
    import OutpostSkylineDisplays
    report['skyline_displays']=OutpostSkylineDisplays.build(api)
    import OutpostInteriorGraphics
    report['interior_graphics']=OutpostInteriorGraphics.apply(api)
    import OutpostInteriorReadability,OutpostReadability
    report['interior_readability']=OutpostInteriorReadability.apply(api)
    report['text_readability']=OutpostReadability.apply(api)
    import OutpostFrontLighting
    report['front_lighting']=OutpostFrontLighting.apply(api)
    import OutpostBlueSignage,OutpostPublicLighting,OutpostSkylineAtmosphere
    report['blue_signage']=OutpostBlueSignage.apply(api)
    report['public_lighting']=OutpostPublicLighting.apply(api)
    report['skyline_atmosphere']=OutpostSkylineAtmosphere.apply(api)
    import OutpostPadTrim
    report['pad_trim']=OutpostPadTrim.apply(api)
    report['promenade_native']=OutpostPromenadeDetails.audit_native(api)
    if report['promenade_native']['failures']:
        raise RuntimeError('New promenade clearance audit failed; map not saved')
    (api['OUT']/'detail-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
