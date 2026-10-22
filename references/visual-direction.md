# Design the visual explanation

Use before implementing a course world, and again when a supplied reference or user criticism changes the direction. The product's visual standard is illustrated spatial storytelling. A functional video renderer and a clean bounds audit do not establish that standard.

## Inspect the real reference

When the user identifies a course or visual reference, inspect actual encoded frames and transitions from the exact edition. Establish the source/version lineage. A palette, contact-sheet thumbnail or a written description alone is insufficient to reproduce a visual language. If remote access is blocked, use a matching authorized local artifact and state the boundary; do not bypass authentication or assume an earlier edition is identical.

Analyze the reference's object vocabulary, proportions, composition, typography, hierarchy, motion grammar, camera movement, density, contextual anchors and pacing. Name visible differences in the draft. “More polished” and “add icons” are not actionable design directions. Record a few representative comparison frames and the concrete changes they justify in the private project; do not redistribute private references with the skill.

An explanatory world can contain recognizable people, publications, envelopes,
documents, records, coins and access controls. Relationships accumulate, objects
retain identity, and a reframe exposes a new relationship while earlier context
remains available. Large rectangles containing nouns do not become a causal
explanation merely by matching a reference's colors. Choose subject-specific forms
and mechanisms for the actual role.

## Give the subject a visual vocabulary

Choose recognizable forms for the actual work. A publication has editorial structure; a document has identity and revision; a payment differs from a promise; a physical bracket has mating geometry, material and a manufacturing definition. A meaningful icon includes the internal details needed to tell those artifacts apart. Labels identify the object or its essential qualification; they should not carry the entire explanation while the shape remains inert.

Design each lesson around its own consequential scene. Infrastructure and drawing primitives may be shared. Do not assign the same generic world to unrelated paragraphs merely because they discuss a decision, evidence or a handoff. A revision-package mistake needs to show which definitions were issued, received and built; a generic build-yield diagram cannot substitute for that failure path.

The starter's `production-source/illustrations.cjs` provides original parameterized people, documents, browsers, phones, envelopes, buildings and clocks with darker companion text inks. `figure()` draws a person with a face, hair, clothes, a pose, a prop and a mouth that moves while speaking. A course defines its recurring people once with `defineCast` and stages them with `cast`, so the same person looks the same in every lesson. Use `createIllustration(stage)`, `figure` and `cast` with the design stage or the motion stage so glyph and label bounds enter the same audit. Supported literal local CommonJS imports are discovered transitively; declare non-module drawing inputs such as images or fonts in `renderSources`. Dynamic or alternate module loading fails explicitly. This is a vocabulary seed: author the subject's missing forms and causal scene, rather than inserting these glyphs into a repeated diagram. Shapes and paths still need raster inspection; automatic bounds do not verify their internal anatomy, meaning or readability.

Use a hierarchy of context, active mechanism and outcome. Scale and position encode relationships. Keep enough context to understand why the active detail matters, and zoom only when it reveals something. Empty travel, excessive text containers and crowded detail are different failures; filling space is not the objective. A sparse two-object explanation can be right when it teaches the complete relationship, but it cannot replace a richer operating scene that the narration actually requires.

## Stage it with the design system

[The design system](video/design-system.md) supplies the shared typographic hierarchy, colour meaning, motion timing, camera language and transitions; the subject supplies the objects and the mechanism. Frame the consequential scene with its templates: an opener with an agenda, one kinetic claim whose emphasised value is carried into the mechanism, a compare or line story that isolates what changed against what held, a stepper for a procedure, and a question on the night background. Keep templates subordinate to the scene they frame. Adapting to a user's reference changes the tokens and roles in one place; it does not justify per-scene fonts, colours or ad hoc easing.

Decide the course-wide choices once, before the first lesson:

- the state code a quantity can be in (`defineStates`);
- the recurring cast (`defineCast`);
- each part's opener layout and motif (`defineParts`);
- where the fiction badge is on and off.

Every lesson then reuses them.

## Write the design brief

Before authoring the first world, write a short brief in the private project, for example `design-brief.md` beside `visual-design.json`. It is working evidence and is not exported. Revise it when a reference or a user's criticism changes the direction, then re-check the lessons the change affects.

```markdown
# Design brief: <course title>

Reference: <exact edition and lineage, frames inspected>, or "none: the house system".
Adaptations: <token, face or role changes made once in design.cjs, with font licences>.

## Made once for the course
- State code: <state: token, solid or hatched, meaning, aliases>
- Cast: <key: name, role, look>; generic people: <keys>
- Parts: <part: layout, motif, the kind of hero object>
- Fiction: <what is invented; which material is real, so the badge is off there>

## Per lesson
| Lesson | Part | Hero object and its internal detail | Mechanism (visual-design.json id) | Reframing pushes | Transitions in | Practice picture |
```

