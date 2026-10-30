"""Remove tiny opposite-leg influences below the preserved Vexa hip junction.

Only vertices below0.90m, outside the central20mm strip, with >90percent of
their weight on their own leg and <=5percent on the opposite leg qualify.
Pelvis/glute/spine weights keep their exact value; removed weight is allocated
proportionally to existing own-leg influences. No new groups or topology.
"""
def isolate(scene):
    rows=[]
    is_leg=lambda name:name.startswith(('thigh','calf','foot','ball','toe'))
    for ob in scene.objects:
        if ob.type!='MESH' or ob.hide_render:continue
        for vertex in ob.data.vertices:
            point=ob.matrix_world@vertex.co
            if abs(point.x)<.01 or point.z>.90:continue
            side='l' if point.x>0 else 'r';other='r' if side=='l' else 'l'
            groups={ob.vertex_groups[g.group].name:g.weight for g in vertex.groups if g.weight>0}
            own={n:w for n,w in groups.items() if is_leg(n) and n.endswith('_'+side)}
            wrong={n:w for n,w in groups.items() if is_leg(n) and n.endswith('_'+other)}
            a=sum(own.values());b=sum(wrong.values())
            if not (a>.90 and 0<b<=.05):continue
            for name in wrong:ob.vertex_groups[name].remove([vertex.index])
            for name,weight in own.items():ob.vertex_groups[name].add([vertex.index],weight*(a+b)/a,'REPLACE')
            rows.append({'mesh':ob.name,'vertex':vertex.index,'rest':list(point),'removed':wrong,'before':groups})
    return rows
