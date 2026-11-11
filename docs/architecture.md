# Architecture

The repository root is the single installable `continuous-learning-video` skill. `SKILL.md` gives the agent the complete job-to-course contract. The agent performs research, judgment, writing and subject-specific visual authoring. Helpers validate recorded evidence and files; they are not an unattended job-link service.

```text
Posting + authorized source material
  -> dated sources and claims
  -> requirements, objectives and curriculum
  -> parent manuscript and adapted lessons
  -> derived timing estimates, player data and sentence-cue skeleton
  -> authorized measured narration and captions   (either order;
  -> sentence beat sheet and authored visual worlds  narration first is normal)
  -> one encoded picture per lesson, copied into the narrated video
  -> frame/media checks, sentence-end review and actual review
  -> allowlisted static player export
  -> supported hosting result and exact package identity
```

- `references/research/` maintains organization-first research, fictional reasoning and career boundaries.
- `references/video/` maintains visual planning, production and review methods.
- `scripts/workflow.py` manages nine checkpoints and invalidates dependent stages when relevant sources change. Narration and visuals both depend on the script and not on each other.
- `scripts/sync_plan.py` (`workflow.py sync`) derives estimated scene timing, player data and the beat-sheet skeleton from `course.json`, keeps authored visual fields across script changes, and maintains one working beat-sheet file per lesson.
- `scripts/design_checks.py` checks the narrative/visual evidence contract and local video prototypes, and rejects hard-coded colours and fonts in design-system worlds.
- `scripts/new_project.py` creates an empty authoring project; `--demo` explicitly selects the mechanical example and `--design-demo` the design-system example.
- `assets/starter/` supplies the editable renderer, the shared design system, narration helper, local server and static player. The design system has three modules and the fonts:
  - `design.cjs`: meaning tokens, a course-defined state code, tiered type roles, cue, camera and spoken-number helpers, and a stage whose type-floor, edge and word-budget checks report through the frame audit.
  - `templates.cjs`: teaching templates and the top-band chrome.
  - `illustrations.cjs`: glyphs, people with faces and a course-defined cast.
  - Bundled OFL fonts.
- `scripts/review_frames.py` samples each narration sentence's end state from an encoded lesson into time-stamped contact sheets and a plan for the sentence-end review. It samples; reviewers judge.
- `assets/design-demo/` holds the fictional design-system world, lesson, beat sheet and overlap rules copied by `--design-demo`.
- `scripts/validate_project.py` checks text/timing/captions and optionally full media decoding. A final file whose bytes an earlier passing run decoded is not decoded again.
- `assets/starter/production-source/lesson-scope.cjs` gives each lesson a scope: its own module (`worlds/<lessonId>.cjs`, else `world.cjs`), a view of the course without other lessons' scenes and timing, and an identity of everything its picture depends on. `render.cjs` draws a lesson's picture once and copies that stream into the narrated video; `audit.cjs` replays a lesson only when its identity changed. The audit also rejects labels on screen for under half a second and checks the fiction badge against scenes that declare `fiction`.
- `scripts/build_skill.py` builds only reviewed `skill-files.json` paths and can create a deterministic checksum ZIP outside the source tree.

Authored worlds fail for unsupported lessons. Static import discovery records supported local render dependencies without executing the world, but rendering still executes trusted code. Hashes bind identity; they do not prove source accuracy, actual hosting, speech quality or learning outcomes.

Working research snapshots, private source records, audio stems, review evidence and editable production code stay in the local course project. Hosted exports contain only allowed player/media fields and selected source links. Retained content still needs semantic privacy and rights review. Repository visibility and course audiences are independent.
