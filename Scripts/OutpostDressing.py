"""Bounds-centered decorative composition for the asteroid outpost sandbox.

Units are centimetres. center is WORLD bounds center, size is LOCAL bounds size
BEFORE yaw. floor_z labels support surfaces only for independently grounded
objects. Shared-pivot assembly children MUST NOT be independently grounded.
No Unreal calls, primitive placeholders or source asset mutations occur here.
"""
from math import cos, radians, sin

P5 = '/Game/P1toP5_Bundle/P5_FruitSeller'
LANDMARKS = {
    'market_vendors': [[290,1535,0],[790,1700,0],[150,-1490,0],[285,-1490,0]],
    'market_shoppers': [[50,690,0],[700,690,0],[50,-1040,0],[460,-1040,0]],
    'lounge_conversation': [[3310,3410,0],[3540,3440,0]],
    'arcade_player': [3690,3940,0],
    'wardrobe_reserved': {'center':[4930,3800,0],'radius':500},
    'ops_conversation': [[7750,-180,0],[7940,-130,0]],
    'engineering_maintenance': [[3600,-3730,0],[4800,-3730,0]],
    'ops_briefing_display': [8970,0,180],
    'atrium_circulation': {'center':[4200,0,0],'clear_radius':850},
    'signs': [
        {'text':'AFTERBURN / ARCADE','center':[3700,4330,285],'yaw':0},
    ],
}


