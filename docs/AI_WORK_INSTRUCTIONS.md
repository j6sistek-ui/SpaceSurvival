# AI work instructions: characters, animation and physics

Every AI assistant working on a character, an animation or a physics setup in this repository follows these
instructions, so the work is approached the same way every time. Read this file before that work starts.

It owns **method**. It does not own scope, priorities or status:

- [AGENTS.md](../AGENTS.md) owns what you may do, and the documentation and PR policy.
- [CLAUDE.md](../CLAUDE.md) owns how this machine works, the cost rules and the hard rules (no window on the
  owner's screen, one Unreal process, one capture at a time).
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) owns what is open, per character. Nothing in this file is the status of
  a character's work; the one table here records how far each **method** is proven.

Each rule carries the date and the case that taught it. A rule with no case behind it does not belong here.

## When these instructions change, and how the owner is told

These instructions are meant to change. A method proven on one character is a starting point for the next,
not a guarantee. The owner must never find out later that the method shifted.

**Triggers.** Any one of these means the instructions change, in the same piece of work:

1. A rule here was followed and the result failed on this character.
2. A rule had to be skipped or worked around to get the result.
3. A step that is not written here was needed to make it work.
4. A starting value had to be different for this character.
5. A second character confirmed a method that was proven on only one.
6. The owner corrected an approach or stated a preference.
7. A tool or engine change removed a trap listed here, or added one.

**When the check happens.** Twice, every time, for any character, animation or physics work:

- **At the moment of deviation.** Before doing something differently from what is written here, say so to the
  owner in one line: what the instruction says, what will be done instead, and why. Then carry on; this is a
  notice, not a request for permission, unless it touches one of the owner's own quoted rules.
- **Before the closing report.** Compare what was actually done with these instructions, trigger by trigger.
  Update the file, or state that nothing changed.

**How the owner is told.** Every closing report for this kind of work ends with a line headed
**Method changes**, even when the answer is "none":

- what changed in these instructions, in plain words;
- which character and which result caused it;
- what it means for characters already done (nothing, or "needs redoing on X").

The same entry goes in the change log at the end of this file, and the table "How far each method is proven"
is updated.

A pull request carries the same line under Owner review: `Method changes: None — <why>` or
`Method changes: Changed — <what changed, which character, what it means for characters already done>`.
The documentation check (`Scripts/CheckPrDocumentation.py`) refuses a ready pull request without exactly one
such line, from any assistant. The check sees that the line is there and specific; it cannot tell whether it
is true. Work that never becomes a pull request is covered only by the closing-report rule above.

**Rules for the edit itself**

- Replace the rule, add the date and one line on what happened. Do not leave the old rule beside the new one.
- A value that differs per character goes in as a per-character value with its reason. Do not widen the
  shared starting value to fit one character.
- A method that worked once on one character is recorded as that: say which character and how it was verified.
- Do not record a guess as a rule. "Tried, looked right in one frame" is not verification.
- The owner's own rules are quoted and dated. Only the owner changes those: a conflict with one is put to him
  as a question, never resolved by editing the quote.

## How far each method is proven

This is the standing of the **method**, not of the work on a character (that is in KNOWN_ISSUES). A method
proven on one character is expected to need changes on the next. When it does, a trigger above has fired.

| Method | Proven on | How it was verified | Not yet tried on |
| --- | --- | --- | --- |
| True-centimetre export, delete-and-create import | Freya | Bone scale and height read in the engine; all clips play at size; level actor found her again | Allison, Femme2 |
| Measured-flat normal for materials with no normal map | Allison, Freya, Femme2 | Same-camera frames and the surface-normal view | — |
| Height map converted to a normal map at the source's strength | Allison | Close-up frames, before and after | Any other bump-mapped skin |
| Hair chains recovered from the pack original by vertex order | Freya | Edge-length check; hair hangs and stays attached in frame sheets | Any hair whose original has no bones (Allison's ponytail, Femme2's hair): chains must be generated, and that method is not written yet |
| Sphere colliders fitted to the clothed body | Freya | No starting penetration; frame sheets | A flat back (the single sphere lets back hair slide off: a box is the next thing to try) |
| Hair physics asset, starting values in section 4 | Freya | Bone tracks and three-camera frame sheets; owner: "better" | Walking characters (Freya stands at a console), short hair, ears and tails |

