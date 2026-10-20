# Combined skill development status

## Current private release candidate

October 20, 2026. The combined skill has produced five complete illustrated review courses: 154 chapters and approximately 399 minutes of measured narrated video. All five current editions are privately hosted for owner review. The repository remains private, and course audiences remain private separately. Neither completion nor technical review constitutes the owner's final acceptance or permission for public release.

| Case | Chapters | Authored visual focus |
| --- | ---: | --- |
| Axios Staff Software Engineer | 45 | Revision races, service boundaries, incidents, rollout decisions and growth evidence. |
| Figma product design internship | 25 | Interface behavior, collaborative design decisions, evidence and handoff. |
| Mill hardware/product design engineering internship | 27 | Physical fit, tooling economics, assembly, measurement and variation. |
| Wikimedia financial partnering | 25 | Investment choices, capacity, cash and expense timing, forecasts and variance. |
| GitLab UK public-sector major account sales | 32 | Buying groups, evidence, procurement, account decisions and adoption. |

Each course retains a substantial five-part organization-to-role narrative, sourced research, a requirement-to-learning map, measured narration, captions, transcripts, lesson sources and practice with explanatory feedback. Teaching examples and invented quantities are labeled as fiction rather than employer internal knowledge. The illustrated scenes use recognizable subject artifacts, persistent people and context, and changes that explain relationships. The private review records identify specific improvements and remaining uncertainties against the original Axios Salesforce reference.

## Reusable workflow

One installed `$job-to-learning-videos` skill accepts a job URL and requests the full course workflow. Narration and hosting require supported services, setup and authorization for the current material. An inaccessible vacancy requires a verified recovery source or supplied posting text. The agent performs research and creative authoring; the scripts do not independently research jobs, invent subject-specific animation or deploy a site.

`scripts/build_skill.py` assembles the combined entry point, both methods, references, production helpers and player into a self-contained folder. It rejects included source symlinks and a symlink output, excludes dependencies and environment files, and can generate a reproducible ZIP with a per-file SHA-256 manifest. Installing the unassembled source template is unsupported.

New job projects begin with an unimplemented world that refuses to render until authored. The mechanical example is available only through an explicit `--demo`. Transitive supported local CommonJS imports participate in source freshness checks; unsupported dynamic or alternate loaders fail explicitly. Other filesystem inputs need a declared source manifest. An illustrated helper library supports authoring but does not substitute for a subject-specific world.

`workflow.py` validates evidence and learning maps, records stage fingerprints, invalidates downstream stages after source changes, and exports an allowlisted player package. Raw research, original posting snapshots, private source records, narration stems and production code remain outside the hosted export. A delivery record must match the exact exported package, and hosted completion requires an actual successful native hosting result. Authorized public-facing text and assets still need review before export; an allowlist cannot infer their meaning or rights.

The player provides a compact editorial opening, wide video, grouped course navigation, duration and progress state, captions, transcripts and downloads, lesson sources, practice feedback and an optional glossary. Seeking recovery uses only the active same-origin chapter and releases it on chapter changes. Progress reset is scoped and confirmable. Course review limitations remain visible.

## What was verified

The current core passes **43 Python regressions and 13 player contracts**. The explicit 12-second silent mechanical example is rendered, audited at all **288 output-frame timestamps**, and decoded. Tests cover workflow, media, packaging, export privacy, recovery and state-invalidation behavior. They use synthetic fixtures without making speech, research or hosting requests.

The real cases add public-source research, substantial authored manuscripts, actual speech and measured word timing, caption and media checks, source-bound prototypes, all-output-timestamp registered geometry checks, and a bounded audit of finite numeric Canvas method arguments. Selected actual encoded states and transitions were inspected, defects were repaired, and before/after evidence was preserved. Intentional object contacts are documented where appropriate. A positive video-stream probe establishes a finite-duration video stream and usable dimensions; full decoding and perceptual acceptance require separate checks. Registered bounds and numeric-operation checks do not certify every glyph, raster effect, relationship or readable composition.

Independent review also addressed practice-choice wording, alignment with the question and explanation, and answer-length cues. These editorial checks do not establish item difficulty or learning effectiveness. Source/pixel comparisons preserve the relationship between current course metadata, source revisions and earlier encoded media; unchanged pixels do not prove teaching quality.

Isolated assembled installations, a fresh local canvas dependency installation and Linux CI were exercised. Desktop browser interaction and responsive/keyboard checks add bounded player evidence. See [supported environments](supported-environments.md) for exact setup coverage. Private reports, source snapshots, generated media and hosting identifiers remain outside the repository and installation bundle.

## Review limits and owner decisions

Full-course independent listening, synchronized viewing and complete silent viewing have not been completed as acceptance reviews. Selected encoded-frame inspection cannot replace those reviews. Physical mobile-device checks, a true screen-reader audit and learner comprehension studies remain incomplete. No blanket accessibility, pronunciation, human-voice realism or learning-outcome certification is claimed. Windows and a clean physical second machine remain untested.

The owner must review the final private editions and decide whether these disclosed limits are acceptable before approving a public release. The proposed MIT scope, adapted historical example provenance, third-party material rights and external service terms also require owner review; the privacy/provenance assessment is not legal clearance. Repository visibility and course audience changes require separate explicit decisions.

## Historical evidence

The first Axios Staff trial contained 18 lessons and approximately 31 minutes. It demonstrated the job-to-private-hosting pipeline but compressed the requested narrative. Its [sanitized trial report](e2e-axios-8229298.md) remains historical evidence, with its original review limits.

A later five-part revision restored narrative depth, but the owner rejected its visual direction. Reference-led redesign then replaced generic diagrams with authored illustrated worlds and checked encoded transitions across the five current cases. Earlier rejected graphics and technical passes are retained privately as history; their pass counts and acceptance status do not describe the current editions. The initial import and method decisions are summarized in [development notes](development-notes.md).
