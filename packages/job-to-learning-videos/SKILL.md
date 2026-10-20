---
name: job-to-learning-videos
description: Turn a job posting or job URL into a complete sourced video learning course and hosted course page. Use for the full organization-to-role learning journey with narrated explanatory motion, captions, practice questions, and sources. A job link alone requests the complete workflow; a narrow job question does not request video production.
---

# Job to Learning Videos

Take one job link through research, curriculum, writing, visual production, narration, review, and a hosted course. The user should not need to invoke another skill, collect chapters, transfer a document, or type “continue” for each part. Keep the company-first depth of the research method and the semantic motion of the video method.

## Resolve the project and setup

For a new request, read [the workflow contract](references/workflow.md). Create a dedicated project with `python3 <skill-dir>/scripts/workflow.py init <absolute-project> --job-url <url>`. This creates an empty course, not a demonstration lesson. Run `workflow.py preflight` to check local tools without contacting a speech provider. Discover available browsing and hosting capabilities; do not assume this machine has the original author's services or accounts.

Resolve a one-time run profile: narration provider and voice, language, intended audience, hosting destination, and applicable service/spending authorization. Reuse explicit session choices. For a new user, offer a sensible English beginner course, a short voice sample, and private hosting; ask only for a material missing choice or authorization. A job link authorizes the requested course workflow within existing permissions, not an arbitrary paid service or a public audience. Service setup and native tool approvals may still be necessary. Credentials belong in the supported secret store or environment, never project JSON, rendered pages, or this skill.

For an existing project, inspect `project.json`, actual files, and current delivery before changing anything. Use `workflow.py status <project>` to find stale stages. Preserve accepted work, controls, voice choices, and audience. A repair request should rebuild only affected stages.

## Research the actual opportunity

Read [research methodology](references/research/research-methodology.md). Retrieve the complete posting and establish the exact employer, role, location, identifier, responsibilities, qualifications, and appointment duration. Save a dated private working snapshot when permitted; keep it out of the hosted package. Populate `job.json` and `sources.json` using [the data contract](references/project-data.md).

Research the organization's purpose, origins, governance, offerings, constituencies, funding or economics, operating model, and context relevant to this role. Separate sourced fact, interpretation, fiction, and unknowns. A source supports only its actual claims. Prefer primary sources and current facts. Never silently substitute another vacancy or infer that a failed fetch means the job was filled.

When retrieval fails, continue useful company research while trying an available supported retrieval route. Ask for posting text if missing responsibilities prevent the promised role course. Do not present a general role-family course as a verified analysis of the requested opening. Record the gap and resume from that stage when the information arrives.

## Author the full learning journey

Read [chapter structure](references/research/chapter-structure.md), [storytelling](references/research/storytelling-framework.md), and [editorial and motion review](references/editorial-and-motion-review.md). Complete the substantial parent narrative in `manuscript.md` before adapting it into lesson scripts. Automatic continuation replaces the standalone storyteller's wait between parts; it does not shorten those parts. Preserve an explicitly requested part structure. Otherwise let the organization and role determine the structure and duration.

Move through the organization, operating model, real work and systems, hiring evidence, onboarding, and advancement where relevant. Use the posting's seniority and duration. Read [candidate evaluation](references/research/candidate-evaluation.md) for hiring and career content. With only a job link, teach readiness criteria without inventing a learner biography, personal candidacy score, internal hiring sequence, or promotion policy.

Plan objectives and decisions before choosing lesson count. In `curriculum.json`, map each published responsibility and requirement to an objective or an explicit reason for exclusion. Connect objectives to lessons and claims. Keep a consistent fictional cast and quantitative model across the course. Label simulations where they appear. The [historical Axios example](references/research/axios-case-study.md) calibrates narrative depth; its employer claims require fresh verification and its unfinished series does not limit this course's scope.