The brief states the hard rules below. Each rule has a measure and names what checks it, so a reviewer can mark it met or failed. Where a rule says "review", no automatic check covers it.

| Rule | Measure | Checked by |
| --- | --- | --- |
| Type floors | Text carrying meaning is at least 28 px on screen after camera zoom. Units, ticks and glyph-internal IDs are at least 24 px. Only the rail and the fiction badge use 18 px chrome. | Audit `type-<id>` for sizes; `design_checks` rejects chrome type in worlds |
| Edges | Outside transitions, no visible text comes within 12 px of the safe area (40–1240 × 88–587). Nothing a viewer must read sits in the caption band. | Audit `edge-<id>`, review |
| Density | At most 24 content words are on screen in a frame. Each beat has one hero filling a third or more of the safe area. | Audit `words`, review |
| Timing | Every reveal lands on its spoken word, and a repeated cue word names its occurrence. Each template gets at least its minimum spoken span. | `createCues` throws, audit `fit-<template>`, sentence-end review |
| Reading time | Every label stays readable for at least 0.5 s. A highlighter marks one thing and retracts when the narration moves on. | Sentence-end review |
| Colour meanings | Signal marks only what is spoken about now. Red marks only what is wrong, green only what is correct or conserved, and violet is only the fiction badge. States never use a meaning colour. No colour or font literals appear in a world. | `defineStates` throws, `design_checks`, review |
| Numbers | A figure shows only a value the narrator says, and a count passes only through round steps. Totals stay conserved through motion. | `spoken`/`stepValue`, `finish({totalUnits, expectedTotal})`, review |
| Camera | A slow push stays within 1.06 across a scene, and within 1.03 while templates are on screen unless their labels fade first. Reframing pushes come from `fitCamera`. A counted group stays whole on screen. | Review |
| Transitions | Iris and wipe paint the full frame, and transitions begin in the closing pause. A pan never arrives on a blank page. | Audit `transitionFrames`, review |
| Pace | No beat stays sparse or static for more than about 2 s unless the beat sheet gives the reason. | Sentence-end review |
| People | Recurring people come only from cast presets and look the same in every lesson. | `cast()` throws on a look override, review across lessons |
| Fiction | The badge is on whenever invented people, companies or figures are on screen, including practice panels, and off over real facts. | Sentence-end review |

The brief does not replace the reference comparison or the prototype review. It makes their findings testable.

## Animate the cause

Construction, movement and transformations must respond to the explanation. Draw a path as a relationship becomes relevant; send the same identifiable object across it; show the actual blocked transition, changed value, split obligation or failed hypothesis. Retain the rejected state or relevant history when it explains the correction. Do not color a unit as failed before the test occurs or replace an unresolved obligation with a success label.

Anchor important events to the named phrase's measured word timing. Paragraph-wide linear interpolation can show a quantitative result too early or too late. A purposeful hold is appropriate for comprehension, but a mostly static labeled diagram under several minutes of new reasoning calls for redesigned staging, additional meaningful detail or tighter narration. Decorative movement does not solve that problem.

Compare the actual sequence across the full explanation, not just its attractive final frame. Introduce the evidence before rejecting or superseding it, preserve the identity of the object that passes a gate, and depict a new denominator or changed physical assumption explicitly. If a prototype contains separate implemented, mocked, unknown and failed states, keep them distinct. Near-static intervals are review candidates rather than automatic failures; a camera pan or moving clock cannot substitute for a missing cause or consequence. Inspect active quantities and labels at the normal embedded viewing size as well as full screen.

Physical forms must behave consistently with their stated model. A clamp must attach to the beam and change the depicted boundary; a shaft must visibly stop or enter; a conservation story must preserve the amount during transit. Label deliberate exaggeration where it helps interpret the model. Do not call an arbitrary sum of temperatures an energy-conservation check.

## Prove the direction before scaling

Create a short encoded scene with representative subject illustration, a difficult transition, a consequence and enough final detail to assess composition. Inspect its actual intermediate and final frames at the intended viewing size, and compare it directly with the reference. Review the motion, not just a decorative opening. Repair the visual language before multiplying it across a course.

The workflow probes each prototype with local `ffprobe`: it requires a positive-duration video stream with nonzero dimensions, excluding attached cover art. This rejects documents and audio files disguised as clips. It establishes media structure only; full decoding, actual sampled viewing, continuous motion review and any outstanding human acceptance remain separate checks.

Use a design-focused independent review for a substantial course when delegation is available and authorized. Ask the reviewer to identify visible mismatches and demonstrate a corrected scene. Distinguish that judgment from geometry, content review and a learner comprehension test.

If the user rejects the visual direction, mark the affected visual acceptance failed, preserve usable prose/audio and stop final bulk rendering/export. Rebuild representative scenes against the actual reference, then propagate the corrected language. Do not continue treating rejected prototypes as completed visual evidence. A saved review form is traceability, not approval.
