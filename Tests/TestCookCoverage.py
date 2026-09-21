"""Cook exclusions must not hide missing runtime assets behind a broad cook root."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
from CheckCookCoverage import cook_rules, is_covered


class CookCoverageTests(unittest.TestCase):
    def setUp(self):
        self.rules = cook_rules((ROOT / "Config/DefaultGame.ini").read_text(encoding="utf-8"))

    def test_author_assets_are_excluded_despite_parent_cook_root(self):
        self.assertEqual(len(self.rules[2]), 6)
        for package in self.rules[2]:
            with self.subTest(package=package):
                self.assertFalse(is_covered(package + "." + package.rsplit("/", 1)[1], *self.rules))

    def test_runtime_nyxar_and_private_airbrake_remain_covered(self):
        for package in (
            "/Game/Nyxar/Meshes/SKM_Nyxar.SKM_Nyxar",
            "/Game/Nyxar/Meshes/SKEL_Nyxar",
            "/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew/MI_NyxarCrew_Teal",
            "/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew/Anims/A_Alien_MOB1_Walk_F_Loop_IPC",
            "/Game/SpaceSurvival/Licensed/PhoenixPresentation/AirBrake",
            "/Game/Stellar_Phoenix/Spaceship/Animation/Landing_On",
        ):
            with self.subTest(package=package):
                self.assertTrue(is_covered(package, *self.rules))

    def test_directory_exclusion_wins(self):
        self.assertFalse(is_covered("/Game/SpaceSurvival/Licensed/MocapSource/IK_UE4Mannequin", *self.rules))

    def test_plugin_runtime_light_mask_is_explicitly_cooked(self):
        # The installed plugin's UWPPortalLightTransmissionSubsystem loads this literal
        # at game-world initialization; scanning our own /Game/ strings cannot discover it.
        folder = "/WormholePortal/WormholePortal/Materials/LightFunctions"
        material = folder + "/M_WPPortalSphericalGate.M_WPPortalSphericalGate"
        self.assertIn(folder, self.rules[0])
        self.assertTrue(is_covered(material, *self.rules))
        without_mask = [root for root in self.rules[0] if root != folder]
        self.assertFalse(is_covered(material, without_mask, self.rules[1], self.rules[2]))

    def test_package_boundary_and_case(self):
        roots = ["/Game/Runtime"]
        self.assertTrue(is_covered("/game/runtime/Clip.Clip", roots, [], set()))
        self.assertFalse(is_covered("/Game/RuntimeOther/Clip", roots, [], set()))
        self.assertFalse(is_covered("/game/runtime/Clip.Clip", roots, [], {"/Game/Runtime/Clip"}))
        self.assertTrue(is_covered("/Game/Runtime/ClipOther", roots, [], {"/Game/Runtime/Clip"}))

    def test_unmodelled_recursive_exclusion_fails_closed(self):
        with self.assertRaises(ValueError):
            cook_rules('+PrimaryAssetTypesToScan=(SpecificAssets=("/Game/A.A"),Rules=(bApplyRecursively=True,CookRule=NeverCook))')


if __name__ == "__main__":
    unittest.main()
