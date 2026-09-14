# Proposed PR #6 metadata update

Title: Refresh flight environment, assets and feedback for tester review

This refresh fixes clipped rear-flight framing, integrates licensed asteroid/station assets and an industrial exterior, and retains the optional Ludo ship trial. Depot, combat-feedback and hero-animation repairs remain included. Raw licensed assets are excluded from Git.

The current environment combines an owned cool nebula cubemap, ambient sky lighting, thin vendor-graph local dust volumes, four asteroid depth/size bands with bounded parallax, and private blue-white Niagara ribbons. A presentation Data Asset supplies the editable look. Early-wave hazard admission, progression and station cadence are unchanged. Final packaged 1080p captures show no recurrence of the earlier opaque cloud rectangle; the historical custom material's root cause is not claimed solved.

Validation: 44 Unreal tests passed with zero test warnings/failures/not-run, 27 source checks, native formatting and Python/source-asset checks passed. Editor compilation and Windows BuildCookRun succeeded. The 29-second normal-stat scripted packaged Wave1 capture verifies cruise/turn/boost/brake screenshots, package hashes and preserved production saves. docs/validation/2026-09-14-combined-space-look.json binds exact source hashes and artifacts. Offscreen visual captures are not natural gameplay, physical-input, audio, continuous-motion quality or representative 60 FPS acceptance.

Known gaps include uniform blue rock illumination, thin exhaust/nozzle fit, simple dust grains, bounded rather than infinite parallax, and existing station-exterior Nanite-usage fallback warnings. Phase1 remains PARTIAL. docs/production/COMBINED_SPACE_LOOK.md records tuning/build instructions; the five owner-supplied Fab candidates are assessed separately with no purchases.

PR8 guidance and main's planning/feedback are incorporated through the PR3 conflict repair. The newer combined look is in the local Windows archive only. Itch remains 0.1.15-alpha/build1978147 from source602be07; its devlog awaits authentication. This PR remains unmerged; publication and implementation do not establish owner acceptance.
