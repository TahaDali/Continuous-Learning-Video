# Validation and owner acceptance

## Owner acceptance - October 20, 2026

The owner stated that they reviewed the five sample courses, accepted the combined final version, and authorized remediation and public release as **Continuous-Learning-Video**. Apache-2.0 was separately approved. This records actual owner acceptance; it does not retroactively assert that every independent perceptual check was completed.

The private development record covers 154 chapters and approximately 399 minutes across Axios staff software engineering (45 chapters), Figma product design (25), Mill hardware/product design (27), Wikimedia financial partnering (25) and GitLab public-sector sales (32). These are agent-authored development cases, not an unattended compiler benchmark. Their private media, hosting identities and source snapshots are excluded from the repository and release ZIP. No course audience changes are authorized by publication of the skill.

## What the automated checks establish

CI exercises source/resource checks, clean locked canvas installation, the explicit 12-second/288-frame silent example, full silent-video decoding, Python regressions, controlled player contracts and secret scanning. Packaging tests verify exact payload selection, no-overwrite/symlink/nested-output behavior and reproducible checksums. Workflow tests exercise evidence references, state invalidation, prototype identity, media/caption validation and allowlisted export.

The retained player contracts include a later manual pause overriding asynchronous transcript seek/recovery and stale work not affecting a new chapter. The renderer checks registered geometry and selected numeric Canvas arguments at output timestamps. These checks do not cover every glyph, raster effect, connector, causal claim or learner interpretation.

For design-system worlds the frame audit also fails three kinds of frame:

- registered text below its tier's floor on screen;
- text the edge guard had to fade outside a transition;
- frames over the 24-word budget.

Narration cue lookup rejects a repeated word that does not name its occurrence. Regression tests cover these guardrails, the templates, the cast and the sentence sampling of `review_frames.py`. Its contact sheets are sampled evidence for a reviewer, not an automated judgment of meaning.

## Faster production path

The production path was shortened without changing what a course looks like. Regression tests cover each claim below.

- **One encode per lesson.** `render.cjs` draws a lesson's picture once and the narrated file copies that video stream. On the design demo with synthetic narration, the narrated MP4 produced this way is byte-identical to the one the previous renderer drew a second time.
- **Per-lesson scope.** A lesson with its own module is redrawn and replayed only when its own files, its lesson record or timing, its rules, the shared course fields or the tool itself change. A lesson's world cannot read another lesson's scenes or timing, so that identity cannot miss a dependency.
- **Two more every-frame checks.** The audit rejects a label that becomes readable and is gone within 0.5 s, and holds the fiction badge to scenes that declare `fiction`. The first found a real case in the bundled design demo, where an equation term was on screen for 0.25 s at default timing; the demo now fades that line before the term would open. Compared frame by frame before encoding, the demo is unchanged at slow narration rates and differs only in that one- to two-second window at the others.
- **Derived plan structure.** `workflow.py sync` builds the beat-sheet skeleton, timing estimates and player data from `course.json`. A sync of the design demo leaves every authored field and cue time unchanged.
- **Independent narration and visuals stages.** Either can be recorded first; narration first is the documented order.

A mechanical trial on four copies of the demo lesson (5.8 minutes of video, synthetic silent narration, four cores) took 283 s through the previous commands and 93 s through these, with the same outputs. That measures tool time only. It is not a measurement of an authored course, of agent time or tokens, or of review quality; no speech was requested and no course was authored or hosted for this change.

## Review limits

Complete independent listening and whole-course synchronized/silent viewing were not established by the audit. Selected encoded inspection and owner acceptance remain different evidence. Physical mobile, full screen-reader accessibility, Windows and a clean physical second machine are not certified. No blanket WCAG, human-voice realism, pronunciation or learner-effectiveness claim is made.

The owner accepted the sample courses and authorized this release with the recorded limits. Future course deliveries must keep their own truthful review records. A hash, passing schema or playback confirmation does not establish full perceptual review.

The [earlier Axios trial](e2e-axios-8229298.md) is historical evidence. Its counts and private-release wording describe its original snapshot, not the current repository visibility or a new acceptance certificate.

## Reusable player mobile update

The starter now carries the touch, transcript, radio-group, focus, and modal behavior checked in the historical example. A fresh package-generated mechanical course was checked in Chrome at 320 × 640, 375 × 812, 390 × 844, 768 × 1024, 568 × 320 and 1280 × 720. Those checks found no page-wide overflow, no visible authored control below 44px in height, and 16px transcript reading text. Keyboard checks covered radio selection/feedback, transcript focus, drawer focus containment, Escape return, landscape reset actions and horizontal scrolling of the generated HTML beat sheet.

Player contracts also exercise those interactions while retaining asynchronous media recovery, saved-state and transcript-download checks. The HTML plan regression checks canonical text, escaped markup, names and column-header relationships. These are bounded browser and automated checks: physical phones, spoken screen readers and complete accessibility conformance remain unverified. The separate 25-lesson Pages branch is unchanged by this skill-source update.
