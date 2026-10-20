# Learning Skills

Two Codex skills for understanding organizations through stories and turning source material into narrated visual lessons.

This repository starts as a private development workspace. Changing its visibility to public is a separate owner decision. The initial import preserves the installed skills as of October 20, 2026.

| Skill | Purpose | Entry point |
| --- | --- | --- |
| Company & Role Storyteller | Research an organization and teach its purpose, economics, operations, roles, and career paths through a connected series. A company or job link alone starts a substantial organization-first Part I. | [Instructions](skills/company-role-storyteller/SKILL.md) |
| Continuous Learning Videos | Adapt source material into narrated educational videos using sentence-level visual planning, continuous spatial storytelling, measured timing, and explicit media review. Includes an editable local starter. | [Instructions](skills/continuous-learning-videos/SKILL.md) |

The skills work independently. They can also form a workflow: research and write the learning series, then adapt the approved content into videos. Producing a series does not automatically authorize uploading its text to a speech service or publishing its videos.

## Install and use

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
python3 skills/continuous-learning-videos/scripts/new_project.py /absolute/path/course-project --title "Course title"
```

From that new project's directory:

```sh
npm install --prefix production-source
node production-source/render.cjs all --silent-preview
node production-source/render.cjs posters
node production-source/audit.cjs
```

These commands make a **silent demonstration preview**, not a finished narrated course. See [production and measured timing](skills/continuous-learning-videos/references/production.md) for narration, final rendering, captions, and the player. The [review guide](skills/continuous-learning-videos/references/review-and-delivery.md) distinguishes mechanical checks from listening and synchronized viewing.

## Development and checks

Edit the repository copies; installed copies are separate snapshots. Review and copy a changed skill back to the installation when ready. Generated courses, dependencies, audio, credentials, and local review artifacts do not belong in this repository.

Run the offline checks with Python and Node available:

```sh
python3 scripts/check.py
```

For the rendering check, install the starter's canvas dependency first, then run:

```sh
npm install --prefix skills/continuous-learning-videos/assets/starter/production-source
python3 scripts/check.py --render
```

The rendering check uses a temporary project. GitHub Actions runs the same checks without requesting speech or publishing anything. See [development notes](docs/development-notes.md) for the decisions recovered from earlier sessions and the limits of historical validation.

## Before a public release

Review the complete Git history as well as the current files for private material. Decide on a license before inviting reuse; no open-source license has been selected here. Review the historical Axios example, the personalized Ava voice preference, external service expectations, and behavior on a fresh installation. A successful starter check does not establish teaching quality or validate a finished course.
