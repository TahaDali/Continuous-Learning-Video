# Changelog

## Unreleased

Shorter production runs with the same pictures. Tool time on a four-lesson mechanical trial fell from 283 s to 93 s; see [validation](docs/validation.md#faster-production-path) for what that does and does not measure.

- **One encode per lesson.** `render.cjs` draws each picture once into `review/silent/` and writes the narrated video by copying that stream and adding audio and captions. The narrated file is byte-identical to the one the previous renderer drew a second time. `--force` redraws; `--jobs N` renders lessons side by side.
- **Per-lesson worlds.** A lesson can have its own module, `production-source/worlds/<lessonId>.cjs`, and its own overlap rules in `worlds/<lessonId>.overlaps.json`. `lesson-scope.cjs` gives each lesson an identity of what its picture depends on; the renderer redraws and the audit replays only lessons whose identity changed. `audit.cjs --lesson <lessonId>` audits one lesson without touching the course report.
- **Narration no longer waits for visuals.** `workflow.py` treats narration and visuals as independent stages after the script. Narrating first is now the documented order, so worlds are authored on measured timing.
- **`workflow.py sync`.** Derives estimated scene timing, `player/course-data.js` and the sentence-cue skeleton of the beat sheet from `course.json`, keeps authored visual fields across script changes, and with `--split` keeps one working beat-sheet file per lesson.
- **Beat-level fields.** A beat may state `metaphor`, `elements`, `camera` and `risks` once for its cues.
- **Audit checks.** `flash` rejects a label that becomes readable and is gone within 0.5 s. `fiction-badge` holds the badge to scenes that declare `"fiction": true` or `false` in `course.json`. Transition windows are recorded per lesson. A flagged frame is drawn on its own canvas, so a failing audit no longer rasterizes every earlier frame.
- **Sentence-end review.** `review_frames.py` accepts `all`, writes a reviewer brief per lesson, has `--quiet` and `--jobs`, and samples the midpoint of each transition the audit recorded.
- **Validation.** A final video whose bytes an earlier passing run decoded is not decoded again.
- **Design demo.** Its equation line now leaves before the in-transit term would flash, and its scenes declare `fiction`.
- **Documentation.** Call signatures moved from the design-system reference into `references/video/design-api.md`. The workflow reference gains per-lesson and delegation guidance.

Existing projects keep working with their own copies of the renderer and audit. To use the new path in one, copy `render.cjs`, `audit.cjs`, `render-sources.cjs` and `lesson-scope.cjs` from the starter. The fiction-badge check also needs the starter's `templates.cjs` and the stage's `note` method in `design.cjs` and `motion.cjs`; a project that customized `design.cjs` adds that method instead of replacing the file. Worlds may then need changes:

- A label on screen for under 0.5 s now fails the audit. Fix its timing, or add a rule with `"type": "flash"` and a reason.
- A world that reads another lesson's `scenes` or timing through its `course` argument now throws.
- `workflow.py status` lists narration before visuals. Checkpoints recorded in the old order remain valid.

## 1.3.0 - 2026-10-22

- **Design-system guardrails in the frame audit:**
  - Type tiers with floors: content 28 px, tertiary 24 px, chrome 18 px. `role()` raises smaller sizes, and `type-<id>` fails text that is smaller on screen after zoom.
  - An edge guard fades text near the safe area and fails `edge-<id>` outside transitions.
  - `words` fails frames with more than 24 content words.
- **Ambiguous narration cues are rejected.** `cue(scene, word)` throws when the word is spoken more than once in the scene and no occurrence is named. `cue.count` and `cue.end` are new. A measured provider event that covers several words is split.
- **Memory leak fixed.** The background grain is now drawn from a decoded image instead of a canvas, which removes a leak of about 3.6 MB per rendered frame. `installDesignRuntime` now requires the canvas module's `Image`.
- **Full-frame transitions.** `iris()` and `wipe()` paint the full frame and clip only the next scene.
- **Colour meanings and the state code:**
  - Meaning tokens: `signal`/`signalSoft` (the highlighter), `wrong`/`wrongSoft`, `goodSoft` and `fiction`/`fictionInk`. `good` now means only correct or conserved.
  - A course-defined state code: `defineStates`, `stateOf`, `S.stateBox`, `S.swatch` and `S.hatch`.
  - Stage helpers: `S.callout`, `S.markText`, sentence highlighter runs, `S.rule`/`S.vrule`, `S.onScreen` and `S.night`.
- **Staging helpers:**
  - Camera: `fitCamera`, `beforePush`, `world`, `orderKeys` and `planner`.
  - Spoken numbers: `spoken`, `stepValue` and `niceStep`.
  - Focus: `talking` and `focusOf`.
- **Templates:**
  - New: `partOpener` with `defineParts`, `sectionHead`, `readout`, `stateKey` and `fictionBadge`.
  - `progressRail` uses chrome type, marks the current section in inverted ink, and gains `night` windows and `states`.
  - `question` gains `art`, `tags`, `tagsAt`, `optionsAt` and `promptAfter`. It highlights the correct option and strikes wrong ones in `wrong`.
  - `carry` gains `hold`.
  - Existing templates are re-laid out for the new checks.
- **People with faces in `illustrations.cjs`:** `figure`, poses, `blendArms`, props, and a course-defined cast (`defineCast`, `cast`) whose look cannot be overridden in a lesson. Glyph-internal lettering uses the tertiary tier.
- **Sentence-end review.** `scripts/review_frames.py` samples each narration sentence's end state into time-stamped contact sheets and a plan. Review and delivery guidance gains the sentence-end review procedure: reviewers, refuting verifiers, re-verification on fresh clips and honest coverage.
- **Design demo.** It now exercises the state code, spoken numbers, a reframing push, a ledger readout, a speaking cast member, fiction badge windows and a question with a picture. It runs about 72 seconds.
- **Documentation.** The design-system reference covers colour meanings, the state code, type tiers, the checks, the cue ambiguity rule, the camera push rule, full-frame transitions, the fiction badge rule, people and a do-and-don't list. Visual direction gains a design-brief template with measurable rules.
- **Render failures exit.** `render.cjs` closes the encoder's input before stopping it, so a world that throws fails the render instead of leaving it waiting for frames.
- **Chrome type stays in the templates.** Visual checks reject `role:'chrome'`, `tier:'chrome'` and `chrome:true` in authored worlds, because chrome type has the 18 px floor and skips the edge guard and the word budget.

Existing exports keep their names and signatures. Worlds written for 1.2.0 may need changes:

- A cue word spoken more than once now needs its `nth`.
- Roles below their floors now render larger (kicker 15 to 24 px, label 21 to 28, small 17 to 24, mono 17 to 28, accent small 27 to 28; `S.label` defaults to 28), which can cause new collisions.
- `strike()` defaults to ink instead of the accent.
- The progress rail and the question panel look different. The rail is about 1.4 times wider, so a 1.2.0 agenda can fail the new `rail-fit` and `rail-badge` checks; `progressRail` now returns its box.
- The stepper's travelling token is neutral ink instead of gold, or shows a course state through its new `state` option.
- `iris()`, `wipe()` and `S.unclipped()` throw when called inside `S.view`, `S.fade`, `S.actor` or a `world()` draw callback; call them at the top level of the frame.
- Content text drawn in the top band or the caption band is hidden and fails `edge-<id>`; only the rail and the fiction badge use chrome type there.
- Cue matching and the word budget now work in any script, so non-Latin narration can newly report ambiguous cues or crowded frames.
- `defineStates` rejects two states that share both colour and treatment.
- Frames that audited clean in 1.2.0 can now fail the type, edge or word checks.

Already rendered course media are unchanged.

## 1.2.0 - 2026-10-20

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
