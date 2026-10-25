# Character workshop

## October23 three-floor layout

The owner's new direction is saved separately as `/Game/SpaceSurvival/Licensed/EntertainmentObservatory/L_EntertainmentObservatory`: copied crew/performance lounge below, enclosed middle lounge, Spectrum Galaxy panorama above, and a central aerial chamber shared by the upper floors. The original two-level workshop remains intact. Four customized character instances are preserved; Vexa's pink-haired aerial display has gravity/movement disabled only on this map instance. The others remain upstairs. Original body options, hair exports, clips and source Blueprints are unchanged.

Open the new map for layout work; its First Person review mode does not claim the copied wardrobe/services are integrated with the game. The compact editable architecture source is `SourceAssets/EntertainmentObservatory/Modules/Observatory_Modules.blend`. Fresh opposing views and stair movement checks are recorded in [the observatory receipt](../validation/2026-10-23-entertainment-observatory.md). Pole contact, clothing/hair quality and natural-input/owner acceptance remain open. RPT-20261023-02 owns the new layout; RPT-20261021-01 retains character work.

Owner-authorized character and animation workshop, October 21, 2026. This is a
separate authoring level for the future entertainment area. It does not replace
the current station, hero, or Lira's restaurant role.

## Identities

| Character | Source appearance | Dancer personality | Performance direction |
| --- | --- | --- | --- |
| Jinx, 27 | Customized Quinn | Cocky, competitive prankster; cheeky wagers and sharp comebacks | Athletic spins, clear accents, playful challenges |
| Roxie, 30 | Rosie | Warm party starter; earthy innuendo and affectionate teasing | Grounded rhythm, hips and shoulders, audience connection |
| Vesper, 32 | Satomi | Composed, dry and wicked; impeccable manners with outrageous implications | Controlled extensions, aerial shapes, slow tension |
| Vexa, 28 | Saved pink-haired Eden / Riley hair | Inventive instigator; raunchy space jokes and joyful mischief | Fluid spins, unusual shapes, later zero-G choreography |

Profiles are saved under `Content/SpaceSurvival/NpcTalk/Personas`. These names
are distinct from the source package names, which remain intact for traceability.
Their proposed troupe friendships are authored characterization, not claims of
events that have occurred in play. Profiles alone do not bind a vendor Blueprint
to the game's conversation system; that runtime integration remains open in
**RPT-20261021-01**.

## Local authoring inputs

- Saved merged source: `C:/Users/j6sis/Downloads/XCC-Quinn-Unreal/Quinn.uproject`.
- The separate Rosie, Satomi and native body-addon projects are retained as
  fallback originals. Their native package paths are present in the merged source.
- Native Blender body: `D:/FABDOWNLOADS/VaultCache/FabLibrary/F3___M3_Nude_Body_Addon-f51b768b/blender/blender_nudityaddon_extracted/F3_Nude.blend`.
- Portable packed body master: `C:/Users/j6sis/SpaceSurvival/SourceAssets/CharacterWorkshop_20261021/F3_Body_Master.blend`.
- The body master packs all 18 image resources. The original D file remains
  unchanged; active authoring output is on C.

## Motion intent

The supplied animations use an adult female source rig and require adaptation
to the F3 skeleton and proportions. G1 then G2 form one consecutive routine;
B1 then B2 form another. TW and both timestamped recordings remain separate
clips. The merged G export is retained as an alternate source, not silently
substituted for the requested pair. The aerial G routine requires pole/contact
review. Retargeted keys alone do not establish good limb motion or contact.

## Validation and storage

The canonical open-work record is **RPT-20261021-01** in
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md). Intermediate inspection receipts and scripts
are under `.agent/local/CharacterBatch_20261021`. Licensed native and Blender
artwork remains private; a source PR must not publish the purchased packs.

The independent 32 m circular hall is now in the canonical C project, with a 6 m
upper floor, stairs, a 5 cm pole and all four named actors upstairs. The existing
station and player are unchanged. This is an authoring workshop, not an accepted
runtime entertainment area.

## Open and edit

1. In Unreal's Content Drawer, open
   `/Game/SpaceSurvival/Licensed/CharacterWorkshop/L_EntertainmentWorkshop`.
