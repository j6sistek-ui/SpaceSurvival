"""One-off repair for the three JoyBartender material masters made before 2026-10-14's fix: the SuitMask sampler was
Linear Color with the engine's sRGB white square as default, a compile error that dropped every instance to the
fallback. Points the sampler at the TC_MASKS strap mask with a Masks sampler, recompiles and saves. Prints the
compile state of each master and instance afterwards.
"""
import unreal as u

B = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender"
E = u.MaterialEditingLibrary
L = u.EditorAssetLibrary


def log(s):
    u.log_warning("REPAIR| " + str(s))


mask = u.load_asset(B + "/Textures/T_Joy_Std_Skin_Body_SuitMask")
assert isinstance(mask, u.Texture2D)
mask.set_editor_property("srgb", False)
mask.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_MASKS)
mask.set_editor_property("virtual_texture_streaming", False)
assert L.save_loaded_asset(mask, False)
for name in ("M_JoyBOpaque", "M_JoyBMasked", "M_JoyBTranslucent"):
    m = u.load_asset(B + "/Materials/" + name)
    assert isinstance(m, u.Material), name
    fixed = 0
    for x in E.get_material_expressions(m):
        if isinstance(x, u.MaterialExpressionTextureSampleParameter2D) and str(x.get_editor_property("parameter_name")) == "SuitMask":
            x.set_editor_property("texture", mask)
            x.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_MASKS)
            fixed += 1
    E.recompile_material(m)
    assert L.save_loaded_asset(m, False), name
    log("%s: %d SuitMask samplers fixed, recompiled, saved" % (name, fixed))
# every texture her instances use must not be a virtual texture (the samplers are plain 2D)
for ad in u.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(B + "/Textures", True):
    t = ad.get_asset()
    if isinstance(t, u.Texture2D) and t.get_editor_property("virtual_texture_streaming"):
        t.set_editor_property("virtual_texture_streaming", False)
        assert L.save_loaded_asset(t, False)
        log("virtual texture streaming turned off: " + t.get_name())
log("DONE")
