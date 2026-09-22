# September22 arcade flight baseline

Owner approved left-stick nose steering, right-stick camera, bumper tap sideways dash/bank and hold fast roll. Acceleration/steering/response increased; ordinary cruise remains60m/s and engine-off coasting remains. Asteroid launch-only belt replaced by deterministic800m cells:2048 rocks in15 shared batches,125 resident cells,1.4km draw distance, stable nearby instances, exact regeneration on revisit, solid physics/shot collision. Director budget/difficulty and orange3x hazards unchanged.

Editor builds1/2 passed. Focused1: ControllerToPhysics, DistantAsteroidIsolation and MenuBackBoostRelease pass; ControllerTestingPreset initially failed because vendor roll shaping attenuated the authored rate. Adapter now sets roll multiplier1; Focused2 passes that case. First failure retained under Artifacts/ArcadeResponse. The test observes actual physics movement, tap bank/return, sustained roll, camera independence,9km world travel/all six directions, reachable shot collision, deterministic revisit and rebasing. Synthetic input is not physical-controller feel acceptance.

Owner defers character work. Read-only light review found combined squirrel50508vertices/1section, segmented110734vertices/9sections, neither with tail bones; no rig, selection or deletion performed. Caped character remains reserved. Owner map actor-removal edit is retained in this baseline.

Package, bounded rendered flight check and authorized itch publication: pending. No full-suite rerun, natural ten-wave acceptance, listening or representative performance claim. Earlier GPU-memory warnings and boarding/art/animation follow-ups remain open in KNOWN_ISSUES.