def build(catalog):
    """Return authored placement records. Missing static assets fail explicitly.

    Blueprint records use assembled individual FruitSeller props, not vendor
    example rooms. The caller measures native Blueprint component bounds before
    fitting them, provides collision, and checks appearance in the engine.
    """
    meshes = catalog['meshes'] if isinstance(catalog, dict) else catalog
    by_asset = {m['asset']:m for m in meshes}
    by_name = {}
    for m in meshes:
        if '/Horific/' not in m['asset']:
            by_name.setdefault(m['name'],m)
    result = []

    def get(asset):
        m = by_asset.get(asset) if asset.startswith('/Game/') else by_name.get(asset)
        if m is None:
            raise ValueError('Missing real outpost dressing mesh: '+asset)
        return m

    def rotate(v,yaw):
        a=radians(yaw)
        return [v[0]*cos(a)-v[1]*sin(a),v[0]*sin(a)+v[1]*cos(a),v[2]]

    def mesh(name,asset,x,y,floor=0,height=None,size=None,yaw=0,solid=True):
        m=get(asset)
        native=[2*v for v in m['extent']]
        if size is None:
            scale=height/native[2] if height is not None else 1.0
            size=[v*scale for v in native]
        row={'name':name,'asset':m['asset'],'center':[x,y,floor+size[2]/2],
             'size':list(size),'yaw':yaw,'solid':solid,'floor_z':floor,
             'expected_up':[0,0,1]}
        result.append(row)
        return row

    def bp(name,asset,x,y,height,floor=0,yaw=0,solid=True):
        result.append({'name':name,'asset':f'{P5}/Blueprints/{asset}.{asset}',
                       'kind':'blueprint','center':[x,y,floor+height/2],
                       'height':height,'yaw':yaw,'solid':solid,'floor_z':floor,
                       'expected_up':[0,0,1]})

    def assembly(name,parts,x,y,yaw=0,scale=1.0,floor=0):
        # Ground the UNION once. Child origin offsets remain unchanged.
        prepared=[]
        bottom=float('inf')
        for asset,offset,part_yaw in parts:
            m=get(asset)
            origin=rotate(m['origin'],part_yaw)
            center=[(origin[i]+offset[i])*scale for i in range(3)]
            size=[2*v*scale for v in m['extent']]
            bottom=min(bottom,center[2]-size[2]/2)
            prepared.append((m,center,size,part_yaw))
        for i,(m,center,size,part_yaw) in enumerate(prepared):
            center[2]+=floor-bottom
            center=rotate(center,yaw)
            result.append({'name':f'{name}_{i+1:02d}','asset':m['asset'],
                           'center':[center[0]+x,center[1]+y,center[2]],
                           'size':size,'yaw':yaw+part_yaw,
                           'solid':i==0 or 'Seat_V1_Part2' in m['name'],
                           'assembly':name,'assembly_floor_z':floor,
                           'expected_up':[0,0,1]})

    # Exact authored shared pivots, checked against BuildingSandbox scene.json.
    # Use the straight second terminal: all screen parts have yaw180, pitch0.
    chair=[(f'SM_TitaniumIndustrySeat_V1_Part{i}',(0,0,0),0) for i in (1,2,3)]
    console=[('SM_TitaniumIndustryStation_V1_Part1',(0,0,0),180),
             ('SM_TitaniumIndustryStation_V1_Part2',(0,-60,120),180),
             ('SM_SciFiScreen_V1_Part1',(0,20,150),180),
             ('SM_SciFiScreen_V1_Part2',(0,20,150),180),
             ('SM_SciFiScreen_V1_Part3',(0,20,150),180)]

    # Market uses complete vendor mini-kits in OutpostTechDisplays.py.
    # Keep this helper focused on social areas and engineering detail.

    # Four diagonal conversation pockets; cardinal entrances and atrium clear.
    for i,(x,y,yaw) in enumerate(((3200,920,-45),(5200,920,45),
                                  (3200,-920,-135),(5200,-920,135))):
        mesh(f'Atrium_Bench_{i}','SM_Bench_V1',x,y,height=65,yaw=yaw)
        bp(f'Atrium_Planter_{i}','BP_ISM_PlantBox_V1',
           x+(-160 if x<4200 else 160),y,120,yaw=yaw)

    # Arcade lounge with an open east wardrobe bay. Cabinet facing is a visual
    # check: facing_target makes the intended player approach explicit.
    for name,asset,x,height in (
        ('SpaceHunt','SM_Space_hunt_Arcade_Machine',3690,195),
        ('RetroConsole','SM_Sci_fi_Console_Game',3935,180)):
        row=mesh('Lounge_Arcade_'+name,asset,x,4220,height=height,yaw=180)
        row['facing_target']=[x,3800,height/2]
    for i,(x,y,yaw) in enumerate(((3330,3010,0),(3330,3570,180),
                                  (4910,2790,0),(5230,3050,90))):
        assembly(f'Lounge_Chair_{i}',chair,x,y,yaw=yaw,scale=.86)
    for i,(x,y) in enumerate(((3330,3260),(5020,3050))):
        mesh(f'Lounge_LowTable_{i}','SM_GoliathTable02',x,y,height=64)
        mesh(f'Lounge_GameProjector_{i}','SM_Props_ConstructionPart114',x,y,
             floor=64,height=12,solid=False)
        mesh(f'Lounge_GameHologram_{i}','SM_Props_ConstructionPart115',x,y,
             floor=76,height=26,solid=False)
    bp('Lounge_GardenWest','BP_ISM_PlantBox_V1',3030,4050,150)
    bp('Lounge_GardenEast','BP_ISM_PlantBox_V1',5300,4270,150)
    mesh('Lounge_ArcadeWaitingBench','SM_Bench_V1',3150,4200,height=65,yaw=180)

    # Four assembled terminals face the central briefing aisle. West door and
    # east display approach stay open; chair placement follows authored approach.
    for i,(x,y,yaw) in enumerate(((7230,920,0),(8200,920,0),
                                  (7230,-920,180),(8200,-920,180))):
        assembly(f'Ops_CommandConsole_{i}',console,x,y,yaw=yaw)
        delta=rotate((0,-225,0),yaw)
        assembly(f'Ops_OperatorChair_{i}',chair,x+delta[0],y+delta[1],yaw=yaw,scale=.9)
    for i,y in enumerate((-810,0,810)):
        bp(f'Ops_ArchiveStorage_{i}','BP_ISM_Storage_V1',8850,y,165,yaw=90)
    for i,(x,y) in enumerate(((6810,-1030),(6810,1030))):
        bp(f'Ops_Biofilter_{i}','BP_ISM_PlantBox_V1',x,y,145)
    for i,x in enumerate((7360,8060)):
        mesh(f'Ops_Casework_{i}','SM_Cabinet_B',x,1190,height=90)
        mesh(f'Ops_PowerCore_{i}','SM_Props_ConstructionPart115',x,1190,
             floor=95,height=55,solid=False)
    # Engineering is a working refit shop, not an empty room around a terminal.
    # The Goliath hub at (4200,-3850) remains the central visual/service focus.
    # Side diagnostics and repair benches face inward, with a broad direct aisle
    # from the north door and clear circulation around the central workstation.
    for i,(x,y,yaw) in enumerate(((3160,-3150,90),(5240,-3150,-90))):
        assembly(f'Engineering_Diagnostics_{i}',console,x,y,yaw=yaw)
        delta=rotate((0,-225,0),yaw)
        assembly(f'Engineering_DiagnosticChair_{i}',chair,x+delta[0],y+delta[1],
                 yaw=yaw,scale=.9)
    for i,x in enumerate((3200,5200)):
        mesh(f'Engineering_RepairBench_{i}','SM_Cabinet_A',x,-3730,
             size=(225,100,95),yaw=90)
        mesh(f'Engineering_PowerDock_{i}',
             'SM_Props_ConstructionPart35_S3000Serie_IonEnergyStabiliser',
             x,-3730,floor=95,height=45,yaw=90)
        mesh(f'Engineering_IonCore_{i}','SM_Props_ConstructionPart115',
             x,-3730,floor=140,height=35,solid=False)
    for i,x in enumerate((3150,3630,4800,5270)):
        bp(f'Engineering_SparesRack_{i}',
           'BP_ISM_S3000Series_1Bloc_V3' if i%2==0 else 'BP_ISM_Storage_V1',
           x,-4250,175,yaw=180)
    for i,(x,y,h) in enumerate(((3210,-3930,55),(3390,-3910,60),
                                (5200,-3940,66),(5010,-3930,48))):
        mesh(f'Engineering_ServiceCargo_{i}','SM_Props_Box03' if i%2==0 else 'SM_Props_Box04',
             x,y,height=h,yaw=(-8,12,5,-15)[i])
    for i,x in enumerate((3310,5150)):
        mesh(f'Engineering_WaitingBench_{i}','SM_Bench_V1',x,-2610,height=65,yaw=180)
    return result
