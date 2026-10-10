"""One-shot Central concept features, with explicit staging and no implicit save.

Run geometry() outside Unreal, import_geometry() once, then apply() on the exact
saved candidate. Original maps, vendor assets, actors and the other rooms remain.
"""
import hashlib
import math
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/CentralFeatures99'
PREFIX = 'Refine/CentralFeatures99/'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'
OLD = '/Game/OutpostSandbox/StationRefinement/CentralArchitecture97/'


def geometry(folder):
    """Closed beveled annular sections in centimetres, with normals and UVs."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    specs = [('SM_CentralCeilingRing', 1310, 1360, 24, 3, 360, 128),
             ('SM_CentralWarmRing', 1323, 1329, 3, .5, 360, 128),
             ('SM_CentralInnerRing', 875, 900, 20, 2, 360, 128),
             ('SM_CentralPlanter', 1260, 1380, 64, 5, 24, 16),
             ('SM_CentralPlanterSoil', 1274, 1366, 4, 1, 23, 16),
             ('SM_CentralPlanterLip', 1258, 1382, 5, 1, 24, 16)]
    for name, inner, outer, height, bevel, arc, steps in specs:
        path = folder / (name + '.obj')
        assert not path.exists(), 'Keep prior generated source'
        cross = [(inner+bevel,-height/2),(outer-bevel,-height/2),
                 (outer,-height/2+bevel),(outer,height/2-bevel),
                 (outer-bevel,height/2),(inner+bevel,height/2),
                 (inner,height/2-bevel),(inner,-height/2+bevel)]
        closed = arc == 360
        count = steps if closed else steps+1
        vertices = []
        for i in range(count):
            angle=math.radians(-arc/2+arc*i/steps)
            vertices += [(r*math.cos(angle),r*math.sin(angle),z) for r,z in cross]
        faces=[]
        for i in range(steps):
            j=(i+1)%count
            for k in range(8):
                n=(k+1)%8
                faces.append((i*8+k,j*8+k,j*8+n,i*8+n))
        if not closed:
            # End caps oppose the boundary edge winding of the adjoining sides.
            faces += [tuple(range(8)),tuple((count-1)*8+k for k in reversed(range(8)))]
        lines=['# Original Central modular geometry, centimetres','o '+name]
        lines += ['v %.6f %.6f %.6f'%v for v in vertices]
        lines += ['vt 0 0','vt 1 0','vt 1 1','vt 0 1']
        for face in faces:
            a,b,c=[vertices[v] for v in face[:3]]
            ab=[b[k]-a[k] for k in range(3)];ac=[c[k]-a[k] for k in range(3)]
            normal=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
            length=math.sqrt(sum(n*n for n in normal))
            lines.append('vn %.8f %.8f %.8f'%tuple(n/length for n in normal))
        for i,face in enumerate(faces,1):
            # Triangulate arbitrary cap polygons; quads retain matching winding.
            for j in range(1,len(face)-1):
                tri=(face[0],face[j],face[j+1])
                lines.append('f '+' '.join('%d/%d/%d'%(v+1,k+1,i) for k,v in enumerate(tri)))
        path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return [str(folder/(s[0]+'.obj')) for s in specs]


def import_geometry(u, folder, apply=False):
    paths=sorted(Path(folder).glob('SM_Central*.obj'))
    assert len(paths)==6
    assert not u.EditorAssetLibrary.does_directory_exist(PRIVATE)
    if not apply:return {'dry_run':True,'meshes':[p.stem for p in paths]}
    tasks=[]
    for p in paths:
        task=u.AssetImportTask()
        for k,v in dict(filename=str(p),destination_path=PRIVATE,destination_name=p.stem,
                        automated=True,replace_existing=False,save=False).items():
            task.set_editor_property(k,v)
        opts=u.FbxImportUI()
        for k,v in dict(import_mesh=True,import_as_skeletal=False,import_materials=False,
                        import_textures=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH).items():
            opts.set_editor_property(k,v)
        data=opts.static_mesh_import_data
        for k,v in dict(combine_meshes=True,auto_generate_collision=False,
                        generate_lightmap_u_vs=True,import_uniform_scale=1.,convert_scene=False,
                        force_front_x_axis=False,normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
            data.set_editor_property(k,v)
        task.options=opts;task.factory=u.FbxFactory();tasks.append(task)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    report=[]
    for p,t in zip(paths,tasks):
        found=[u.load_asset(q) for q in t.imported_object_paths]
        assert len(found)==1 and isinstance(found[0],u.StaticMesh),str(p)
        mesh=found[0]
        assert mesh.get_path_name().split('.')[0]==PRIVATE+'/'+p.stem
        report.append({'asset':mesh.get_path_name(),'origin':mesh.get_bounds().origin.to_tuple(),
                       'extent':mesh.get_bounds().box_extent.to_tuple()})
    return report


def apply(u, expected_sha, execute=False):
    ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert ed.get_editor_world().get_path_name().split('.')[0]==MAP and not ed.get_game_world()
    mapfile=Path(u.Paths.project_content_dir())/(MAP.removeprefix('/Game/')+'.umap')
    assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==expected_sha
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    actors=list(sub.get_all_level_actors())
    assert len(actors)==8756 and not any(a.get_actor_label().startswith(PREFIX) for a in actors)
    for name in ('SM_CentralCeilingRing','SM_CentralWarmRing','SM_CentralInnerRing',
                 'SM_CentralPlanter','SM_CentralPlanterLip','SM_CentralPlanterSoil'):
        assert u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
    if not execute:return {'dry_run':True,'features':['Two-tier radial ceiling','Four portal surrounds',
                    'Four planted seating bays','Sculpted concierge','Warm physical light sources']}
    state={'new':[],'originals':[],'materials':[],'private':[]}
    lib=u.MaterialEditingLibrary
    def one(label):
        f=[a for a in actors if a.get_actor_label()==label]
        assert len(f)==1,label
        return f[0]
    def keep(a):
        if not any(v[0]==a for v in state['originals']):
            state['originals'].append((a,a.get_actor_transform(),a.hidden,a.get_actor_enable_collision()))
            a.modify()
        return a
    def surface(a,m,slots=None):
        c=a.static_mesh_component;c.modify()
        state['materials'].append((c,list(c.get_materials())))
        for i in range(c.get_num_materials()) if slots is None else slots:c.set_material(i,m)
    def named(a,label):
        a.set_actor_label(PREFIX+label);a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostLabel:'+PREFIX+label)])
        state['new'].append(a);return a
    def mi(name,parent,vectors=None,scalars=None):
        assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
        m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PRIVATE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        state['private'].append(m);lib.set_material_instance_parent(m,u.load_asset(parent))
        for k,v in (vectors or {}).items():
            assert k in map(str,lib.get_vector_parameter_names(m)),k
            lib.set_material_instance_vector_parameter_value(m,k,u.LinearColor(*v))
        for k,v in (scalars or {}).items():
            assert k in map(str,lib.get_scalar_parameter_names(m)),k
            lib.set_material_instance_scalar_parameter_value(m,k,v)
        lib.update_material_instance(m);return m
    def mesh(label,path,center,size=None,rot=None,material=None,collision=False,scale=None):
        m=u.load_asset(path);assert isinstance(m,u.StaticMesh),path
        a=named(sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),label)
        c=a.static_mesh_component;c.set_static_mesh(m)
        a.set_actor_rotation(rot or u.Rotator(),False)
        ext=m.get_bounds().box_extent
        a.set_actor_scale3d(u.Vector(*(size[i]/(2*ext.to_tuple()[i]) for i in range(3))) if size else u.Vector(*(scale or (1,1,1))))
        p,_=a.get_actor_bounds(False);a.set_actor_location(u.Vector(*center)-p,False,True)
        c.set_collision_profile_name('BlockAll' if collision else 'NoCollision');a.set_actor_enable_collision(collision)
        if material:
            for i in range(c.get_num_materials()):c.set_material(i,material)
        return a
    def atpolar(angle,radius,z):
        r=math.radians(angle);return (4200+radius*math.cos(r),radius*math.sin(r),z)
    def beam(label,a,b,width,depth,material,path='/Engine/BasicShapes/Cube'):
        a,b=u.Vector(*a),u.Vector(*b)
        return mesh(label,path,((a+b)*.5).to_tuple(),((b-a).length(),width,depth),u.MathLibrary.find_look_at_rotation(a,b),material)
    def light(label,position,target,power,radius,width=25,height=150):
        a=named(sub.spawn_actor_from_class(u.RectLight,u.Vector(*position)),label)
        a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*position),u.Vector(*target)),False)
        c=a.rect_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_intensity_units(u.LightUnits.LUMENS);c.set_intensity(power)
        c.set_light_color(u.LinearColor(1,.71,.43,1));c.set_attenuation_radius(radius)
        c.set_source_width(width);c.set_source_height(height);c.set_cast_shadows(False)
        c.set_indirect_lighting_intensity(.45);c.set_volumetric_scattering_intensity(0)
        return a
    try:
        dark=mi('MI_Graphite','/Game/OutpostSandbox/Materials/M_OutpostGraphite',{'HullTint':(.055,.064,.073,1)})
        bronze=mi('MI_Champagne',OLD+'MI_ChampagneJoinery',{'Albedo Tint':(.36,.24,.12,1)},
                  {'Albedo Tint Intensity':1.,'Opacity (Damage)':.08,'Opacity Value (Dirt)':.08})
        warm=mi('MI_SolidWarm','/Game/OutpostSandbox/Materials/M_OutpostWorkstationWarmLens',{'HullTint':(5.,2.65,.95,1)})
        soil=u.load_asset('/Game/P1toP5_Bundle/P5_FruitSeller/Materials/Instances/Opaque/MI_Mud04')
        sofa_mesh=u.EditorAssetLibrary.duplicate_asset('/Game/Clinic/Meshes/Props/SM_Entrance_Sofa01',PRIVATE+'/SM_CentralSofaCollidable')
        assert sofa_mesh
        state['private'].append(sofa_mesh)
        mesh_edit=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        mesh_edit.remove_collisions(sofa_mesh)
        mesh_edit.add_simple_collisions(sofa_mesh,u.ScriptingCollisionShapeType.BOX)
        assert mesh_edit.get_simple_collision_count(sofa_mesh)==1
        palette={}
        for a in actors:
            if not isinstance(a,u.StaticMeshActor):continue
            label=a.get_actor_label()
            if label=='Atrium/Upper service panel' or label.startswith('Atrium/Bay ') and '/Panel ' in label:
                c=a.static_mesh_component
                for i,old in enumerate(c.get_materials()):
                    if old and old.get_path_name().startswith(OLD):
                        key=old.get_path_name()
                        if key not in palette:
                            palette[key]=mi('MI_Wall_'+hashlib.sha256(key.encode()).hexdigest()[:8],key,
                              {'Albedo Tint':(.055,.065,.078,1),'Albedo Tint (Damage)':(.07,.075,.08,1)},
                              {'Albedo Tint Intensity':1.,'Albedo (Damage)':1.,'Opacity (Damage)':.12,'Opacity Value (Dirt)':.12})
                        surface(a,palette[key],[i])
        # Solid emissive lenses replace a translucent hologram material on fixtures.
        for a in actors:
            label=a.get_actor_label()
            if '/Rib ' in label and label.endswith('/Housing') or label.startswith('Refine/CentralArchitecture97/Bay ') and label.endswith('/Warm fixture'):
                keep(a);surface(a,warm,[0])
                p,b=a.get_actor_bounds(False)
                rotation=a.get_actor_rotation();rotation.yaw+=180
                a.set_actor_rotation(rotation,False)
                q,_=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+p-q,False,True)
        # Two radial ceiling tiers below the existing structural annulus.
        for i in range(16):
            angle=i*22.5
            for tier,radius,length,width in [('Inner',1070,550,245),('Outer',1480,280,510)]:
                a=mesh('Ceiling/%s panel %02d'%(tier,i),P4+'SM_UniversalPanel400X200_V1',atpolar(angle,radius,649),
                       (length,width,34),u.Rotator(roll=180,yaw=angle))
                for slot in range(5):a.static_mesh_component.set_material(slot,dark if slot!=3 else bronze)
                for slot in (5,6):a.static_mesh_component.set_material(slot,dark)
            beam('Ceiling/Radial rib %02d'%i,atpolar(angle+11.25,790,631),atpolar(angle+11.25,1645,631),
                 30,24,bronze,P4+'SM_CornerWallCeiling400X70_V13_ElectricalEquipment')
        for name,asset,z,mat in [('Crown','SM_CentralCeilingRing',626,dark),('Amber seam','SM_CentralWarmRing',612,warm),
                                 ('Inner lip','SM_CentralInnerRing',634,bronze)]:
            mesh('Ceiling/'+name,PRIVATE+'/'+asset,(4200,0,z),material=mat)
        for i in range(8):
            angle=i*45
            light('Ceiling/Wash %02d'%i,atpolar(angle,1320,604),atpolar(angle,1470,300),1150,650,180,25)
        # Portals preserve the full original clear opening (660cm x350cm).
        for i,angle in enumerate((0,90,180,270)):
            base=u.Vector(*atpolar(angle,1510,0));r=math.radians(angle)
            tangent=u.Vector(-math.sin(r),math.cos(r),0)
            outline=[(-370,0),(-370,315),(-275,410),(275,410),(370,315),(370,0)]
            for j in range(len(outline)-1):
                def p(v,depth=0):return (base+tangent*v[0]+u.Vector(0,0,v[1])+u.Vector(math.cos(r),math.sin(r),0)*depth).to_tuple()
                beam('Portal %d/Frame %d'%(i,j),p(outline[j]),p(outline[j+1]),42,44,dark,P4+'SM_CornerWallCeiling400X70_V13_ElectricalEquipment')
                beam('Portal %d/Join %d'%(i,j),p(outline[j],-23),p(outline[j+1],-23),7,7,bronze)
                a0,b0=outline[j],outline[j+1]
                if j not in (0,4):beam('Portal %d/Light %d'%(i,j),p(a0,-28),p(b0,-28),3.5,3.5,warm)
            light('Portal %d/Header light'%i,atpolar(angle,1465,396),atpolar(angle,1250,100),1600,450,300,20)
        # Curved broad planter banks on all four diagonal solid wall bays.
        for i,angle in enumerate((45,135,225,315)):
            for kind,z,mat in [('Planter',32,bronze),('PlanterLip',65,dark),('PlanterSoil',68,soil)]:
                a=mesh('Waiting %d/%s'%(i,kind),PRIVATE+'/SM_Central'+kind,(0,0,z),rot=u.Rotator(yaw=angle),material=mat)
                # Source arc is centred on room origin, not on its own bounds.
                a.set_actor_location(u.Vector(4200,0,z),False,True)
            # Hidden box supports block the actual planter footprint, not aisle.
            for j in (-8,0,8):
                a=mesh('Waiting %d/Planter collision %d'%(i,j),'/Engine/BasicShapes/Cube',atpolar(angle+j,1320,30),
                       (90,190,60),u.Rotator(yaw=angle+j),dark,True)
                a.set_actor_hidden_in_game(True)
            for j in range(7):
                plant_angle=angle-10+j*(20/6)
                asset='/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_ConstructionPart'+str(108+j%6)+'_Plant'
                height=145 if j%2 else 180
                mesh('Waiting %d/Broadleaf %d'%(i,j),asset,atpolar(plant_angle,1320,70+height/2),
                     (125,135,height),u.Rotator(yaw=plant_angle+j*73))
            for j in range(4):
                mesh('Waiting %d/Low planting %d'%(i,j),'/Game/Nanite_Plants_Sample_Collection/Geometries/SM_Abelia_x_grandiflora_Nanite_Free_Sample',
                     atpolar(angle-8+j*5.3,1285,102),(125,120,82),u.Rotator(yaw=j*91+angle))
            light('Waiting %d/Plant wash'%i,atpolar(angle,1200,60),atpolar(angle,1330,150),550,340,120,40)
            # Existing seated visitors and their benches retain exact contacts.
            if i in (1,3):
                sofa=mesh('Waiting %d/Sofa'%i,PRIVATE+'/SM_CentralSofaCollidable',atpolar(angle,1190,41.6),
                          (284,86,83.2),u.Rotator(yaw=angle+90),collision=True)
                surface(sofa,u.load_asset('/Game/OutpostSandbox/StationRefinement/ArchiveConcept77/MI_ArchiveUpholstery'))
        # Existing tiny square planters and sparse trees are superseded by the
        # contiguous banks. Keep the occupied benches and all NPC identities.
        for a in actors:
            label=a.get_actor_label()
            if (label.startswith('Refine/Concept73/Waiting/') and any(s in label for s in ('Plant ','Understory '))) or \
               ('CentralWelcomeArrival2/' in label and '/Planter ' in label) or \
               (label.startswith('Refine/CentralArchitecture97/Waiting ') and label.rsplit('/',1)[-1] in ('Planter','Tree','Understory')):
                keep(a);a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(False)
        # Concierge: existing detailed fascias receive the same graphite palette,
        # warm structural ribs and a low glowing reveal under the original lip.
        for a in actors:
            label=a.get_actor_label()
            if label.startswith('Refine/CentralArchitecture97/Reception/Fascia '):
                surface(a,dark,[0,1,2,3,4])
            elif label.startswith('Refine/CentralArchitecture97/Reception/Joint '):
                surface(a,bronze)
                keep(a);a.set_actor_scale3d(a.get_actor_scale3d()*u.Vector(1.5,3,1))
        mesh('Reception/Lower light','/Game/OutpostSandbox/Geometry/SM_OutpostHalo',(4200,0,8),(600,600,3),material=warm)
        mesh('Reception/Plinth','/Game/OutpostSandbox/Geometry/SM_OutpostCollar',(4200,0,5),(606,606,7),material=dark)
        # Warm lenses in narrow mechanical bases at existing reading tables.
        for group in ('NW','SE'):
            table=one('Refine/CentralArchitecture97/Waiting '+group+'/Table');p,e=table.get_actor_bounds(False)
            position=(p.x+22,p.y-18,p.z+e.z+2)
            mesh('Reading '+group+'/Base','/Engine/BasicShapes/Cylinder',position,(14,14,4),material=bronze)
            mesh('Reading '+group+'/Stem','/Engine/BasicShapes/Cylinder',(position[0],position[1],position[2]+11),(3,3,20),material=bronze)
            mesh('Reading '+group+'/Lens','/Engine/BasicShapes/Cylinder',(position[0],position[1],position[2]+20),(11,11,15),material=warm)
            mesh('Reading '+group+'/Cap','/Engine/BasicShapes/Cylinder',(position[0],position[1],position[2]+28),(13,13,2),material=bronze)
            light('Reading '+group+'/Light',(position[0],position[1],position[2]+22),(p.x,p.y,p.z),100,200,12,12)
        arrange_waiting(u,state)
        return state,{'actors_added':len(state['new']),'originals_changed':len(state['originals']),
                      'private_materials':[m.get_path_name() for m in state['private']],'saved':False}
    except Exception:
        restore(u,state)
        raise


def restore(u,state):
    for c,materials in reversed(state['materials']):
        for i,m in enumerate(materials):c.set_material(i,m)
    for a,t,h,c in reversed(state['originals']):
        a.set_actor_transform(t,False,True);a.set_actor_hidden_in_game(h);a.set_actor_enable_collision(c)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in reversed(state['new']):sub.destroy_actor(a)


def arrange_waiting(u,state):
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    actors=list(sub.get_all_level_actors())
    def one(label):
        f=[a for a in actors if a.get_actor_label()==label];assert len(f)==1,label
        return f[0]
    def keep(a):
        if not any(v[0]==a for v in state['originals']) and a not in state['new']:
            state['originals'].append((a,a.get_actor_transform(),a.hidden,a.get_actor_enable_collision()))
        a.modify()
    for group,angle in (('NW',135),('SE',315)):
        r=math.radians(angle)
        table=one('Refine/CentralArchitecture97/Waiting '+group+'/Table')
        p,e=table.get_actor_bounds(False)
        target=u.Vector(4200+1060*math.cos(r),1060*math.sin(r),p.z)
        delta=target-p
        for a in actors:
            label=a.get_actor_label()
            if label.startswith('Refine/CentralArchitecture97/Waiting '+group+'/') and label.rsplit('/',1)[-1] in ('Table','Tablet','Reading','Water') or label.startswith(PREFIX+'Reading '+group+'/'):
                keep(a);a.set_actor_location(a.get_actor_location()+delta,False,True)
        for i,turn in enumerate((10,-10),1):
            a=one('Refine/CentralArchitecture97/Waiting '+group+'/Chair '+str(i));keep(a)
            r=math.radians(angle+turn);p,e=a.get_actor_bounds(False)
            pos=u.Vector(4200+1000*math.cos(r),1000*math.sin(r),p.z)
            rotation=u.MathLibrary.find_look_at_rotation(pos,target);rotation.pitch=0;rotation.yaw-=90
            a.set_actor_rotation(rotation,False);p,e=a.get_actor_bounds(False)
            a.set_actor_location(a.get_actor_location()+pos-p,False,True)
