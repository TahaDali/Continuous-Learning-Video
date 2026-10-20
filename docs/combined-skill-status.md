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

These tests do not establish the factual accuracy of a real employer course, voice quality, engaging motion design, learner understanding, service availability, or hosted delivery. The earlier Chamber and Axios course acceptance limits remain unchanged. The installed personal skills have not been overwritten by these repository changes.

A local browser spot check of the silent synthetic fixture confirmed the job context, visible review limitation, practice-question feedback, source link and fiction label, and caption-control state. This was a desktop interaction check, not a full mobile accessibility audit, listening review, or synchronized course viewing.

## Remaining before public release

- Run the combined skill from a clean installation on contrasting real job postings, including an internship and an inaccessible-posting recovery case. Capture research, output artifacts, interruptions, and actual completion.
- Expand the authored mechanism examples beyond the single conserved transfer, while allowing bespoke subject-specific worlds. Assess explanation quality rather than counting decorative motion.
- Configure and exercise the intended narration provider with explicit authorization. The optional bundled Edge client is distinct from Azure Speech. Complete perceptual listening and synchronized viewing of representative courses.
- Exercise native private hosting with the exported package, confirm the deployed version, and test mobile and desktop playback, captions, sources, questions, keyboard operation, and resume behavior.
- Validate source support and role coverage editorially, review all public-facing example provenance and repository history, and select a license.

The combined bundle is a usable development draft for agent-driven authoring. It is not yet a validated promise that every job URL automatically yields a production-quality hosted course. A skill coordinates available tools and authored work; the current bundle does not include a general animation compiler, speech-service account, or hosting service.
