# Project data contract

Use UTF-8 JSON. The helpers reject missing required fields and broken references. Never place service keys, tokens, personal candidate details, or account credentials in these files. The working project remains separate from the hosted export.

## Project and posting

`project.json` is managed by `workflow.py`: schema version, source URL, creation time, stage checkpoints, their artifact fingerprints, and export records. Do not mark stages complete by editing it manually.

`job.json` contains `url`, `status` (`verified` or `unavailable`), `retrievedAt` (ISO 8601 with timezone), `employer`, `title`, and `requirements`. A verified posting needs nonempty requirements. When only supplied posting text exists, use `url: null`, `sourceKind: "supplied-text"` and a private nonempty `sourceNote` describing its origin and limits. This verifies the supplied description, not that a vacancy remains open. The exporter labels this source kind without publishing the private note. Each requirement has a unique `id`, `text`, and `kind` (`responsibility`, `required`, or `preferred`). Add the actual job identifier, location, duration, and a private snapshot path when available. Those are working evidence, not hosting metadata. An unavailable posting needs a `limitation` and cannot satisfy the research checkpoint for a job-specific course.

## Sources and claims

`sources.json` contains `sources` and `claims` arrays. Each source has a unique `id`, `title`, `url` (HTTP/S or null for supplied material), `accessedAt` (dated ISO 8601), and `publish` (boolean). Set `publish` to true only for source links appropriate to the course audience. Null URLs and private supplied documents are never exported as links.

Each claim has `id`, `text`, `kind` (`fact`, `interpretation`, `fiction`, or `unknown`), and `sourceIds`. A factual claim needs at least one existing source. Interpretation should identify its basis; fiction is explicit. The helper checks references, not whether a source proves the sentence. Perform that review using the research methodology. No complete job-description snapshot or private source text enters the player by default.

## Objectives and lessons

`curriculum.json` contains `objectives`, `lessons`, and `exclusions`. Each objective has `id`, `text`, and `requirementIds`. Each lesson has `id`, `title`, `objectiveIds`, and `claimIds`. Each exclusion has `requirementId` and `reason`. Every posted requirement must map to an objective or an explicit exclusion; decide the appropriate depth editorially, not through an automatic coverage percentage. Every objective must be taught in a lesson, and each lesson must name its evidence or fictional/unknown claims.

Runtime `course.json` follows the video starter: title, storageKey, language, dimensions, frame rate, and lessons with `id`, `title`, `goal`, `coverage`, `visual`, `duration`, and `scenes`. The runtime lesson IDs and narration must match the curriculum and manuscript. The helper checks lesson IDs; a human or model content review checks that the manuscript meaning survived adaptation. Preserve any useful `part`, `question`, `options`, `answer`, and `explanation` fields. `answer` is a zero-based option index. Optional `optionFeedback` contains one explanation per option, in the same order; use it to address the selected misconception. Malformed feedback is omitted during export. The general `explanation` remains the fallback. Optional `course.job` stores only public `employer`, `title`, `url`, and `researchedAt`; the exporter derives it from the posting. Sources and source IDs are populated from the evidence map during export.

For new projects, the `narrative-motion-v2` profile also records `narrative-map.json`, `review/editorial.json`, `visual-design.json` and `review/prototypes.json` as specified in [editorial and motion review](editorial-and-motion-review.md). These are working design evidence and are not exported. Prototype media must be inside the project; the review is invalidated when the world, motion library or declared renderer dependencies change. A legacy project's record remains readable, but a substantive revision should adopt the current profile and complete its design evidence.

## Review and delivery

For prerequisite support, optional `course.glossary` contains `{term, definition}` entries. Teach terms where they become consequential in the story; the on-demand glossary is a reminder, not a substitute for the explanation. Only these two text fields are exported, and the player renders them as text.

Optional `course.tagline` is a short authored editorial proposition for the page; `subtitle` develops it. Keep the exact employer/role and research date in the separate job context and the full course title in document metadata. A generic slogan copied across every role is not a meaningful course introduction.

`review/acceptance.json` has `content`, `listening`, `synchronizedViewing`, and `silentInspection` objects. Each has `status` (`completed`, `partial`, `pending`, `unavailable`, or `failed`) and a concrete `coverage` string. Completed listening/viewing additionally names the `reviewer`. Optional `acceptedLimit` records the actual user's acceptance and its scope, not the author's assumption. Any failed review blocks export. Incomplete perceptual review is exported with an explicit review-version label and a concise visible limitation. It must not be described as completed QA.

`delivery.json` is written only after a native hosting tool confirms deployment. It includes `status: "deployed"`, `url`, `provider`, `version`, `audience`, and `packageSha256` from the export manifest. It records the real result, not a constructed URL. The helper checks format and package identity; it cannot independently attest that a hosting service deployed it. Keep hosting source IDs and secrets in the provider's own local state and secret mechanisms.

All paths registered as evidence must be inside the project. Symlinked export assets are rejected. Private projects use unique output paths and separate progress keys.
