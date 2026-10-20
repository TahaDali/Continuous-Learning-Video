# Combined skill development status

October 20, 2026. The intended product is one installed Codex skill: a job URL starts research and delivers a hosted narrated video learning course. The GitHub repository remains private. Course hosting defaults to private separately from repository visibility.

## Implemented in the private draft

The new `job-to-learning-videos` entry point explicitly requests the complete workflow, overrides the standalone storyteller's chapter-by-chapter chat pacing for course production, and preserves substantial organization-first explanations. It routes to research, curriculum, narrative, video, and review guidance and requires only one installed skill bundle.

The repository maintains the original research and video modules. `scripts/build_skill.py` assembles their references, production helpers, player, and assets with the combined entry point into a self-contained folder. This avoids maintaining copied renderer implementations in two source locations. Installing the unassembled source template is unsupported.

`workflow.py` initializes an empty job-course project, reports local prerequisites without speech requests, validates the evidence and requirement-to-objective maps, records stage fingerprints, detects upstream changes, and exports an allowlisted player package. Research evidence, private source records, arbitrary course metadata, original posting snapshots, narration stems, and production source stay outside the hosted export. An export manifest identifies the exact packaged files. A delivery record must refer to that package; editing the package invalidates that match. Deployment still requires a successful native hosting-tool result.

The player now supports job context, learning objectives, lesson sources and evidence categories, optional practice questions with explanations, and visible review-version limitations. Existing video controls, caption toggling, transcript jumps, downloads, and progress are retained.

The validation defects demonstrated in review have been corrected: comparisons retain signs, decimals, currencies and percent symbols; word-source alignment checks significant characters; sentence cues must be ordered and non-overlapping; measured sentence bounds must match their words; final audio and video stream durations are checked independently. Missing source-coverage notes are rejected. Reports distinguish text/beat coverage from factual source verification. Project generation excludes dependency folders, cache files, and environment files. Regenerated narration also regenerates its decoded PCM rather than depending only on timestamps.

## Verification coverage

Regression tests use explicitly synthetic fixtures and silent PCM; they make no speech, research, or hosting requests. They exercise changed quantities, missing signs, permitted sentence punctuation, overlapping cues, missing coverage, complete and truncated audio, isolated skill assembly, missing upstream stages, changed research, uncovered requirements, export privacy, and changed-package detection. The 12-second mechanical visual example is separately rendered, audited at all 288 output-frame timestamps, and decoded.

These synthetic tests do not establish factual accuracy, voice quality, engaging motion design, learner understanding, service availability, or hosted delivery. A separate real Axios trial is now recorded below. Earlier course acceptance limits remain unchanged. The installed personal skills have not been overwritten by these repository changes.

A local browser spot check of the silent synthetic fixture confirmed the job context, visible review limitation, practice-question feedback, source link and fiction label, and caption-control state. This was a desktop interaction check, not a full mobile accessibility audit, listening review, or synchronized course viewing.

## Real job-to-private-course trial

The combined bundle was exercised on Axios Staff Software Engineer posting 8229298 on October 20, 2026. The resulting owner-private Site contains 18 narrated lessons in six sections, 30:35 of measured runtime, captions, transcripts, lesson sources, and practice questions. Research maps 32 posting requirements to 18 objectives. All workflow stages, including package identity and confirmed private deployment, are recorded. The authenticated desktop browser played a captioned video from the deployed Site. Access remained one owner, zero groups and zero external visitors.

The run found and fixed stale readable timing sheets, false upstream invalidation after measured timings, text wrapping and shape-interior collisions, stale audit screenshots, insufficient speech-failure context, and exported-player preview support. Fifteen regression tests pass. All 18 final media files decode and pass duration checks; all 44,052 registered output-frame timestamps pass the geometry audit without overlap exemptions. Source and actual encoded-frame review remain distinct from that mechanical audit.

Full perceptual listening is unavailable in this review environment. Full synchronized viewing, complete silent viewing, mobile-device checks and learner testing remain pending. The hosted page visibly identifies itself as a review edition. See the [sanitized trial report](e2e-axios-8229298.md) for exact coverage and limitations; private course media and Site identity are kept outside this repository.

## Remaining before public release

- Run from a clean machine or installation with contrasting roles, including an internship and an inaccessible-posting recovery case. This trial reused working local rendering and speech dependencies.
- Complete full perceptual listening and synchronized viewing of the real course, then correct any pronunciation, pacing, timing or instructional problems found. The speech endpoint required a cached retry during this run.
- Assess whether the 18 authored graphical mechanisms explain the subject without narration. Complete silent viewing and learner comprehension checks; geometry and frame samples cannot establish this.
- Test mobile-device playback, fullscreen diagram legibility and a full accessibility pass. Desktop navigation, captions, transcript jumps, source presentation, question feedback, keyboard activation and saved completion were spot checked.
- Review example provenance and complete repository history, choose a license, and specify supported tool/service environments before promising reliable job-link-only completion to new users.

The combined bundle is a usable private development draft with one confirmed real hosted trial. It is not yet a validated promise that every job URL automatically yields a production-quality hosted course. A skill coordinates available tools and authored work; the current bundle does not include a general animation compiler, speech-service account, or hosting service.
