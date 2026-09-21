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
        for p in self.placements:
            if p["solid"]:
                collider = by_name["Collision_" + p["name"]]
                self.assertEqual(collider["location"], p["center"])
                self.assertEqual([v * 2 for v in collider["extent"]], p["size"])

    def test_asteroid_is_private_uniform_and_excluded_from_walk_collision(self):
        asteroid = next(m for m in self.recipe["static_meshes"] if m["name"] == "AsteroidHabitat")
        self.assertEqual(asteroid["asset"], "/Game/SpaceSurvival/Licensed/StationReset/SM_StationAsteroid")
        self.assertEqual(asteroid["scale"], [145, 145, 145])
        self.assertFalse(any("Asteroid" in b["name"] for b in self.recipe["collision_boxes"]))
        direction = MODULE.rotated_vector([-.76475, -.31190, .56381], asteroid["rotation"])
        self.assertAlmostEqual(direction[0], -1, places=4)
        self.assertAlmostEqual(direction[1], 0, places=4)
        self.assertAlmostEqual(direction[2], 0, places=4)


if __name__ == "__main__":
    unittest.main()
