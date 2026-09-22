"""Portable geometric guards for the station recipe, independent of Unreal render acceptance."""
import importlib.util
import math
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "station_reset", Path(__file__).resolve().parents[1] / "Scripts/AuthorStationReset.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StationResetRecipe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Deliberately asymmetric, non-origin pivots exercise the authored placement calculation.
        cls.recipe, cls.placements, cls.assets = MODULE.build_recipe(
            lambda asset: dict(origin=[31.0, -79.0, 48.0], extent=[64.0, 153.0, 87.0], materials=["/Test/Material"]))

    def test_measured_mesh_centers_and_surfaces_match_specs(self):
        for mesh, placement in zip(self.recipe["static_meshes"], self.placements):
            measured = self.assets[mesh["asset"]]
            local = [measured["origin"][i] * mesh["scale"][i] for i in range(3)]
            rotated = MODULE.rotated_vector(local, mesh["rotation"])
            for axis in range(3):
                self.assertAlmostEqual(mesh["location"][axis] + rotated[axis], placement["center"][axis], places=6,
                                       msg=mesh["name"])
            if mesh["name"].startswith("Deck_"):
                self.assertAlmostEqual(placement["center"][2] + placement["size"][2] / 2, -10)
        foundation = next(p for p in self.placements if p["name"] == "Foundation")
        self.assertLess(foundation["center"][2] + foundation["size"][2] / 2, -32,
                        "Foundation must not z-fight with the visible deck")

    def test_service_approaches_are_supported_and_outside_solids(self):
        kinds = {a["service"] for a in self.recipe["service_anchors"]}
        self.assertEqual(kinds, {"Wardrobe", "Paint", "Repair", "Loadout", "Launch", "Contracts", "Systems",
                                "Modules", "Gallery", "Beacon"})
        for anchor in self.recipe["service_anchors"]:
            x, y, z = anchor["location"]
            self.assertTrue(-1858 <= x <= 2058 and -1458 <= y <= 1458, anchor["name"])
            self.assertEqual(z, -10)
            # Conservative upright capsule bounds: an interaction point must fit a 42cm-radius walker.
            for solid in self.recipe["collision_boxes"]:
                if solid.get("walk_floor"):
                    continue
                cx, cy, cz = solid["location"]
                ex, ey, ez = solid["extent"]
                overlaps = abs(x - cx) < ex + 42 and abs(y - cy) < ey + 42 and cz + ez > z + 2.5 and cz - ez < z + 195
                self.assertFalse(overlaps, (anchor["name"], solid["name"]))

    def test_entry_and_central_aisle_are_unobstructed(self):
        for solid in self.recipe["collision_boxes"]:
            if solid.get("walk_floor"):
                continue
            x, y, z = solid["location"]
            ex, ey, ez = solid["extent"]
            in_aisle = x + ex > -1900 and x - ex < 1600 and y + ey > -400 and y - ey < 400
            in_walker_height = z + ez > -7.5 and z - ez < 185
            self.assertFalse(in_aisle and in_walker_height, solid["name"])

    def test_visual_solids_have_matching_explicit_colliders(self):
        by_name = {b["name"]: b for b in self.recipe["collision_boxes"]}
        meshes = {m["name"]: m for m in self.recipe["static_meshes"]}
        for p in self.placements:
            if p["solid"]:
                if meshes[p["name"]].get("triangle_collision"):
                    self.assertEqual(p["name"], "AsteroidHabitat")
                    self.assertEqual(meshes[p["name"]]["asset"], MODULE.ASTEROID)
                    self.assertNotIn("Collision_" + p["name"], by_name,
                                     "A solid bounding box would seal the asteroid's real cavity")
                    continue
                collider = by_name["Collision_" + p["name"]]
                self.assertEqual(collider["location"], p["center"])
                self.assertEqual([v * 2 for v in collider["extent"]], p["size"])

    def test_asteroid_is_private_uniform_and_uses_its_triangle_surface(self):
        asteroid = next(m for m in self.recipe["static_meshes"] if m["name"] == "AsteroidHabitat")
        self.assertEqual(asteroid["asset"], "/Game/SpaceSurvival/Licensed/StationReset/SM_StationAsteroid")
        self.assertEqual(asteroid["scale"], [145, 145, 145])
        self.assertTrue(asteroid.get("triangle_collision"))
        self.assertEqual([m["name"] for m in self.recipe["static_meshes"] if m.get("triangle_collision")],
                         ["AsteroidHabitat"], "Only the reviewed private asteroid uses triangle collision")
        self.assertFalse(any("Asteroid" in b["name"] for b in self.recipe["collision_boxes"]))
        direction = MODULE.rotated_vector([-.76475, -.31190, .56381], asteroid["rotation"])
        self.assertAlmostEqual(direction[0], -1, places=4)
        self.assertAlmostEqual(direction[1], 0, places=4)
        self.assertAlmostEqual(direction[2], 0, places=4)

    def test_control_consoles_keep_the_authored_display_transform(self):
        meshes = {m["name"]: m for m in self.recipe["static_meshes"]}
        self.assertFalse(any("Info_Terminal" in m["asset"] for m in meshes.values()),
                         "The rejected glowing light sculpture is not a usable control-console asset")
        for anchor in self.recipe["service_anchors"]:
            kind = anchor["service"]
            body, display = meshes["Console_" + kind], meshes["ConsoleDisplay_" + kind]
            self.assertEqual(body["asset"], MODULE.TERMINAL)
            self.assertEqual(display["asset"], MODULE.TERMINAL_UI)
            for key in ("location", "rotation", "scale"):
                self.assertEqual(display[key], body[key],
                                 "Re-fitting the offset UI bounds would detach the display from its console")
            self.assertAlmostEqual(body["scale"][0], body["scale"][1])
            self.assertAlmostEqual(body["scale"][1], body["scale"][2])

    def test_staff_standing_bodies_clear_the_service_bay_structure(self):
        for body in self.recipe["collision_capsules"]:
            x, y, z = body["location"]
            radius, half_height = body["radius"], body["half_height"]
            self.assertAlmostEqual(z - half_height, MODULE.FLOOR_Z)
            for solid in self.recipe["collision_boxes"]:
                if solid.get("walk_floor"):
                    continue
                cx, cy, cz = solid["location"]
                ex, ey, ez = solid["extent"]
                overlaps = (abs(x - cx) < ex + radius and abs(y - cy) < ey + radius and
                            abs(z - cz) < ez + half_height)
                self.assertFalse(overlaps, (body["name"], solid["name"]))

    def test_habitats_fit_the_measured_terraces_with_uniform_scale(self):
        meshes = {m["name"]: m for m in self.recipe["static_meshes"]}
        habitats = [p for p in self.placements if p["name"].startswith("ColonyHabitat_")]
        self.assertEqual(len(habitats), 2)
        self.assertFalse(any("Ultimate_Space_Colony_Outpost_Pack" in m["asset"] for m in meshes.values()),
                         "Cycle1 equipment cases must not silently return as substitute colony buildings")
        for habitat in habitats:
            mesh = meshes[habitat["name"]]
            self.assertEqual(mesh["asset"], MODULE.COLONY_HABITAT)
            self.assertEqual(len(set(mesh["scale"])), 1)
            self.assertAlmostEqual(habitat["center"][2] - habitat["size"][2] / 2, 750)
            self.assertLessEqual(max(habitat["size"][:2]), 1800.000001)
            self.assertLessEqual(habitat["size"][2], 4500)


if __name__ == "__main__":
    unittest.main()
