"""CPU regression checks for backup fidelity and unsafe native profile rejection."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

script = Path(__file__).resolve().parents[1]/'Scripts/StationReviewProfile.py'
if not script.exists():
    script = Path(__file__).with_name('StationReviewProfile.py')
spec = importlib.util.spec_from_file_location('review_profile',script)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='StationReviewCPU-',
                                              dir=Path(__file__).parent)
        self.base = Path(self.tmp.name)
        self.repo = self.base/'SpaceSurvival'
        self.live = self.repo/'Saved/SaveGames'
        self.live.mkdir(parents=True)
        (self.repo/'SpaceSurvival.uproject').write_text('{}')
        self.payload = b'non-text\x00save\xffbytes'
        (self.live/'SS_Settings_v1.sav').write_bytes(self.payload)
        self.app = self.base/'AppData'
        self.run = review.prepare(self.repo,self.app)
        self.user = self.run/'User'
        self.command = ('-RenderOffscreen -SaveToUserDir -SSStationReviewRoot="'+
                        self.run.as_posix()+'" -UserDir="'+self.user.as_posix()+'"')
        self.world = None
        self.paths = SimpleNamespace(convert_relative_path_to_full=lambda p:p,
            project_dir=lambda:str(self.repo), project_user_dir=lambda:str(self.user),
            project_saved_dir=lambda:str(self.user/'Saved'))
        self.engine = SimpleNamespace(Paths=self.paths,
            SystemLibrary=SimpleNamespace(get_command_line=lambda:self.command),
            UnrealEditorSubsystem=object,
            get_editor_subsystem=lambda c:SimpleNamespace(get_game_world=lambda:self.world))
        self.previous = sys.modules.get('unreal')
        sys.modules['unreal'] = self.engine

    def tearDown(self):
        if self.previous is None:sys.modules.pop('unreal',None)
        else:sys.modules['unreal']=self.previous
        self.tmp.cleanup()

    def test_exact_byte_backup_and_independent_review_writes(self):
        self.assertEqual((self.run/'Backups/0/SS_Settings_v1.sav').read_bytes(),self.payload)
        clone=self.user/'Saved/SaveGames/SS_Settings_v1.sav'
        self.assertEqual(clone.read_bytes(),self.payload)
        clone.write_bytes(b'review changed settings')
        self.assertEqual((self.live/'SS_Settings_v1.sav').read_bytes(),self.payload)

    def test_successful_fake_native_paths_can_be_rechecked(self):
        self.assertTrue(review.verify_before_play()['ready_for_play'])
        self.assertTrue(review.verify_before_play()['production_unchanged'])
        self.assertEqual(len(list(self.run.glob('NativeBeforePlay-*.json'))),2)

    def test_live_save_path_is_rejected(self):
        self.paths.project_saved_dir=lambda:str(self.repo/'Saved')
        with self.assertRaisesRegex(RuntimeError,'not isolated'):review.verify_before_play()

    def test_current_owner_process_flags_are_rejected(self):
        self.command='-SaveToUserDir'
        with self.assertRaisesRegex(RuntimeError,'RenderOffscreen'):review.verify_before_play()

    def test_changed_or_new_production_slot_is_rejected(self):
        (self.live/'NewSlot.sav').write_bytes(b'new')
        with self.assertRaisesRegex(RuntimeError,'changed since'):review.verify_before_play()

    def test_existing_play_is_rejected(self):
        self.world=object()
        with self.assertRaisesRegex(RuntimeError,'before GameInstance'):review.verify_before_play()

    def test_marker_tampering_is_rejected(self):
        (self.run/'.ss-station-review').write_text('other')
        with self.assertRaisesRegex(RuntimeError,'marker mismatch'):review.verify_before_play()

    def test_redirected_save_tree_is_rejected(self):
        link=self.repo/'redirected'
        try:link.symlink_to(self.live,target_is_directory=True)
        except OSError:self.skipTest('Host does not allow unprivileged symlink creation')
        with self.assertRaisesRegex(RuntimeError,'Redirected'):review.direct(link/'slot.sav')

    def test_windows_junction_attribute_is_rejected(self):
        # Exercise the Windows reparse guard even without symlink privileges.
        info=SimpleNamespace(st_mode=0o040755,st_file_attributes=0x400)
        with patch.object(Path,'lstat',return_value=info):
            with self.assertRaisesRegex(RuntimeError,'Redirected'):review.direct(self.live)


if __name__=='__main__':unittest.main()
