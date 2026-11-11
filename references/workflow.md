# Complete course workflow

The installed bundle contains the research references, video references, scripts, and starter assets. It does not require the two original skills to be installed. The repository root and release ZIP each contain the complete skill; no separate source template or other skill installation is required.

## Normal path

One job URL initiates the full course after service setup. Give concise progress updates at useful milestones and continue through the authorized work. Ask only when missing information or authorization materially prevents the next action. Do not add an approval gate between every chapter, script, and render.

1. **research:** retrieve the posting, establish its identity, and map supported facts, interpretations, fictional illustrations, and unknowns.
2. **curriculum:** choose learning objectives and lesson boundaries; trace the actual requirements to their teaching or an explicit scope exclusion.
3. **script:** author the full organization-first parent manuscript, map its decisions into adapted narration, and review each planned part. Preserve an explicitly requested part structure; otherwise adapt scope to the job without a fixed length or lesson count. Then run `workflow.py sync <project> --split`: scene timing estimates, player data and the sentence-cue skeleton of the beat sheet are derived from the scripts, not typed again.
4. **narration:** generate approved narration, align it, and create captions and transcripts. It needs only the script, so do it before the worlds whenever the voice is settled. No external request happens during project creation or preflight.
5. **visuals:** fill the sentence beat sheets, specify visible mechanism states/transitions, implement each lesson's world and inspect encoded prototypes before bulk production.
6. **media:** render every lesson and poster, run the frame audit, and validate all final video/audio streams and captions. Each picture is drawn once; the narrated file copies it.
7. **review:** record actual content review, listening, synchronized viewing, and silent inspection in the acceptance record. Use completed, partial, pending, unavailable, or failed honestly.
8. **package:** export a portable course player. Only explicit export assets belong in the hosted source, not the entire project directory.
9. **delivery:** deploy through the available hosting provider and record its confirmed version, URL, audience, and package hash.

`workflow.py record` requires the stages a stage depends on to be current. Narration and visuals each depend on the script and not on each other: either can be recorded first, and recording one never clears the other. Media needs both. Narrating first is the normal order because worlds are then authored on measured timing and the first full render is the final one; visuals first remains valid when a voice is still being chosen. The status command checks the saved fingerprints and marks descendants stale after an upstream change. The readable beat sheet is regenerated from canonical JSON when visuals and narration are checkpointed. Script and visual-plan fingerprints ignore timing fields that narration legitimately updates; changing their wording or visual design still invalidates downstream work. Re-record from the changed stage after doing the affected work. Fingerprints describe file identity, not truth or comprehension.

New projects use the `narrative-motion-v2` review profile: script recording requires the narrative map and editorial review; visual recording requires a mechanism design and inspected prototype clips matching the authored world. See [editorial and motion review](editorial-and-motion-review.md). These checks establish traceable evidence, not its pedagogical truth. Older project checkpoints remain readable; when revising an older course to this profile, set its `reviewProfile` explicitly and re-record the affected stages after doing the work.

## Keep each piece of work small

A course is long and most of its work is per lesson. These habits keep time and context in proportion to what actually changed.

- **Read for the stage you are in.** Open a reference when its stage begins: the research references for research and the scripts, the visual references for worlds, review and delivery last. Whoever authors one lesson's visuals needs the visual references and that lesson's files, not the research.
- **Decide the course-wide choices once.** The state code, the cast, the part openers and shared mechanisms go into the design brief and one shared module before the first lesson. After that a lesson is one beat-sheet file and one world module, so lessons can be authored in any order.
- **Work per lesson.** Read and edit `visual-beat-sheet/lessons/<lessonId>.json` and `production-source/worlds/<lessonId>.cjs`, not the whole-course files. Check a lesson alone with `node production-source/render.cjs <lessonId> --silent-preview`, `node production-source/audit.cjs --lesson <lessonId>` and `review_frames.py <project> <lessonId> --silent`. These touch only that lesson's files.
- **Delegate lessons when delegation is available and authorized.** Give each worker one lesson or a few: the paths of its two files, the shared module, the design brief and the visual references. Because the per-lesson commands do not touch shared files, workers can run side by side. A worker changes only its own lesson's files and reports back what belongs to shared ones: its mechanism entry for `visual-design.json`, and any narration change it needs. Merge those yourself, then run `workflow.py sync`, the course audit and the checkpoints once. Give workers file paths, not pasted content, and have each report what it changed and what it could not verify.
- **Let unchanged work stand.** The renderer redraws and the audit replays only lessons whose picture dependencies changed, and the validator decodes only files it has not decoded. After a fix, run the ordinary whole-course commands; they do the minimum. Do not re-inspect media that did not change.

## Learning page

Use the player to present the employer and role, research date, objectives, grouped lessons, videos, optional captions, transcript jump points, sources, and practice questions with explanations. A progress mark means the user completed a lesson; it is not a claim of professional mastery. Keep fictional examples and the independent educational status visible. Verify keyboard access, captions, playback, question feedback, and legibility at mobile and desktop sizes.

## Recovery

A blocked posting may require supplied text. Provider failure should leave usable scripts and authored visuals intact. Keep bounded retries and fail explicitly; never substitute an unauthorized provider or publish silently without narration. If an encoded file or caption fails validation, repair that lesson and invalidate its downstream review/export. If deployment is pending, continue the existing attempt; a second new site is not the default retry.

## Release status

The owner accepted the five private sample courses and approved the combined public release as Continuous-Learning-Video. Each new course retains its own service permissions, audience, review evidence and remaining limits. Passing helper tests does not establish teaching quality or a hosting result.
