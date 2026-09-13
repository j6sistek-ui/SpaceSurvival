# Utility tuning bridge

**Status: domain and actual Unreal automation passed; custom-price native vendor acceptance remains pending.** This is a bounded Phase 1 change. It adds no utilities, slots, inventory or save fields.

`DA_Phase1.Utilities` contains the existing Vector Thrusters and Overdrive Cooling definitions. Identities are read-only and the roster has two entries. GameMode maps their validated prices/effect magnitudes into `SS::Tuning`; domain stat composition, purchase eligibility/payment and vendor labels use those values.

| Utility | Default price | Existing effect defaults |
| --- | ---: | --- |
| Vector Thrusters | 150 | Maneuver x1.30; response x1.12 |
| Overdrive Cooling | 150 | Boost efficiency x1.35; cooling efficiency x1.45 |

Edit only the relevant numeric fields on the asset. Values are applied when GameMode initializes. Suspensions retain the utility identity and use the loaded game's tuning, as other existing tuning does; there is no per-save content snapshot. Free event fitting, one-slot replacement and rejecting a repeated fitted purchase are unchanged.

Runtime accepts either row order and canonicalizes identity. Missing, extra, duplicate or unknown entries restore both defaults. A nonpositive price, nonfinite multiplier or multiplier below one restores that row's defaults. Finite high values clamp to price 100,000,000 or multiplier 3 and report invalid content. Authoring and fresh persisted validation reject corrected/malformed values so runtime fallback does not silently become authored content.

After the editor rebuild, run the normal Content and Validate targets. Existing authored values are preserved while new fields are saved. A focused Unreal test uses real reflected Data Assets with non-default values and the same mapping used by GameMode; it also checks malformed definitions without GameInstance initialization or save writes.

The container run passed **593 strict and 593 ASan/UBSan assertions**. Exact compiled input hashes match the test image and the retained raw log. Owned C++ formatting, 20 structural checks, Python syntax and diff checks passed. The full formatter attempt found a concurrent AcornShipV2 line-wrap issue in `SSStation.cpp`, outside this change. The first UHT attempt failed because the reflected enum lacked zero. A hidden `None = 0` entry fixed that requirement while preserving IDs 1/2 and rejecting None from the purchasable roster. The subsequent editor build succeeded in 23.52 seconds. The final Unreal report at 2026-09-13 08:14:57 records 14 Success, zero warnings/failures/not-run tests, including the reflected utility bridge. Content authoring and fresh validation also passed at the lead checkpoint; native vendor behavior with custom prices is not yet claimed. See the [utility tuning receipt](validation/2026-09-13-utility-tuning.json).
