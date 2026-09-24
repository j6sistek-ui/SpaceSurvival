"""Offline regression of readability graph isolation; no Unreal installation used."""
import copy
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest

spec = importlib.util.spec_from_file_location('readability', Path(__file__).resolve().parents[1] / 'Scripts/OutpostReadability.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Object:
    def get_editor_property(self, name):
        return self.props[name]
    def set_editor_property(self, name, value):
        self.props[name] = value
    def get_name(self):
        return self.name
    def get_class(self):
        return NS(get_name=lambda: type(self).__name__)
    def get_path_name(self):
        return self.path + '.' + self.name


class Node(Object):
    def __init__(self, name, owner):
        self.name, self.owner = name, owner
        self.props = {'desc': '', 'default_value': 0.}
        self.inputs = []


class Multiply(Node):
    def __init__(self, name, owner):
        super().__init__(name, owner)
        self.inputs = [None, None]


class Scalar(Node):
    pass


class Material(Object):
    def __init__(self, path):
        self.path, self.name = path, path.rsplit('/', 1)[-1]
        self.props = dict(two_sided=True, blend_mode='masked', shading_model='unlit', opacity_mask_clip_value=.333)
        color, font = Node('NativeColor', self), Node('NativeFontAlpha', self)
        self.nodes = [color, font]
        self.links = {'emissive': (color, 'RGB'), 'opacity': (None, ''), 'mask': (font, 'A')}


class Component(Object):
    def __init__(self, material):
        self.props = {'text_material': material}
    def set_text_material(self, material):
        self.props['text_material'] = material


class TextActor:
    def __init__(self, name, material, authored=True):
        self.name, self.component = name, Component(material)
        self.tags = ['OutpostAuthored'] if authored else []
    def get_actor_label(self):
        return self.name
    def get_component_by_class(self, kind):
        return self.component


class Fixture:
    def __init__(self, root):
        self.root, self.package = Path(root), m.MAP
        source_file = self.root / 'EngineMaterials/UnlitText.uasset'
        source_file.parent.mkdir()
        source_file.write_bytes(b'unchanged-engine-font-and-alpha')
        self.assets = {m.SOURCE: Material(m.SOURCE), m.ONE_SIDED_SOURCE: Material(m.ONE_SIDED_SOURCE)}
        self.assets[m.ONE_SIDED_SOURCE].props['two_sided'] = False
        self.actors = [TextActor('Atrium/Heading', self.assets[m.SOURCE]),
                       TextActor('Observation/Arrival sign', self.assets[m.ONE_SIDED_SOURCE]),
                       TextActor('Not ours', self.assets[m.SOURCE], authored=False)]
        def duplicate(source, target):
            result = copy.deepcopy(self.assets[source])
            result.path, result.name = target, target.rsplit('/', 1)[-1]
            self.assets[target] = result
            return result
        def create(material, kind, x, y):
            node = kind('Added' + str(len(material.nodes)), material)
            material.nodes.append(node)
            return node
        def connect(source, output, target, input_name):
            target.inputs[0 if input_name == 'A' else 1] = source
            target.props['output_' + input_name] = output
            return True
        def connect_property(node, output, prop):
            node.owner.links[prop] = (node, output)
            return True
        edit = NS(get_material_expressions=lambda mat: mat.nodes,
                  get_inputs_for_material_expression=lambda mat, node: node.inputs,
                  get_material_property_input_node=lambda mat, prop: mat.links[prop][0],
                  get_material_property_input_node_output_name=lambda mat, prop: mat.links[prop][1],
                  create_material_expression=create, connect_material_expressions=connect,
                  connect_material_property=connect_property, recompile_material=lambda mat: None)
        u = NS(Material=Material, MaterialExpressionMultiply=Multiply,
               MaterialExpressionScalarParameter=Scalar, TextRenderActor=TextActor,
               TextRenderComponent=Component, UnrealEditorSubsystem=object,
               MaterialProperty=NS(MP_EMISSIVE_COLOR='emissive', MP_OPACITY='opacity', MP_OPACITY_MASK='mask'),
               Paths=NS(engine_content_dir=lambda: str(self.root), convert_relative_path_to_full=lambda p: p),
               get_editor_subsystem=lambda kind: NS(get_editor_world=lambda: NS(get_path_name=lambda: self.package + '.World')))
        self.api = dict(u=u, EAS=NS(get_all_level_actors=lambda: self.actors), EDIT=edit,
                        LIB=NS(does_asset_exist=lambda p: p in self.assets, duplicate_asset=duplicate,
                               save_loaded_asset=lambda a: True),
                        load=lambda p: self.assets[p], OUT=self.root, TARGET=m.MAP)


class ReadabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(self.temp.name)

    def test_preserves_font_alpha_source_and_unowned_text(self):
        report = m.apply(self.f.api)
        self.assertEqual(report['assigned_count'], 2)
        self.assertTrue(report['engine_source_unchanged'])
        self.assertEqual(len(self.f.assets[m.SOURCE].nodes), 2)
        self.assertIs(self.f.actors[2].component.props['text_material'], self.f.assets[m.SOURCE])
        for target in (m.TARGET, m.ONE_SIDED_TARGET):
            mat = self.f.assets[target]
            self.assertEqual(mat.links['mask'][0].name, 'NativeFontAlpha')
            self.assertEqual(mat.links['mask'][1], 'A')
            self.assertEqual(mat.links['emissive'][0].props['output_A'], 'RGB')
            self.assertEqual(len(mat.nodes), 4)
        self.assertFalse(self.f.assets[m.ONE_SIDED_TARGET].props['two_sided'])
        self.assertTrue(self.f.assets[m.TARGET].props['two_sided'])

    def test_repeat_reuses_nodes_and_gain_does_not_stack(self):
        m.apply(self.f.api)
        second = m.apply(self.f.api, gain=6.)
        third = m.apply(self.f.api, gain=6.)
        self.assertEqual(second['assigned_count'], 0)
        self.assertTrue(all(row['added_gain_nodes'] == 0 for row in second['materials']))
        self.assertTrue(all(not row['changed'] for row in third['materials']))
        for target in (m.TARGET, m.ONE_SIDED_TARGET):
            mat = self.f.assets[target]
            self.assertEqual(len(mat.nodes), 4)
            self.assertEqual(mat.links['emissive'][0].inputs[1].props['default_value'], 6.)

    def test_wrong_map_and_unknown_material_reject_before_mutation(self):
        self.f.package = '/Game/SpaceSurvival/Maps/Survival'
        with self.assertRaises(RuntimeError): m.apply(self.f.api)
        self.assertNotIn(m.TARGET, self.f.assets)
        self.f.package = m.MAP
        self.f.actors[0].component.props['text_material'] = Material('/Game/OwnerCustomSign')
        with self.assertRaises(RuntimeError): m.apply(self.f.api)
        self.assertNotIn(m.TARGET, self.f.assets)

    def test_corrupt_private_alpha_rejects_reapplication(self):
        m.apply(self.f.api)
        self.f.assets[m.TARGET].links['mask'] = (None, '')
        with self.assertRaises(RuntimeError): m.apply(self.f.api)
        self.assertEqual(len(self.f.assets[m.TARGET].nodes), 4)


if __name__ == '__main__':
    unittest.main()
