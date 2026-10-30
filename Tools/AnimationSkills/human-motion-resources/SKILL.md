---
name: human-motion-resources
description: "Choose and apply human animation resources: video motion recovery, mocap retargeting, SMPL/MANO reference bodies and hands, corrective deformation, and Unreal contact constraints. Use when evaluating these resources or adapting motion to a character; not for UI animation."
---

# Human Motion Resources

Turn the available resource into a small, testable improvement on the intended
character. Explain **why it helps, what it cannot establish, the compatibility
work, and the next concrete test**. Preserve the chosen choreography and character.

## Choose the problem before the tool

Read the relevant rows in [application-matrix.md](references/application-matrix.md).
Classify the visible failure before changing anything:

1. **Motion:** poses, pacing, coordinated limbs, root trajectory and transitions.
2. **Retarget:** source/target rest poses, bone axes, scale and joint mapping.
3. **Contact:** a hand/foot/leg fails to reach or slides through an apparatus.
4. **Deformation:** the bones reach an acceptable pose but the skin pinches or collapses.
5. **Secondary motion:** cloth, hair, chains or soft tissue follow-through.

More than one layer may fail. Compare them separately; a skin correction cannot
make a hand reach the pole, and a contact solver does not create better skin weights.
Prefer existing usable mocap and native rig tools over constructing motion anew.
SMPL/MANO are mathematical body models, not a universal range-of-motion or collision engine.

## Work from evidence

- Identify the exact source and target, topology, skeleton/bind pose, morph names,
  units, frame rate, motion/root convention, current environment and ownership.
  Names such as "same body" or "Mixamo compatible" are hypotheses until compared.
- Consult [verified-resources.md](references/verified-resources.md) for inspected
  local files and traps. These are dated observations: refresh cheap facts before
  running anything. Other machines should locate equivalent resources rather than
  copying this machine's paths blindly.
- State a bounded hypothesis and a small test that could disprove it. Reuse
  source extraction when its input identity/settings still match; do not repeat
  inference, download models or install a second tool merely to inspect an output.
- Follow [application-workflows.md](references/application-workflows.md) only for
  the selected route. Start with a short excerpt or a few diagnostic poses,
  compare a preserved control, then inspect continuous motion and the target mesh.
- Report evidence levels separately: **present → parsed → converted → motion
  reviewed → target/native validated → owner accepted**. Advancement in one
  resource does not confer acceptance on another.

## Reusable operating boundaries

- Keep original assets and accepted controls intact. Use derived, traceable copies
  and agreed scratch/output storage. Inspect archives without executing bundled
  scripts; legacy Python2, pickle and Chumpy formats need a deliberate compatibility
  path, not global dependency changes.
- Check the current owner instruction before GPU/native-editor work. A skill is
  not permission to launch an editor, stop another chat, alter a shared skeleton,
  install plugins, upload licensed material or resume a held backlog.
- Pose channels, learned morph deltas, skin weights, joint limits and physics
  are different data. Do not relabel a target's morphs `Pose###` to trick a plugin
  into treating an unrelated mesh as SMPL.
- Joint-limit axes are rig-local. Do not copy another rig's numeric limits or
  interpret PCA coefficients as Euler angles. Preserve proportions: solve a
  feasible contact/root/limb configuration rather than stretching the skeleton.
- Keep extraction, tool-code, model/data and release permissions distinct.
  An authorized evaluation need not repeat resolved permission questions, but
  research-model installation does not establish commercial distribution rights.

## SpaceSurvival application

Read the current `.agent/CONTINUITY.md`, `AGENTS.md`, `CLAUDE.md`, the active
`docs/KNOWN_ISSUES.md` item, and relevant parts of
`docs/production/DANCE_OWNER_FEEDBACK.md` before project changes. For existing
deformation work, reuse the current local `DEFORMATION_RECIPE.md` if present;
refresh the actual target asset/handoff rather than choosing an older Vexa by name.

The owner wants the complete deliberate routine first, then detailed physics;
do not erase good motion to conceal rig defects. Review both sides, intermediate
bends, wrists/ankles, root/contact transitions and the whole loop. A good still,
finite values or a self-intersection report is not a gold-standard rig. Hair is
last unless the owner changes the priority. Existing game evidence/PR rules apply.

## Deliver a useful decision

Give the selected matrix row, reason, observed compatibility, smallest next test,
expected artifact and remaining uncertainty. After execution, include exact
input/output identities, settings, measured/visual results and adoption state.
Keep active follow-ups in the project's existing issue log; this skill and its
matrix are reusable guidance, not another competing backlog.
