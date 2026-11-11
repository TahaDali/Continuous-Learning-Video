# Review and delivery

## Composition and timing

Inspect beginnings, endings and intermediate states. Check moving labels, full glyph extents, camera zoom, temporary copies, object travel, foreground masks and caption space. Include completed connector segments and partial arrowheads: a route can cross text before it reaches its clear final position. Different drawing contexts need one global draw order when assessing whether a later opaque object actually covers an earlier path. A clear end frame does not establish a clear transition.

The bundled audit replays every output-frame timestamp and checks visible registered object/label intersections and label safe zones in screen coordinates. Fully offscreen actors are ignored, and actors can cross the clipped viewport on entrance or exit. Delay labels until readable. It records flagged frame ranges, a representative PNG, declared intentional pairs and source hashes. It also follows each label through time and rejects one that becomes readable and is gone within 0.5 s (`flash`), and it holds the fiction badge to every scene that declares `fiction` in `course.json` (`fiction-badge`). Its result is a mechanical screen, not a claim that a human inspected every frame. The audit rejects non-finite alpha or bounds before filtering visibility, so NaN coordinates cannot disappear from collision checks. New rendering code must register its extents; unregistered strokes cannot be certified by this audit.

A lesson is replayed again only when something its picture depends on has changed: its own source files, its lesson record and timing, its rules, the shared course fields or the auditor. Otherwise its last clean result is kept and marked `reused`; the report still covers every lesson and every current source hash. A lesson with unresolved findings is always replayed, and `node production-source/audit.cjs --force` replays all of them.

Intentional overlap rules are narrow records in `intentional-overlaps.json`: exact lesson ID, exact stable object IDs, bounded start/end times and an educational reason. A lesson drawn by its own module keeps its rules beside it in `production-source/worlds/<lessonId>.overlaps.json`, where the lesson is implied. A rule with `"type": "flash"` names one label (`a`, no `b`) that may be on screen for under 0.5 s; it excuses nothing else about that label. An intentional stack, contained label or emerging copy can be legitimate. Nested illustrated composites can use explicit `owner` links on actor and label records; the audit follows those ancestors only when the descendant fits inside them. Shared ownership never exempts sibling collisions. Do not exempt all documents or an entire lesson. Examine each exemption's intermediate encoded frames. Report the accepted pairs alongside zero unresolved findings; do not hide them in a pass count.

Fix collisions through stable positions and choreographed timing. Separate label placement from actor construction where useful, stage reveals, route transfers through actual gaps and keep connectors behind foreground objects. Reserve space for captions, but also check actual browser/native caption rendering because font metrics and controls can differ. Do not solve crowding by making essential type unreadably small.

## Review layers

