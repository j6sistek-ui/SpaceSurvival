---
name: ue5-blueprint-workflow
description: UE5.6-UE5.8 Blueprint graph workflow for feature implementation, input events, node wiring, and graph validation. Use when requests involve adding Blueprint logic, keyboard input behavior, function chains, event graph edits, or pin-level connection guidance.
---

Read [the SpaceSurvival adapter](references/project-adapter.md) before applying this generic workflow. It maps the scope, existing systems, tooling and evidence requirements.

# Quick Start
- Identify target Blueprint asset and graph (`EventGraph` or function graph).
- Confirm requested behavior as event -> logic -> output chain.
- Decide input route first: legacy key event or Enhanced Input action event.
- Produce graph-level steps first, then exact node/pin wiring details.

# API Anchors (UE5.6-UE5.8)
- Keyboard and event node anchors:
  - `UK2Node_InputKey`, `UK2Node_InputAction`, `UK2Node_InputActionEvent`
  - `UK2Node_CallFunction`, `UK2Node_CustomEvent`
- Enhanced Input anchors:
  - `UInputAction`, `UInputMappingContext`
  - `UEnhancedInputLocalPlayerSubsystem::AddMappingContext(...)`
  - `UEnhancedInputLocalPlayerSubsystem::RemoveMappingContext(...)`
  - `UEnhancedInputComponent::BindAction(...)`
- Discover the connected editor tool inventory and schemas before choosing an automation operation. Tool names in upstream examples are not guaranteed to exist here.

# Graph Stage Contract
- Every requested Blueprint feature must specify:
  - Entry event source (key/input action/custom event)
  - The minimal core logic needed for the behavior (no arbitrary node minimum)
  - Required pin-level connections (exec and data pins)
  - Output/side effects (state change, call, spawn, UI)
  - Validation method (compile status, node/pin inspection, expected execution order)
- If any item is missing, the graph implementation is incomplete.

# Workflow
## 1) Entry Event
- Locate the existing native or Blueprint input route before editing a graph.
- For a Blueprint-owned Enhanced Input action, add/reuse the corresponding action event after checking its mapping context and ownership.
- For a legacy key event that is actually required, use a supported dedicated operation if available and avoid duplicates. Native player input is not a reason to create a Blueprint event.

## 2) Core Logic Chain
- Build minimal deterministic logic with explicit control flow (`Branch`, `Sequence`, function calls).
- Prefer existing graph variables/functions over creating redundant nodes.
- Keep one clear execution path per behavior branch.

## 3) Pin Wiring
- Connect exec pins before data pins to lock execution order.
- Inspect exact pin names through the available editor tools before connecting them.
- Avoid ambiguous autowiring when multiple overload pins exist.

## 4) State/Output
- Apply state updates (variables/tags), then side effects (spawn/call/UI feedback).
- Keep output nodes isolated by intent to simplify later debugging.
- When both success/fail paths exist, wire both explicitly.

## 5) Validation and Summary
- Validate compile state and pin integrity after wiring.
- Confirm there are no duplicate input nodes for the same key/action.
- Summarize final chain in deterministic order: entry -> branch -> action -> output.

# Constraints
- Reuse existing key/action events where appropriate and verify that input is bound only once.
- Avoid trial-and-error node class guessing when a dedicated operation exists.
- Separate graph steps from pin-level detail in final output.
- Prefer Enhanced Input assets (`UInputAction`/`UInputMappingContext`) for new input systems.
- Avoid hidden behavior in latent/timer nodes unless explicitly requested.

# Failure Handling
- Symptom: key press does not fire.
  - Locate: input node type, duplicated key nodes, input focus/context.
  - Fix: repair the actual native or Blueprint binding, remove duplicates, and verify focus and the mapping context path.
- Symptom: graph compiles with warnings but behavior is wrong.
  - Locate: branch conditions and exec pin order.
  - Fix: reorder exec chain and verify condition data pins.
- Symptom: pin connection fails in automation.
  - Locate: node variant pin names or overload mismatch.
  - Fix: inspect exact pins with the available editor tools before wiring.
- Symptom: Enhanced Input event exists but never triggers.
  - Locate: mapping context registration and action binding path.
  - Fix: ensure mapping context is added and action event node matches action asset.
- Symptom: event fires multiple times unexpectedly.
  - Locate: duplicate entry nodes or repeated binding paths.
  - Fix: consolidate to one entry node and guard re-entrant path with state flags.
- Symptom: graph no longer compiles after edits.
  - Locate: broken links after node replacement or stale function signatures.
  - Fix: reconnect required pins and refresh function node signatures.

# UE5.6-UE5.8 Compatibility Notes
- Core Blueprint graph nodes above are stable across UE5.6-UE5.8.
- UE5.8 adds an Enhanced Input UI Input Debugger; use it when available, while keeping log and mapping-context checks valid for 5.6/5.7.
- Prefer Enhanced Input path for new implementations across all supported versions.

# Escalation
- Escalate when behavior requires C++ extension, custom latent nodes, or engine plugin changes.
- Escalate when Blueprint is locked, corrupted, or cannot compile due to unrelated project errors.
