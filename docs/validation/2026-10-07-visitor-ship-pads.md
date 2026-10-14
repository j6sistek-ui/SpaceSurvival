# Decorative visitor ship support correction

2026-10-07T20:03Z [TOOL] PARTIAL, UNSAVED_EDITOR_TEST. Two decorative Havolk
ships are lowered onto their existing pad decks; their four literal Cube support
blocks are hidden and have collision disabled. No actors or source assets are
deleted. Functional Phoenix boarding supports are excluded.

Root driver session36714 exits0. Separate ordinary before/after PIE sessions
produce two matched2742x781 views each. The saved Main, owner settings, player
saves, source bytes, dirty packages, targeted fourteen actor states, camera and
view restoration checks pass. Exact trial Z values are150.0000099182129cm south
and177.5000114440918cm north, derived from current imported bounds and the actual
deck tiles. Hull yaw, scale, material and collision remain unchanged.

- Before: `LiveOperationsPIEReview1_VisitorShipPads2_Before/manifest.json`,
  SHA `76def67f3647c04da77473ed7d4685faaeaccb8d621435803f8404b5da204651`.
- After: `LiveOperationsPIEReview1_VisitorShipPads2_After/manifest.json`,
  SHA `971d9d64e679f516bf20a5eafdc5341d85a0ef4a2c6f42f9f7ef53c4061a7371`.

Root and independent review accept block removal and the lower visual placement.
There is no obvious broad floor clipping or route obstruction in these two angles.
Raised engines/wing areas still read somewhat hover-like; source minima belong
to the fuselage rather than landing gear. Continuous contact and natural walking
clearance are unverified. Do not lower the hulls further merely to close gaps below
raised parts. The trial remains unsaved, owner approval is pending, and the
published build is unchanged.

The durable `Scripts/AuthorOutpostSandbox.py` correction removes only the four
decorative cradle spawns. It derives each decorative hull's bottom from its
generated Visitor02/03 deck top through `OutpostBerthDetails.bounds(row)[5]`.
The existing catalog yields47 Deck rows per pad and top0.5cm; mesh, XY, yaw,
scale and collision stay unchanged. Root and independent source review pass.
AST/in-memory compilation and diff checks pass; the generator has not been rerun
against the owner map. This source recipe does not save the live trial.
