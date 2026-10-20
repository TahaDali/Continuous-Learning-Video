# Review and delivery

## Composition and timing

Inspect beginnings, endings and intermediate states. Check moving labels, full glyph extents, camera zoom, temporary copies, object travel, foreground masks and caption space. A clear end frame does not establish a clear transition.

The bundled audit replays every output-frame timestamp and checks visible registered object/label intersections and label safe zones in screen coordinates. Fully offscreen actors are ignored, and actors can cross the clipped viewport on entrance or exit. Delay labels until readable. It records flagged frame ranges, a representative PNG, declared intentional pairs and source hashes. Its result is a geometric screen, not a claim that a human inspected every frame. New rendering code must register its extents; unregistered strokes cannot be certified by this audit.

Intentional overlap rules are narrow records in `intentional-overlaps.json`: exact lesson ID, exact stable object IDs, bounded start/end times and an educational reason. An intentional stack, contained label or emerging copy can be legitimate. Do not exempt all documents or an entire lesson. Examine each exemption's intermediate encoded frames. Report the accepted pairs alongside zero unresolved findings; do not hide them in a pass count.

Fix collisions through stable positions and choreographed timing. Separate label placement from actor construction where useful, stage reveals, route transfers through actual gaps and keep connectors behind foreground objects. Reserve space for captions, but also check actual browser/native caption rendering because font metrics and controls can differ. Do not solve crowding by making essential type unreadably small.

## Review layers

1. Validate source coverage and conceptual invariants: conserved quantities, consistent units, independent states, honest uncertainty, permissions and exceptions.
2. Run geometry checks at the output rate, inspect flagged intermediate frames and inspect encoded contact sheets covering every lesson. Add purpose-specific checks for the mechanism, such as conservation including in-flight amounts.
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

## Delivery and hosting

Provide one unmistakable latest edition. Typical output: player and MP4 archive, captions, transcripts, visual beat sheet, editable production source and a short review record. A separate full local source archive can retain original documents when appropriate; the hosted/player package should exclude them by default. Test archive integrity and link to actual existing deliverables.

For web delivery, inspect the existing source and identity first. Use the hosting skill's current supported source/open/package/publish workflow; do not embed tool credentials, repository IDs, usernames or site URLs in this skill. Preserve access when updating. Native successful deployment state verifies publication; local files alone do not mean the hosted course changed. Report an automatic approval rejection with the specific blocked action and stated reason, without substituting a broader public audience or an indirect upload path.

Sharing is a separate requested operation. Read current access and any external-invite availability before adding a viewer. Preserve the full current allowlist where the tool requires replacement, or use the supported additive operation. Adding an external viewer may send an invitation; do not claim email delivery unless confirmed. Confirm the returned viewer role and provide the ordinary course URL. A request to make a skill does not authorize changing an existing course or messaging a former viewer.

Avoid unneeded external generative-video services. Precise explanatory 2D systems are often better served by editable local graphics. Use another service when it materially meets the brief and is authorized; do not send documents to it merely because it is installed.
