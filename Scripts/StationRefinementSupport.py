"""Bounded placed-actor authoring helpers; no map loading, saving or source mutations.

Only the explicitly invoked owner-preview author script owns the transaction.
Grounding uses native component geometry, including actual ISM instances.
"""
import unreal as u
from OutpostGeometryUtils import mesh_union, inherit_parent_scale_preserving_world


def vector(value):
    return value if isinstance(value, u.Vector) else u.Vector(*value)


def transform_record(actor):
    t = actor.get_actor_transform()
    return {'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
            'location': list(t.translation.to_tuple()),
            'rotation': list(t.rotation.to_tuple()), 'scale': list(t.scale3d.to_tuple()),
            'hidden': bool(actor.get_editor_property('hidden')),
            'editor_hidden': actor.is_temporarily_hidden_in_editor()}


class Context:
    def __init__(self):
        self.eas = u.get_editor_subsystem(u.EditorActorSubsystem)
        self.actors = list(self.eas.get_all_level_actors())
        self.created = []
        self.records = []
        self.assets = {}

    def asset(self, path):
        if not isinstance(path, str):
            return path
        if path not in self.assets:
            self.assets[path] = u.load_asset(path)
            if not self.assets[path]:
                raise RuntimeError('Missing existing asset: ' + path)
        return self.assets[path]

    def register(self, actor, label):
        label = label if label.startswith('Refine/') else 'Refine/' + label
        actor.set_actor_label(label)
        actor.set_folder_path(label.rsplit('/', 1)[0])
        actor.tags = list(actor.tags) + ['StationRefinement20261006', 'OutpostLabel:' + label]
        self.created.append(actor)
        return actor

    def raw(self, label, asset, loc, rot=(0, 0, 0), scale=(1, 1, 1), collision=True):
        obj = self.asset(asset)
        rotation = rot if isinstance(rot, u.Rotator) else u.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2])
        if isinstance(obj, u.StaticMesh):
            actor = self.eas.spawn_actor_from_class(u.StaticMeshActor, vector(loc), rotation)
            actor.static_mesh_component.set_static_mesh(obj)
        else:
            cls = obj.generated_class() if isinstance(obj, u.Blueprint) else obj
            actor = self.eas.spawn_actor_from_class(cls, vector(loc), rotation)
            if not actor:
                raise RuntimeError('Could not place ' + str(asset))
            if any(c.static_mesh for c in actor.get_components_by_class(u.StaticMeshComponent)):
                inherit_parent_scale_preserving_world(actor)
        actor.set_actor_scale3d(vector(scale))
        actor.set_actor_enable_collision(collision)
        return self.register(actor, label)

    def grounded(self, label, asset, xy, floor=0, yaw=0, scale=(1, 1, 1), collision=True):
        actor = self.raw(label, asset, (xy[0], xy[1], floor), (0, yaw, 0), scale, collision)
        center, extent = mesh_union(actor)
        actor.set_actor_location(actor.get_actor_location() + u.Vector(
            xy[0] - center.x, xy[1] - center.y, floor - center.z + extent.z), False, False)
        center, extent = mesh_union(actor)
        if abs(center.z - extent.z - floor) > .05:
            raise RuntimeError('Grounding failed: ' + label)
        self.records.append({'kind': 'grounded', 'label': label,
                             'center': list(center.to_tuple()), 'extent': list(extent.to_tuple()),
                             'floor': floor})
        return actor

    def box(self, label, center, size, material, collision=True):
        actor = self.raw(label, '/Engine/BasicShapes/Cube.Cube', center,
                         scale=tuple(v / 100.0 for v in size), collision=collision)
        actor.static_mesh_component.set_material(0, self.asset(material))
        return actor

    def hide(self, actor):
        self.records.append({'kind': 'hide', 'before': transform_record(actor)})
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.set_actor_enable_collision(False)
        for component in actor.get_components_by_class(u.PrimitiveComponent):
            component.set_visibility(False)
            component.set_hidden_in_game(True)
        # Hidden rendered lamps must not keep contributing to the room lighting.
        for light in actor.get_components_by_class(u.LightComponent):
            light.set_visibility(False)
        actor.tags = list(actor.tags) + ['StationRefinementRetired']

    def move(self, actor, location, rotation=None):
        self.records.append({'kind': 'move', 'before': transform_record(actor)})
        actor.set_actor_location(vector(location), False, False)
        if rotation is not None:
            actor.set_actor_rotation(rotation if isinstance(rotation, u.Rotator)
                                     else u.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), False)
        return actor

    def text(self, label, content, location, yaw, size=24, color=(.65, .85, 1)):
        actor = self.eas.spawn_actor_from_class(u.TextRenderActor, vector(location), u.Rotator(pitch=0, yaw=yaw, roll=0))
        component = actor.get_component_by_class(u.TextRenderComponent)
        component.set_text(content.replace('\n', '<br>'))
        component.set_world_size(size)
        component.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
        component.set_vertical_alignment(u.VerticalTextAligment.EVRTA_TEXT_CENTER)
        component.set_text_render_color(u.Color(*[int(max(0, min(1, c)) * 255) for c in color], 255))
        actor.set_actor_enable_collision(False)
        return self.register(actor, label)

    def light(self, label, location, intensity, radius, color=(.7, .85, 1), shadows=False):
        actor = self.eas.spawn_actor_from_class(u.PointLight, vector(location))
        component = actor.get_component_by_class(u.PointLightComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(intensity)
        component.set_attenuation_radius(radius)
        component.set_light_color(u.LinearColor(*color, 1))
        component.set_cast_shadows(shadows)
        return self.register(actor, label)

    def summary(self):
        return {'created': [transform_record(a) for a in self.created], 'changes': self.records}
