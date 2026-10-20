# Learning Skills

A combined Codex skill for turning a job URL into a sourced, narrated video learning course, built from the organization-first storyteller and continuous-video production methods.

This repository starts as a private development workspace. Changing its visibility to public is a separate owner decision. The initial import preserved the installed skills as of October 20, 2026. The combined workflow completed an initial job-to-private-course trial and now has five contrasting courses in private design review; see [current scope and remaining release work](docs/combined-skill-status.md).

| Skill | Purpose | Entry point |
| --- | --- | --- |
| Company & Role Storyteller | Research an organization and teach its purpose, economics, operations, roles, and career paths through a connected series. A company or job link alone starts a substantial organization-first Part I. | [Instructions](skills/company-role-storyteller/SKILL.md) |
| Continuous Learning Videos | Adapt source material into narrated educational videos using sentence-level visual planning, continuous spatial storytelling, measured timing, and explicit media review. Includes an editable local starter. | [Instructions](skills/continuous-learning-videos/SKILL.md) |

The skills work independently. They can also form a workflow: research and write the learning series, then adapt the approved content into videos. Producing a series does not automatically authorize uploading its text to a speech service or publishing its videos.

## Combined skill draft

The intended user experience is one installed **`$job-to-learning-videos`** skill: paste a job URL, then receive a hosted course with videos, captions, transcripts, sources, and practice questions. Narration and hosting need one-time service setup and applicable authorization. An inaccessible posting may require its text.

Build the self-contained skill folder from the repository root, choosing a new output path:

```sh
python3 scripts/build_skill.py --output /absolute/path/job-to-learning-videos
```

Add `--archive /absolute/path/job-to-learning-videos.zip` to create a reproducible ZIP containing the assembled folder, license, third-party notices, and a per-file SHA-256 manifest. Both outputs must use new paths. The builder rejects included symlinks and excludes dependency directories and environment files.

Copy that complete generated folder into your personal Codex skills directory, reviewing any existing installation before replacement. It contains both methods and all bundled helpers; the original two skills do not need to be installed. The `packages/job-to-learning-videos/` folder is the source template and must be assembled before installation.

Example invocation after installation:

```text
$job-to-learning-videos https://example.org/company/jobs/position
```

The agent performs research and creative authoring. The scripts maintain project evidence and checkpoints, validate media, and export the player; they do not independently research jobs, create bespoke animation, or deploy a site. Hosted completion requires a real successful hosting result. See the [entry point](packages/job-to-learning-videos/SKILL.md) and [workflow contract](packages/job-to-learning-videos/references/workflow.md).

## Original standalone skills

Clone this repository, then copy either complete folder from `skills/` into your personal Codex skills directory. In the environment where these skills were developed, that directory is `~/.codex/skills/`. Keep the folder name and all its references, scripts, assets, and metadata together. Review and back up an existing installation before replacing it.

Example prompts:

```text
$company-role-storyteller Analyze this organization or job: [name or URL].
```

```text
$continuous-learning-videos Turn the attached source material into narrated educational videos.
```

Follow the instructions in the selected skill. For the storyteller, current employer claims require current research; its Axios reference is a historical teaching example. For videos, the starter demonstrates a mechanism and must be adapted to the actual subject.

## Video starter

The starter needs Python 3.10+, Node.js, FFmpeg/FFprobe, and the canvas dependency declared in its `production-source/package.json`. The optional narration helper also needs `edge-tts` with compatible word-boundary support. Speech generation sends adapted narration to Microsoft and requires authorization for the material being processed.

From the repository root, create a new project outside this repository:

```sh
python3 skills/continuous-learning-videos/scripts/new_project.py /absolute/path/course-project --title "Course title" --demo
```

From that new project's directory:

```sh
npm install --prefix production-source
node production-source/render.cjs all --silent-preview
node production-source/render.cjs posters
node production-source/audit.cjs
```

These commands make a **silent demonstration preview**, not a finished narrated course. See [production and measured timing](skills/continuous-learning-videos/references/production.md) for narration, final rendering, captions, and the player. The [review guide](skills/continuous-learning-videos/references/review-and-delivery.md) distinguishes mechanical checks from listening and synchronized viewing.

Omit `--demo` for an empty authoring project. Its world refuses to draw until the subject's scenes are implemented. The combined job workflow always starts this way; it cannot silently render the mechanical example for a new role.

## Development and checks

Edit the repository copies; installed copies are separate snapshots. Review and copy a changed skill back to the installation when ready. Generated courses, dependencies, audio, credentials, and local review artifacts do not belong in this repository.

Run the offline checks with Python and Node available:

```sh
python3 scripts/check.py
python3 -m unittest discover -s tests -v
node tests/player-contract.test.cjs
```

For the rendering check, install the starter's canvas dependency first, then run:

```sh
npm install --prefix skills/continuous-learning-videos/assets/starter/production-source
python3 scripts/check.py --render
```

The rendering check uses a temporary project. GitHub Actions runs the same checks without requesting speech or publishing anything. See [development notes](docs/development-notes.md) for the decisions recovered from earlier sessions and the limits of historical validation.

## Before a public release

Review the complete Git history as well as the current files for private material. The private candidate proposes [MIT](LICENSE), subject to the owner's final release approval; [third-party notices](THIRD_PARTY_NOTICES.md) define its provenance boundary. Review the historical Axios example, voice preference, external service expectations and behavior on a fresh installation. See [supported environments](docs/supported-environments.md). A successful starter check does not establish teaching quality or validate a finished course.
