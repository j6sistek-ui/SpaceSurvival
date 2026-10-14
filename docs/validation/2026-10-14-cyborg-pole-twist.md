# Cyborg custom pole animation repair — October 14

RPT-20261014-01. Six private pole clips repaired and adopted locally. Broader Cyborg
acceptance remains open; this is not a packaged release or a general skinning fix.

## Cause and bounded change

The owner confirmed these clips are custom procedural animations, not vendor pack
content. The existing `Scripts/TripoCrewBlender/pole/pole_dance.py` is their source.
Cyan's failure under the same clips was evidence against continuing broad mesh edits.
Native evaluation found repeated abrupt arm rotations in the current pole clips.
The later contact adaptation retained old arm roll while changing the elbow plane.

The repair reconstructs arm rotation from a continuous anatomical elbow target,
allows bounded clavicle elevation within arm reach, and limits the gripping wrist's
combined turn to about 60 degrees. The wrist can move while the same palm anchor
stays on the pole. Existing forearm helper weights distribute the repaired roll.
Spin's previously distorted left arm is now a relaxed free arm with a reduced finger
curl; it no longer reaches into the head. Spin/Kick remain one-shot source motions.

Only arm/finger animation tracks in these six private assets were written:
`/Game/SpaceSurvival/Licensed/CyborgRefresh_20261014/Animations/A_Cyborg_Pole{Idle,HipCircle,BodyWave,BackSlide,Spin,Kick}`.
The refreshed mesh, weights, UVs, materials, accepted chest, skeleton, original Cyborg
and Cyan assets, and saved Wayfarer map were preserved. No animation was removed.

## Native evidence

754 evaluated keys across all six clips, before and after:

| Clip | Largest arm rotation between keys before | After | Corrected steps over 20 degrees |
| --- | ---: | ---: | ---: |
| Idle |42.26°|1.48°|0|
| HipCircle |43.78°|2.15°|0|
| BodyWave |41.55°|3.76°|0|
| BackSlide |13.94°|6.11°|0|
| Spin |43.06°|4.28°|0|
| Kick |43.66°|8.17°|0|

The maximum right palm anchor change is .000131cm. This is numerical agreement,
not a claim that every fingertip has perfect surface contact. Head, pelvis and feet
positions are unchanged at every sampled key. The four looping clips' arm endpoint
gaps are .19/.34/2.63/.08 degrees, all below their previous gaps. Wrist/hand movement
is intentional; an unchanged wrist position would have preserved the bad grip angle.

36 native matched-phase clay frames were captured; all 18 candidate poses and
selected matched comparisons were visually reviewed. Normal-speed playback of all
six clips records 2,644 finite transform samples and 30 pole-view images.
The large collapse/twist is reduced in the reviewed shoulders and forearms. Subtle
shoulder creasing and the existing surface/shape limitations are not certified away.

After saving, the task-owned editor was closed and restarted. All 754 production clip
poses exactly match the verified native candidate data. Ordinary 1600x900 station
near/body screenshots show the corrected arm and detailed textures without forced
texture residency. 159 other skeletal components were hidden only in PIE to remove
occlusion; this is not a full-cast performance or natural-play test. The actual
station Blueprint's six-clip playback passed with 754 finite dynamics samples and
82 captured frames. The two breast regions peaked at 1.548/1.394 cm, within the
existing 1.6 cm limit; both corrective weights stayed finite in [0,1]. Representative
HipCircle, BackSlide, Spin and Kick station frames were visually reviewed. The
compatible waiting-pose fixture also retained a valid dynamics binding.

The final guard verifies all six adopted clip hashes and five protected asset hashes.
The station map at this repair's baseline and finish is SHA256
`b6c39471a8b20613984ed85d00e39e13e661c8367c4f68ebbd3ae678cd591971`.
The older `362e7409` map receipt belongs to the earlier adoption checkpoint; this
repair did not rewrite the later map. PIE stopped, the temporary stage was discarded
without saving, the viewport was restored and the task-owned editor exited.

## Rejected attempts and reproducibility

Fractional quaternion roll crossed the 180-degree branch and produced flips. Full
unbounded distal roll collapsed the forearm. Smoothing upper/lower arm world rotation
independently of joint position moved the native grip because Skeleton translation
retargeting ignores authored local offsets. Those candidates were rejected. The
final solver keeps bone axes consistent with positions and filters only helper
orientation. Limiting the wrist and replacing the unstable elbow hint removes the
high-frequency source jumps without changing mesh weights.

`Scripts/TripoCrewBlender/pole/repair_twist.py` and `twist_pose_solver.py` reproduce
the final tracks using the installed Blender runtime. The immutable input is
`BaselineKeys.json` plus the accepted `Cyborg_CHEST_REVIEW.blend`; neither is modified.
A second run of the committed recipe produces byte-identical tracks, poses and report.
`Scripts/ApplyCyborgPoleTwist.py` defaults to dry-run, verifies the six source hashes
and native review receipts, backs up before writing, and rejects replay after adoption.
It does not change a map, skeleton, mesh, material, or source/vendor animation.

Private evidence root in the canonical checkout:
`.agent/local/CyborgRepair_20261013/TwistRepair/`.
Key files: `Compare.html`, `MotionAudit.json`, `NativeVerification.json`,
`Native/Capture.json`, `Playback/Playback.json`, `Adopted.json`,
`BeforeAdoption/*.uasset`, `ReloadVerification.json`, `FullView.json`,
`FullViewNear.png`, `FullViewBody.png`, `StationPlayback/Playback.json`,
`Reproduction.json`, and `Finish.json`.
Native binaries and private input data remain local; this PR contains the recipes
and concise evidence, not a new distributable game build.

## Source checks

42 source structural checks, Python `compileall`, content-source validation
(26 meshes / 17 WAVs), documentation navigation and `git diff --check` pass.
The final recipe was rerun in Blender 5.2.2; all three generated outputs remain
byte-identical. This checkpoint changes Python recipes and documentation only.
The previously built Editor module `02e07c22` was used for the fresh native checks;
no C++ change requires another build. Existing build/toolchain warnings and the
earlier rejected visual claims remain recorded in the preceding repair receipt.

## Limits and next review

This repair addresses the six custom pole clips. It does not establish anatomical
quality for every non-pole vendor animation, all extreme shoulder poses, natural
input/gameplay, representative performance, or owner acceptance. Silver's requested
pink ponytail/outfit work remains untouched pending the broader Cyborg gate.
Review the same-clip before/after and the actual station closeup, rather than assuming
an animation or import passed because its transforms are finite.

This receipt ends at 12:35 UTC. The owner then advised another source is uploading
a fix that may occupy Unreal. The task-owned editor was already closed; no further
native writes were made. That later update needs its own comparison and validation.