## 1. Working method

**Sources**

- An owner-approved master file is opened to read, never saved. Hash it before and after and stop if the hash
  moved. All changes are made to an in-memory copy or a separate derivative.
- Look for the pack's own source before building anything by hand: its Blueprint, its skeleton, its bone
  chains, its original mesh in the asset library. A "fitted" or converted copy has often lost data that the
  original still has. *(2026-11-20: Freya's hair bones were recovered exactly from the library's original.)*
- Working files, exports, captures and backups live outside the repository (see section 5). Game files stay
  in the project. Caches and cooks never go on the external drive.

**Evidence**

- Look at the frames before calling anything fixed, and show same-camera before and after. The owner judges
  characters in game, lit and moving; a clay render or a number supports that and never replaces it.
- Measure the thing, not its name. *(2026-11-20: a texture named `DefaultNormal` was assumed flat. It is a
  tiled-floor pattern, and it put a grid of lines on a character's skin for a whole pass.)*
- One odd frame is not a diagnosis. Check a second angle or a second frame before investigating.
- When the game does not match the source file, test in this order and stop at the first stage that differs:
  the source file, the exported file read back, a posed frame in the authoring tool, the engine at reference
  pose, then the materials and textures the level actor really renders with.
- Report plainly: what was done, what was not, and what was judged from stills only.

**Cost and scope**

- Ask in one line before investigating anything the owner did not ask for. Noticing a defect is not
  authorisation to chase it.
- A loose idea from the owner is a request for one reasoned design, not a menu of decisions.
- Severity, owner 2026-11-20: torn skin or a disconnected mesh is fixed now. A pinched shoulder in a dance is
  logged in KNOWN_ISSUES and left.

**Saving**

- A level is saved only through a gate script that checks the state it expects and backs the level up first.
- Never save a level staged for stills, or one holding a test actor.
- Back up the asset files before any import that replaces them.
- Nothing is committed unless the owner asks.

## 2. Character setup

**Size and units**

- Owner, 2026-11-20: a new character is at most 178 cm unless he asks for taller. Smaller is fine. Always
  tell him when one is over. Never rescale an existing dancer or alien to meet it.
- Export in **true centimetres**: scale the data by 100 in memory, set the scene unit to 0.01, and export
  with no FBX unit scaling. Import at scale 1. Every bone then has scale 1.
  *(2026-11-20: metre exports imported at scale 100 left scale 100 on every bone. Physics multiplied every
  collision shape by it, and anything attached to a socket inherited it.)*
- The mesh and **every** clip that skeleton plays come from exports in the same units. A clip from the other
  route plays the character 100 times too big or too small.
- Changing units, or anything else in the skeleton's reference pose, means delete and create at the same
  asset paths, with the level that uses the character **not loaded**. The saved level finds the assets again.
  Never reimport in place across a unit change. *(2026-11-20: that left a character 178 metres tall, saved.)*

**Skeleton and mesh**

- One root bone. Export deform bones only, with their own names; leave control rigs, helper armatures and
  widget shapes out.
- Apply a modifier only where the master's handoff says the look depends on it, and say so in the export log.
- Leave hidden helper meshes out of the export.
- Owner rule: a garment or a hairpiece is never heavier than the body wearing it. Check vertex counts in the
  engine, where flat shading and seams split vertices.

**Materials**

- One master material per character and one instance per source material. Texture roles come from the source
  material graph, not from file names.
- A material with no normal map of its own gets a texture **measured** flat (`BaseFlattenNormalMap`). It
  never inherits another material's map, and never `DefaultNormal`.
- A height map fed through a bump node is not a normal map. Convert it at the strength the source sets:
  slope = height change per pixel x bump distance x pixels per metre on the surface.
  *(2026-11-20, Allison's skin.)*
- Normal maps from Blender are OpenGL; flip green for Unreal.
- Opacity can come from the base colour's own alpha or from a separate grey map. Read which from the graph.

**Clothing switch (18+)**

- Owner, 2026-11-20: the switch removes tops only, for everyone except the dancers, who remove all. A unique
  outfit is discussed with him first.
- Pieces are matched by material slot name. Before saving, check that no name on the list also matches the
  body, and that the lower half and the body stay.

**A character is "in" when**

- height and bone scale are checked in the engine (bone scale 1);
- every material slot is assigned and the reference pose is clean in the surface-normal view;
- each clip plays her at the right size;
- frames with the clothing switch off and on show a whole body;
- the level is saved through its gate, and her open points are in KNOWN_ISSUES.

Placing a character in a level is a separate instruction. An import request is import only.

## 3. Animation

**Measuring**

- Measure in the engine's own output, not in the source data. A rig on top can undo a clean base clip.
- Measure snaps parent-relative at two thresholds: over 30 degrees a frame (visible) and over 60 (a pop).
- Report the worst case and the share of frames within tolerance. A median hides a 53 cm miss.
- Joint limits are measured against the rest pose or a straight joint, never raw bone axes.
- Clearance is checked against the skinned surface, including the shoulder, not against bones.
- Arm twist is the hand's turn against the upper arm, elbow and wrist together. Wrist roll alone hides it.
- Palm direction is a separate check from palm distance.

**Fixing**

- Contact is not collision. A hand on a hip or a thigh round a pole is the performance. Push only true
  pass-through, by a few centimetres, and compare every pass with the original side by side.
- Stacked fixes compound. Smooth the total offset against the original motion and check for one-frame jumps
  after every pass.
- A smoothing pass after a constraint solve breaks the constraint. Re-apply it, with a guard.
- Knees and elbows are hinges: one axis, with roll and roll-rate limits.
- When contact needs a fast arm swing, move the body, not the arm.
- Before changing a clip, check who else plays it.

**Clips on a new character**

- Retarget onto the character's own skeleton and keep her proportions. Run a hand-clearance pass against her
  own body and outfit.
- A walking character's speed matches the clip's foot speed. Measure it; do not guess.
- A clip change is a cut unless a blend is built. Say which it is.

**Review**

- Before and after sheets: same camera, every frame through fast motion.
- Find defects on a sampling grid shifted by half a step from the last pass. Confirm a fix on the exact frame
  that showed the defect.
- A stick figure or an x-ray view checks pose and contact. It never judges how the body looks.
- Never call an animation fixed from numbers alone.

## 4. Physics

**Owner rule, 2026-11-20:** long hair falls with gravity and stays out of the skin. No walking character has
fixed hair, unless it is short or it is not hair.

**Before any physics**

- The skeleton has unit-scale bones (section 2). Do not start otherwise.
- Check what the master already bakes in. A baked jiggle clip and a runtime spring on the same bones stack.

**Card hair** (flat strips with a hair texture, which is what bought characters ship)

- Card hair moves on bone chains: a few chains, each carrying a clump, blended by weights. It is not one bone
  per strand.
- Recover the chains and weights from the pack's original when the fitted copy has the same vertex order.
  Copy weights index to index, and move each bone by the local reshape. Do not match vertices by nearest
  position: cards share texture space and lie on top of each other, and about one edge in eight comes out
  wrong.
- Generate chains only when no original has them.
- Short pieces (bangs) stay rigid on the head.
- Strand hair (a groom) is a different asset and a different cost. It is the owner's decision per character.

**Colliders**

- Fit collision spheres to the **clothed** body, per bone, sampled evenly so dense detail does not outvote
  the skin.
- Nothing starts in penetration. The approved resting hair is the authority: a collider it already sits
  inside is shrunk until it clears. A body that starts inside a collider is thrown on the first frame.
- Thin hair bodies with inflated body colliders give the same stand-off and far fewer hair-on-hair contacts.

**The physics asset** *(Freya, 2026-11-20; verified in same-camera frame sheets, not yet judged in motion)*

- Body colliders are kinematic. Hair chain bodies are simulated. A simulated body runs on an animated
  character as soon as the component has physics collision on. No Anim Blueprint is needed.
- The component collides with physics bodies only, never with the world.
- Each joint is anchored at the child bone with its twist axis along the hair, has swing and twist limits, a
  soft drive toward the rest angle, and damping. Hair bodies have drag.
- Starting values: hair body radius 1.2 cm, colliders inflated 1.3 cm, drag 2, spin drag 3, swing 45 degrees
  (55 at the root), twist 15, drive stiffness 10, damping 14.
- Tune in this order: drag, damping, limits, stiffness. A stiff drive puts the hair back where the complaint
  started, sticking out with the head.

**Tool traps in Unreal 5.8** *(each one cost a test run or an editor crash on 2026-11-20)*

- The toolset's `AddConstraint` leaves both joint anchors at zero, which pins every bone onto its parent.
- Limits and drives must be written through the joint template's edit path. Written any other way they
  vanish on save.
- A rebuilt physics asset keeps orphaned joints and bodies under their old names. Writing to one reads back
  correctly and changes nothing in game. Prove the write against the asset's own lists.
- Do not reload a physics asset, or read it through the Python constraint accessors, in the session that
  rebuilt it. Rebuild in place, and remove any level actor that uses the mesh first.

**Verifying**

- Track a few bones through a play test: distance from the head and height relative to it. Collapsed chains
  and thrown chains both show in the numbers before they show in a frame.
- Then frames from the side, front and back, same cameras as the "before".
- Watch the frame rate. A broken setup cost most of it.
- The first play of an editor session hitches. Run the probe twice and use the second.

## 5. Where the working tools are

The scripts that implement these methods are local working files, outside the repository by the owner's
storage rule. They live under `X:/Claude_Work/Club/vip` with their logs in
`README_ROUND2_20261120.md` there. The ones these instructions depend on:

| Purpose | Script |
| --- | --- |
| Import a character export (create, replace, materials) | `import_char.py` |
| Export a character from her master | `<character>/export_*.py` |
| Height map to normal map at the source's strength | `q_bump.py`, `q_texel.py`, `bump_to_normal.py` |
| Is a "flat" texture flat | `q_flat.py` |
| What a level actor really renders with | `q_wear.py`, `q_skm.py` |
| Hair bones and weights from a pack original | `hair_transfer.py` |
| Collision spheres fitted to the clothed body | `hair_colliders.py` |
| Build and save a hair physics asset | `pa_tools.py`, `build_hair_pa.py`, `hair_pa_save.py` |

Shared animation notes for every chat are in `X:/Claude_Work/ANIMATION_CONTINUITY.md`, also local by the
owner's decision. Read it before animation work and update it before finishing.

Moving any of these tools into the repository is the owner's decision.

## Change log

Newest first. One entry per change: what changed, which character and result caused it, and what it means
for characters already done.

- 2026-11-20: the pull-request documentation check now requires a **Method changes** line in every ready
  pull request (owner: "yes" to enforcing it). Cause: a written rule alone depends on each assistant
  following it. Nothing to redo on any character.
- 2026-11-20: added the triggers, the two fixed check points, the **Method changes** line in every closing
  report, and the table of how far each method is proven. Cause: the owner asked when the instructions get
  updated, because method shifts had been happening without him knowing. Nothing to redo on any character.
- 2026-11-20: first version, written at the owner's request after the club characters (Freya, Allison,
  Femme2) were brought in. Sections 2 and 4 come from that work; section 3 gathers the standing animation
  lessons from the shared animation notes.
