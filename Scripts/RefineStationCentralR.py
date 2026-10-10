"""Reversible final dressing of central reception and the R wardrobe room.

The lead must inspect the exact saved map, retain a map backup, then review in PIE.
This changes placed actors only. T hardware and source kit assets are untouched.
"""
import hashlib
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PREFIX = 'Refine/StationFinish20261009/'
GUIDE = '/Game/OutpostSandbox/StationRefinement/WardrobeGuide20261009'


def apply(u, expected_sha256):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert not editor.get_game_world() and world.get_path_name().split('.')[0] == MAP
    file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Preserve dirty map'
    guide = u.load_asset(GUIDE + '/M_WardrobeGuide')
    assert guide, 'Stage and review the wardrobe guide before placing its console'
    subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors), 'Already refined'
    state = {'actors':[], 'new':[], 'lights':[], 'tags':[]}

    def one(label):
        matches = [a for a in actors if a.get_actor_label() == label]
        assert len(matches) == 1, label
        return matches[0]

    def keep(a):
        if not any(r[0] == a for r in state['actors']):
            state['actors'].append((a, a.get_actor_transform(), a.hidden, a.get_actor_enable_collision()))
        a.modify()
        return a

    def hide(a):
        keep(a).set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)

    def label_new(a, label):
        state['new'].append(a)
        a.set_actor_label(PREFIX + label)
        a.set_editor_property('tags', [u.Name('OutpostAuthored'), u.Name('OutpostLabel:' + PREFIX + label)])
        return a

    def prop(name, mesh_name, xy, base_z, width, yaw=0., max_height=None):
        mesh = u.load_asset(mesh_name if mesh_name.startswith('/Game/') else
                            '/Game/Cyberpunk_Room/Mesh/' + mesh_name)
        assert mesh, mesh_name
        a = label_new(subsystem.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*xy,base_z)), name)
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        c.set_collision_profile_name('NoCollision')
        b = mesh.get_bounds()
        scale = width / max(b.box_extent.x * 2., b.box_extent.y * 2.)
        if max_height is not None:
            scale = min(scale, max_height / (b.box_extent.z * 2.))
        a.set_actor_scale3d(u.Vector(scale,scale,scale))
        a.set_actor_rotation(u.Rotator(yaw=yaw), False)
        center, extent = a.get_actor_bounds(False)
        a.set_actor_location(a.get_actor_location() + u.Vector(xy[0]-center.x,xy[1]-center.y,
                             base_z-(center.z-extent.z)), False, True)
        return a

    try:
        for suffix in ('-130','130'):
            keep(one('Refine/Reception/Welcome console ' + suffix)).set_actor_scale3d(u.Vector(.42,.42,.42))
        prop('Reception/Visitor forms','SM_Paper_Pile_01',(3983.,-173.),106.,22.,-135.)
        prop('Reception/Pens','SM_pens_01',(4000.,-215.),106.,9.,-120.,14.)
        prop('Reception/Water','SM_Bottle_01',(3976.,160.),106.,7.,0.)

        # Waiting and consultation, with small reading objects instead of tall game projections.
        for number in (1,2):
            base = 'LoungeNative/Conversation ' + str(number)
            for part in (1,2,3):
                hide(one(base + '/West/SM_TitaniumIndustrySeat_V1_Part' + str(part)))
            hide(one(base + '/Projector'))
            hide(one(base + '/Animated game'))
        prop('Archive/Tablet A','SM_Tablet',(3440.,2855.),64.,30.,-20.)
        prop('Archive/Catalog A','SM_Books_02',(3460.,2893.),64.,26.,15.)
        prop('Archive/Tablet B','SM_Tablet',(3425.,3700.),64.,30.,15.)
        prop('Archive/Catalog B','SM_Books_03',(3460.,3730.),64.,24.,-12.)

        # Keep the real terminal/use point and use a complete owned standing console.
        for part in ('Foot','Stem','Display','Status line','Console support'):
            hide(one('Services/CREW WARDROBE/' + part))
        terminal = prop('Archive/Wardrobe terminal',
             '/Game/Fab/Sci_fi_Console_Game/SM_Sci_fi_Console_Game',
             (4750.,3570.),0.,52.,180.,133.4)
        terminal.static_mesh_component.set_material(1, guide)
        face = keep(one('Services/CREW WARDROBE/Face'))
        face.set_actor_location(u.Vector(4750.,3539.,143.),False,True)
        help_text = label_new(subsystem.duplicate_actor(one('Refine/Archive/Identity'),world),
                              'Archive/Wardrobe instructions')
        help_text.set_actor_location(u.Vector(4200.,4433.,272.),False,True)
        help_text.text_render.set_text('CHOOSE YOUR CHARACTER\nUse the Crew Wardrobe console.\nSelect a character to wear it.')
        help_text.text_render.set_world_size(11.)
        help_text.text_render.set_text_render_color(u.Color(173,227,237,255))

        for label, position, yaw in (
            ('Refine/Archive/Conversation guest A',(4425.,3570.,85.),-111.5),
            ('Refine/Archive/Conversation guest B',(4350.,3380.,85.),65.),
        ):
            a = keep(one(label))
            a.set_actor_location(u.Vector(*position),False,True)
            a.set_actor_rotation(u.Rotator(yaw=yaw),False)
        guide = one('Refine/Archive/Conversation guest A')
        state['tags'].append((guide,list(guide.tags)))
        guide.set_editor_property('tags', list(guide.tags) + [u.Name('StationJob:Wardrobe consultation')])

        for label, intensity in (
            ('UsableLighting/Lounge/Ceiling 1',1400.),('UsableLighting/Lounge/Ceiling 2',1400.),
            ('LoungeNative/Conversation 1/Task light',650.),('LoungeNative/Conversation 2/Task light',650.),
            ('Lounge/Wardrobe key',850.),('Refine/CentralWelcomeGreeneryLights1/ReceptionFront',2000.),
        ):
            c = one(label).get_component_by_class(u.LightComponent)
            assert c
            state['lights'].append((c,c.intensity))
            c.modify()
            c.set_intensity(intensity)
        return state
    except Exception:
        restore(u,state)
        raise