1. Validate source coverage and conceptual invariants: conserved quantities, consistent units, independent states, honest uncertainty, permissions and exceptions.
2. Run geometry checks at the output rate, inspect flagged intermediate frames and inspect encoded contact sheets covering every lesson with the [sentence-end review](#sentence-end-review). Add purpose-specific checks for the mechanism, such as conservation including in-flight amounts.
3. Probe and fully decode every final MP4. Check codecs, dimensions, rate, duration, audio and caption streams. Compare caption text against exact narration and check ordered, non-overlapping timings within duration. The validation helper covers these mechanical checks.
4. Listen to the complete narration independently: pronunciation, meaning, stress, rhythm, pauses, warmth, unnatural joins and excessive performance. Audio peak/clipping checks and optional local ASR are useful screens, not substitutes. Never claim to hear content when the tool reports audio input is unavailable.
5. Watch the synchronized result. Ensure objects gain their meaning at the named phrase, a reveal lands on emphasis, motion leaves comprehension time and captions stay clear. Export a silent excerpt without audio or subtitle streams for the creative test.

Record dates/version hashes, exact coverage and remaining issues. Recheck affected checks after edits. Do not rerun expensive checks for unchanged media without a reason.

A minimal acceptance report distinguishes:

| Area | Status | Evidence / limit |
|---|---|---|
| Content / beat coverage | Passed, failed, not reviewed | Sentence count and meaningful qualifications |
| Composition | Passed within scope, failed | Actual checked frames, registered extents, accepted overlaps |
| Media / captions | Passed, failed | Full decode, exact text, stream and timing results |
| Independent listening | Completed, pending, unavailable | Who listened and to how much; findings |
| Synchronized viewing | Completed, partial, pending | Actual lessons/time spans reviewed |
| Silent understanding | Producer inspection or learner test | Who inferred what; avoid overstated comprehension |

The user may accept working audio and request release while perceptual review is incomplete. Do not repeat a permission gate; deliver the accepted edition with the limit recorded accurately. Never upgrade playback confirmation into a fabricated listening certificate.

## Sentence-end review

The geometry audit proves bounds and overlaps, not meaning. After the first full render and before export, review what each narration sentence actually leaves on screen:

```bash
python3 <skill-dir>/scripts/review_frames.py /absolute/project all --quiet          # every lesson's player/videos/<lessonId>.mp4 -> review/sentence-end/
python3 <skill-dir>/scripts/review_frames.py /absolute/project <lessonId>           # one lesson, printing its brief
python3 <skill-dir>/scripts/review_frames.py /absolute/project <lessonId> --silent  # review/silent/<lessonId>.mp4 -> review/sentence-end-silent/
```

For each scene the script grabs the frame 0.6 s into the scene and the frame 0.15 s (`--lead`) before each sentence's last word ends: the state that sentence should have produced. Sentences map to measured word timings by character offset (`charStart`), so a repeated word cannot pull a sample to its earlier occurrence; closing quotes, decimals and common abbreviations do not split sentences, and a sentence may start with a lower-case name such as "iPhone". Without measured timings it spreads the beat-sheet cues and marks the scene `estimated`.

It writes `<lessonId>-plan.json`, full-size frames under `frames/<lessonId>/` and one two-column, time-stamped sheet per scene under `sheets/<lessonId>/`, using ffmpeg only. Each plan entry holds `scene`, `headline`, `start`, `end`, `points` as `[time, sentence]`, `unmapped` sentences, frame and sheet paths, and the sampled `video`, `videoDuration`, `videoModified` and `silent` (no audio stream). It also writes `<lessonId>-brief.md`: which video it sampled, each sheet's path and sentences beside their tile numbers, the coverage counts and the reviewer checklist. That brief is what it prints; with `--quiet` it prints one coverage line per lesson and the brief's path instead, so a whole course can be sampled without its sentences passing through the caller. `--jobs` sets how many frames are grabbed at once. It samples; it does not judge.

When the frame audit has recorded the lesson's transitions at this timing, the midpoint of each pan, iris and wipe is sampled too. It appears as a `~` tile after the sentences of the scene it falls in, and as `transitions` and `transitionFrames` in the plan. Run the audit before sampling to get them.

- It refuses a video whose length differs from the lesson's `duration` in `course.json` by more than one frame plus 0.1 s: another lesson's video, or a render made before the narration changed.
- Silent runs default to `review/sentence-end-silent/`, so they never overwrite the final encode's evidence. `--video` samples another file and `--out` writes elsewhere.
- A full run replaces the lesson's plan, frames and sheets, so a renamed or removed scene leaves no stale sheet.
- `--scene` (repeatable) redoes only those scenes and keeps the others in the plan. It refuses when the kept scenes were sampled from another video, or at times `course.json` no longer gives; rerun the whole lesson then.

1. Run it for `all` lessons. Resolve any `unmapped` sentence before review: an unsampled sentence is unreviewed.
2. Split the lessons into groups. One reviewer per group views every sheet against its sentences, using the checklist in each lesson's brief, and records each finding as lesson, scene, time, sentence, what is wrong and what a learner would wrongly conclude.
3. One refuting verifier per group then tries to refute each finding on the full-size frames, or on a short clip around its time when duration matters. A finding is refuted by default; it survives only when the verifier reproduces it and agrees it misleads.
4. Fix confirmed findings in the authored world, not in the review record. Render the affected lessons again (`node production-source/render.cjs <lessonId>`) and run the audit: only a lesson whose picture changed is redrawn and replayed, and its narrated file takes the new picture unchanged. Then rerun `review_frames.py <project> <lessonId> --scene <sceneId>` and re-verify each fix on its new frames from that final encode. Before narration exists, use `--silent-preview` and `--silent` instead; that evidence holds only for the timing it was sampled at, so sample the final encode again once narration has re-timed the lesson.
5. Record coverage honestly in `review/acceptance.json`: lessons and sentences sampled out of the total, findings raised, refuted, confirmed and fixed, and which fixes were re-verified in the final encode. Cite the plan entries behind each claim: only entries with `silent: false` from the final encode count as final-encode verification. One frame per sentence is a sample, so on its own it supports `partial` synchronized viewing (or silent inspection for silent runs), never `completed` continuous viewing.

Defect classes found in real use after a clean geometry audit. Some are now rejected mechanically, as marked; the review still owns the rest and anything the mark does not cover:

- A recurring real person drawn differently across lessons, so they read as different people. (A cast preset cannot be restyled; a person drawn outside the cast can.)
- The fiction badge left on over real facts, or missing on a practice panel with invented people or figures. (Audited in scenes that declare `fiction`.)
- A stale callout from the previous beat that reads as the cause of the next one.
- A camera push that fades part of a counted group: sixteen items shown as eight.
- An on-screen detail that answers a question the narration only asks later.
- A label readable for less than 0.5 s. (The audit rejects a label on screen for under 0.5 s; one held too briefly for its length is still yours to catch.)
- A panel cut by the caption band.
- A reveal firing on an earlier occurrence of its cue word. (A repeated cue word without its occurrence throws.)

When reviewers or verifiers are agents, never truncate item lists into their prompts; a serialised list cut at a character limit silently drops items. Each lesson's brief already holds its sheet paths, sentences and checklist: pass the brief paths, have findings written to files, and check that each agent reports the number of sheets it read.

## Player usability

Use [mobile and accessibility review](player-accessibility.md) for the player and any browser-facing reference material. Record actual responsive, keyboard and assistive-technology coverage separately from media review.

## Delivery and hosting

Provide one unmistakable latest edition. Typical output: player and MP4 archive, captions, transcripts, visual beat sheet, editable production source and a short review record. A separate full local source archive can retain original documents when appropriate; the hosted/player package should exclude them by default. Test archive integrity and link to actual existing deliverables.

For web delivery, inspect the existing source and identity first. Use the hosting skill's current supported source/open/package/publish workflow; do not embed tool credentials, repository IDs, usernames or site URLs in this skill. Preserve access when updating. Native successful deployment state verifies publication; local files alone do not mean the hosted course changed. Report an automatic approval rejection with the specific blocked action and stated reason, without substituting a broader public audience or an indirect upload path.

Sharing is a separate requested operation. Read current access and any external-invite availability before adding a viewer. Preserve the full current allowlist where the tool requires replacement, or use the supported additive operation. Adding an external viewer may send an invitation; do not claim email delivery unless confirmed. Confirm the returned viewer role and provide the ordinary course URL. A request to make a skill does not authorize changing an existing course or messaging a former viewer.

Avoid unneeded external generative-video services. Precise explanatory 2D systems are often better served by editable local graphics. Use another service when it materially meets the brief and is authorized; do not send documents to it merely because it is installed.
