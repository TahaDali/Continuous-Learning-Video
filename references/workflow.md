# Complete course workflow

The installed bundle contains the research references, video references, scripts, and starter assets. It does not require the two original skills to be installed. The repository root and release ZIP each contain the complete skill; no separate source template or other skill installation is required.

## Normal path

One job URL initiates the full course after service setup. Give concise progress updates at useful milestones and continue through the authorized work. Ask only when missing information or authorization materially prevents the next action. Do not add an approval gate between every chapter, script, and render.

1. **research:** retrieve the posting, establish its identity, and map supported facts, interpretations, fictional illustrations, and unknowns.
2. **curriculum:** choose learning objectives and lesson boundaries; trace the actual requirements to their teaching or an explicit scope exclusion.
3. **script:** author the full organization-first parent manuscript, map its decisions into adapted narration, and review each planned part. Preserve an explicitly requested part structure; otherwise adapt scope to the job without a fixed length or lesson count.
4. **visuals:** create the readable and machine-readable sentence beat sheets, specify visible mechanism states/transitions, implement the worlds and inspect encoded prototypes before bulk production.
5. **narration:** generate approved narration, align it, and create captions and transcripts. No external request happens during project creation or preflight.
6. **media:** render every final lesson and poster, run the geometry audit, and validate all final video/audio streams and captions.
7. **review:** record actual content review, listening, synchronized viewing, and silent inspection in the acceptance record. Use completed, partial, pending, unavailable, or failed honestly.
8. **package:** export a portable course player. Only explicit export assets belong in the hosted source, not the entire project directory.
9. **delivery:** deploy through the available hosting provider and record its confirmed version, URL, audience, and package hash.

`workflow.py record` requires the previous stages to be current. The status command checks the saved fingerprints and marks descendants stale after an upstream change. The readable beat sheet is regenerated from canonical JSON when visuals and narration are checkpointed. Script and visual-plan fingerprints ignore timing fields that narration legitimately updates; changing their wording or visual design still invalidates downstream work. Re-record from the changed stage after doing the affected work. Fingerprints describe file identity, not truth or comprehension.

New projects use the `narrative-motion-v2` review profile: script recording requires the narrative map and editorial review; visual recording requires a mechanism design and inspected prototype clips matching the authored world. See [editorial and motion review](editorial-and-motion-review.md). These checks establish traceable evidence, not its pedagogical truth. Older project checkpoints remain readable; when revising an older course to this profile, set its `reviewProfile` explicitly and re-record the affected stages after doing the work.

## Learning page

Use the player to present the employer and role, research date, objectives, grouped lessons, videos, optional captions, transcript jump points, sources, and practice questions with explanations. A progress mark means the user completed a lesson; it is not a claim of professional mastery. Keep fictional examples and the independent educational status visible. Verify keyboard access, captions, playback, question feedback, and legibility at mobile and desktop sizes.

## Recovery

A blocked posting may require supplied text. Provider failure should leave usable scripts and authored visuals intact. Keep bounded retries and fail explicitly; never substitute an unauthorized provider or publish silently without narration. If an encoded file or caption fails validation, repair that lesson and invalidate its downstream review/export. If deployment is pending, continue the existing attempt; a second new site is not the default retry.

## Release status

The owner accepted the five private sample courses and approved the combined public release as Continuous-Learning-Video. Each new course retains its own service permissions, audience, review evidence and remaining limits. Passing helper tests does not establish teaching quality or a hosting result.
