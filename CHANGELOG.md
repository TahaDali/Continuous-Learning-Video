# Changelog

## Unreleased

- Add a shared design system for explanatory motion: `design.cjs` provides colour tokens, type roles, easing, narration cue lookup, camera keyframes, an auditable stage, hand-drawn annotations, rolling counters, focus dimming and motivated pan, iris and wipe transitions.
- Add `templates.cjs` teaching templates: opener with agenda, kinetic statement, carry, compare, line story, stepper, retrieval question and progress rail. Templates take narration cue times and report a `fit-<template>` audit failure when the spoken span is too short.
- Bundle Inter, Instrument Serif and JetBrains Mono under the SIL Open Font License; the renderer, posters and audit register them, and source discovery includes them in the render identity.
- Add `new_project.py --design-demo`, a fictional cue-driven 70-second example with a complete beat sheet; `check.py --render` renders, audits and decodes it alongside the mechanical example.
- Report per-lesson transition frames in the frame audit, allow scene-scoped intentional-overlap rules, and reject hard-coded colours and fonts in design-system worlds during visual checks.
- Document the system in `references/video/design-system.md` and connect it to the skill, visual direction, beat-sheet and production guidance.

## 1.1.0 - 2026-10-20

- Bring the historical example’s mobile controls, transcript shortcut, keyboard exercise selection, visible focus, modal focus handling and accessibility labels into the reusable player.
- Generate a responsive HTML beat sheet with named keyboard-scrollable tables and column headers alongside the existing Markdown output.
- Add player accessibility regressions and per-course mobile/keyboard review guidance. Preserve existing content and media during interface-only repairs; the separate 25-lesson Pages example is unchanged by this update.

## 1.0.1 - 2026-10-20

- Record the owner's confirmation and retained compilation trail for the historical AI-chat teaching story, closing its previously unrecorded conversation origin.
- Distinguish the Apache-2.0 skill from the separate Pages demo and its unresolved Edge-audio redistribution evidence.
- Require service-specific narration distribution evidence and a source-rights check before course publication; preserve existing provider choices and approval boundaries.
- Preserve historical commits, existing attribution, prior MIT grants and the private original reading document.

## 1.0.0 - 2026-10-20

- Publish the owner-approved combined workflow as **Continuous-Learning-Video**, invoked as `$continuous-learning-video`.
- Consolidate the current research, narrative, visual-authoring, narration, review, player and delivery helpers into one self-contained skill.
- Keep the latest causal-scene guidance and player behavior that respects a later pause during asynchronous seeking/recovery.
- Replace the adapted historical employer example in the current payload with a newly authored fictional teaching case.
- Harden release packaging with explicit payload paths, credential-file rejection, symlink checks, no-overwrite guarantees and rejection of source-nested outputs.
- Lock the renderer dependencies, pin CI action identities, add security/contribution guidance and document current installation and support boundaries.
- Apply owner-approved Apache-2.0 terms, preserve prior MIT grants and notices, and identify TahaDali as creator and maintainer.

The owner reviewed five private sample courses and approved the public skill release. Owner acceptance does not establish complete independent perceptual review, accessibility or learner effectiveness. Private course media and audiences are not part of this release.