def restore(u,state):
    for a in reversed(state['new']):
        u.get_editor_subsystem(u.EditorActorSubsystem).destroy_actor(a)
    for c,intensity in state['lights']:
        c.set_intensity(intensity)
    for a,tags in state['tags']:
        a.set_editor_property('tags',tags)
    for a,transform,hidden,collision in reversed(state['actors']):
        a.set_actor_transform(transform,False,True)
        a.set_actor_hidden_in_game(hidden)
        a.set_actor_enable_collision(collision)


def stage_wardrobe_guide(u):
    """Create two new private assets only; caller saves after reviewing the screen."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    names = (GUIDE+'/T_WardrobeGuide', GUIDE+'/M_WardrobeGuide')
    assert all(not u.EditorAssetLibrary.does_asset_exist(n) for n in names), 'Inspect existing/partial staging'
    root = Path(u.Paths.project_dir()).resolve() / 'ContentSource/WardrobeConsole'
    import json
    manifest = json.loads((root/'manifest.json').read_text('utf-8'))
    assert hashlib.sha256((root/'Wardrobe.png').read_bytes()).hexdigest() == manifest['sha256']['Wardrobe.png']
    task = u.AssetImportTask()
    for key,value in {'filename':str(root/'Wardrobe.png'),'destination_path':GUIDE,
                      'destination_name':'T_WardrobeGuide','automated':True,
                      'replace_existing':False,'save':False}.items():
        task.set_editor_property(key,value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = u.load_asset(names[0])
    assert isinstance(texture,u.Texture2D), 'Inspect partial import; never rerun blindly'
    texture.set_editor_property('srgb',True)
    texture.set_editor_property('address_x',u.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset('M_WardrobeGuide',GUIDE,u.Material,u.MaterialFactoryNew())
    assert material
    material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    sample = u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionTextureSample)
    sample.set_editor_property('texture',texture)
    finish_wardrobe_material(u, material, sample)
    u.MaterialEditingLibrary.recompile_material(material)
    return texture,material


def finish_wardrobe_material(u, material, sample):
    """The owned console's monitor UVs need V flipped; retain source mesh/materials."""
    lib = u.MaterialEditingLibrary
    uv = lib.create_material_expression(material,u.MaterialExpressionTextureCoordinate)
    uv.set_editor_property('v_tiling',-1.)
    offset = lib.create_material_expression(material,u.MaterialExpressionConstant2Vector)
    offset.set_editor_property('r',0.)
    offset.set_editor_property('g',1.)
    add = lib.create_material_expression(material,u.MaterialExpressionAdd)
    gain = lib.create_material_expression(material,u.MaterialExpressionMultiply)
    gain.set_editor_property('const_b',8.)
    assert lib.connect_material_expressions(uv,'',add,'A')
    assert lib.connect_material_expressions(offset,'',add,'B')
    assert lib.connect_material_expressions(add,'',sample,'UVs')
    assert lib.connect_material_expressions(sample,'RGB',gain,'A')
    assert lib.connect_material_property(gain,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
