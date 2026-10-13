# Silver hair coverage diagnosis — 2026-10-13

Related issue: RPT-20261013-01. State: defect reproduced in saved evidence; repair and native visual validation pending.

The owner rejected the sides in the dance GIF as bald-looking. This is separate from acceptable temporary hair crossing the face. Color choices are left to the owner; no color adjustment was made.

Read-only inspection of the retained master confirms that `BackHairVisible` hides all 3,535 strands in `BlondeGroom_4.sides right` and all 1,212 in `BlondeGroom_4.top right`. The retained Alembic export contains zero strands in those sections. Only 183 and 240 strands remain in the two exported left-side sections. Live native readback confirms 12,298 strands overall, no curve decimation and no local transform offset. Missing side source geometry is a confirmed defect; this does not prove it is the only contributor to the final appearance.

`build_hair_physics.py` originally selected complete strands by tip position (`tip.y > .025 or tip.z > 1.72`) to keep hair behind the back. This removed scalp coverage along with front-falling tips. Later contact filtering further thinned the groom. The original strand data remains in the master, so rebuilding it from scratch is unnecessary. Do not restore all front-falling strands blindly: retain the root/temple coverage and reroute the loose lengths, then compare the same close view and dance with collision active.

The other integration lead was actively editing the station in its private offscreen editor. This diagnosis changed no Blender source, cache, native material, groom, Blueprint or map and did not interrupt that session. No repaired GIF or accepted hair result is claimed. Local evidence: `work/Unreal/HairCoverage_SourceSections.json`, `HairCoverage_Width.json`, `HairCoverage_Read.response.json` and the retained export manifest.

The remaining scoped character files measure 3,001,998,411 bytes (about 3.0 GB): M source/recovery 2,322,158,552; C working files 413,364,592; scratch 85,237; native assets 212,188,258; Downloads originals 54,201,772. This is the retained character pipeline, not the whole game or vendor libraries. Small diagnostic text files added afterward do not materially change those rounded totals. Keep the four original GLBs in Downloads unless relocating them to a verified source archive.