Keep a `narrative-map.json` linking manuscript chapters, consequential decisions and adapted lessons. Review purpose, supported strategic context, the operating chain, worked investigations, hiring evidence and growing professional responsibility in `review/editorial.json`. Adaptation may consolidate repetition; record what is retained or omitted and why. A requirement tag, topic heading or word count does not establish that the learner was taught the subject. Use plausible alternatives and evidence-based feedback in exercises, with worked reasoning for difficult cases.

For a substantial course, test transfer with changed constraints in the important parts. Use plausible misconceptions rather than obviously absurd distractors, vary correct-answer positions, and explain why a tempting alternative fails under the stated conditions. Keep practice feedback separate from completion and professional readiness. A five-part evidence matrix should point to actual scenes, alternatives, failed hypotheses, consequences and checks; a broad finding that merely praises each part is insufficient review evidence.

## Teach through motion

Read [visual direction](references/visual-direction.md) and [beat-sheet design](references/video/beat-sheet.md), then [production and timing](references/video/production.md) before rendering. Inspect the user's actual reference edition and establish its visual language before authoring a new world. Create sentence-level `visual-beat-sheet/beat-sheet.json` and a readable `beat-sheet.md` before the production pass. Preserve quantities, qualifications, sources, and fiction labels during adaptation.

The bundled canvas world is a mechanical example, not this course's graphics. Author subject-specific worlds in `production-source/world.cjs`; fail visibly for unsupported lessons. Use progressive construction, persistent objects, cause and effect, and camera reframing that reveals relationships. Choose mechanisms appropriate to the topic; do not turn every job into the same transfer diagram or chain of cards. Add retrieval questions with feedback where they test a meaningful decision, not attendance.

Specify visible initial states, triggers, transformations, exceptions and outcomes in `visual-design.json`. A generic instruction to construct/update a concept is insufficient direction for a causal explanation. Before bulk rendering, render and inspect representative mechanism prototypes: include a difficult state change and a transition that previously failed or could mislead. Record exact media, source identity, observations and limitations in `review/prototypes.json`. Use the review to repair the implementation; do not treat completed metadata as visual acceptance. Static context and deliberate pauses are appropriate when they support learning.

Generate only authorized adapted narration. The bundled optional client uses Microsoft's Edge speech service through `edge-tts`; it is not an Azure Speech account integration. Retain a selected voice, check pronunciation and delivery, and do not switch providers or incur new costs without applicable authorization. Drive visual reveals and captions from measured word/sentence boundaries. Changing narration invalidates affected timings, renders, and review.

## Review and deliver

Read [review and delivery](references/video/review-and-delivery.md). Run the source validator, geometry audit, and final media validator. Inspect encoded images, listen to the full narration where possible, watch the synchronized result, and inspect silent mechanisms. Technical checks do not establish factual accuracy, natural speech, or learner comprehension. Record actual coverage and remaining limitations in `review/acceptance.json`. Do not fabricate a completed listening review. A known limit the user explicitly accepts should not cause repeated approval requests.

Use `workflow.py record <project> <stage>` after completing each stage. Checkpointing validates required artifacts and stores fingerprints; it does not perform creative authoring. Upstream changes invalidate later stages. The workflow helper and [data contract](references/project-data.md) define the stage requirements.

Export using `workflow.py export <project> <new-output-directory>`. The exporter validates the complete media and allows only player code, course media, captions, posters, and selected public source metadata. It omits working job snapshots, private source records, audio stems, credentials, and editable production files. Inspect the exported content before uploading it. Preserve a separate editable local project.

Publish the exported static course using an available supported hosting workflow. If Sites is available, read its skill and follow its current source/package/deploy flow. Private hosting is the new-course default; preserve an existing audience. Publication and viewer invitations are separate actions. Local export does not establish deployment. Record the native confirmed URL, version, audience, and package fingerprint in `delivery.json`, then record the delivery stage. If hosting is unavailable, provide the usable local package, state that the hosted result is unfinished, and identify the missing capability.

Return one verified course URL as the main result, with concise coverage and review status. Do not call the course complete while required media or hosting is missing. Keep public skill release separate from a learner's course audience.