2. Open `Sequences` in that same folder and select a girl's routine. G1_G2 and
   B1_B2 use the joined routines; TW and the two recordings are separate.
   The pole is a contact-test reference: the aerial routine is not yet fitted to it.
3. For Blender, open `C:/Users/j6sis/SpaceSurvival/SourceAssets/CharacterWorkshop_20261021/`
   and choose `Jinx_Character_Options.blend`, `Roxie_Character_Options.blend`,
   `Vesper_Character_Options.blend` or `Vexa_Character_Options.blend`.

In each Blender file, collections 01 and 02 form the character; toggle 03 for
the original removable outfit. Hide 03 and show 05 for Parise clothing. Keep 04
hidden: it retains the complete original clothed parts and would duplicate the
body. Select the root armature in the Action Editor to use one of nine `A_F3_`
actions at 25 fps. All image resources are packed. Blender shaders approximate
the native Unreal materials, with editable skin-match nodes; they are not an
identical shader conversion. The supplied older Blender body rig remains intact
in `F3_Body_Master.blend`, separately from the 95-bone UE export rig used here.

Eight self-contained hair GLBs are in `Hair`, including `Hair_Riley_Pink_Saved.glb`.
`MotionSources` preserves all seven original clips and the merged G alternate;
`MotionExports` holds adapted FBXs. `DeliveryManifest.json` records current hashes.
The private visual review is `.agent/local/CharacterBatch_20261021/Review.html`.

## Unreal options and other imports

- `CharacterWorkshop/Characters` contains twelve Blueprints: Original, Nude and
  Stylized for each name. Stylized uses the Parise garment and the addon body;
  original vendor packages and customization remain available under `/Game/XANDRA`.
- Parise materials expose `OutfitTint`; clothing is weighted, not cloth-simulated.
- Open `/Game/Sci-Fi_Spaceship/Overview` for the complete supplied ship. Its three
  mesh actors retain source material overrides; dragging the raw meshes alone
  uses their original grid-material defaults. This does not replace the player ship.
- `/Game/Flight` contains the supplied jetpack system. Its character, game mode,
  controls and input configuration are not activated for SpaceSurvival.
- Built-in `XRBase` is required by the vendor's customization Blueprint function
  library. It is enabled in the project; no VR platform is enabled.

## What is verified, and what remains

The original845-file adoption plus two new routines now matches the847-file
current native manifest. Eight sequences and four collision assets supersede
their original adoption hashes; both historical and current receipts are retained. Canonical reload tests twelve
variants against all seven clips at three times each. Actual-RHI captures show
all four characters and changing poses; these are sampled editor views, not
continuous natural gameplay. Four Blender files reopen with packed images and
nine actions each. Before replacing 176 existing native files, exact recovery
copies were verified under
`D:/SpaceSurvival_AssetArchive/CharacterWorkshop_20261021/BeforeAdoption_20261021T123245Z`.
Active files are on C; D is recovery only.

Lead work remains on pole/grip and floor contacts, full-motion
garment/skin/hair quality, workshop walking/collision, and vendor demo/animation
warnings. Ten hard dependency references are absent in the source collection:
seven footstep-dust references and three demo Control Rig redirects. Importer
bind-pose and UDIM warnings remain recorded. Do not mark these resolved from
finite poses or a successful load. Live dialogue/role binding, packaged testing
and owner acceptance are also open under RPT-20261021-01.

## October21 motion and collision follow-up

`A_F3_G1_G2_Routine` lasts31.36seconds; `A_F3_B1_B2_Routine` lasts45.60seconds.
Both preserve every original source key, align the second clip horizontally,
and insert a12-frame (0.48second) smoothstep bridge at25fps. Vertical aerial
motion is preserved. Eight character sequences use these two routine assets;
the other twelve single-clip sequences remain unchanged. Four packed Blender
files contain the same two additional actions, with all seven originals retained.

These joins remove the abrupt position jump, but are not pole-fitting or foot IK.
G still needs grip/pole alignment; low soles, garment intersections and continuous
motion need further review. The [follow-up receipt](../validation/2026-10-21-workshop-fixes.md)
records fresh reloads, collision probes, retained failures and their limits.

The newly requested rigging, flight controls, thrust physics and landing animations
for the imported ship are queued under RPT-20261021-02. Import is not flight readiness.
