# Architecture

The repository root is the single installable `continuous-learning-video` skill. `SKILL.md` gives the agent the complete job-to-course contract. The agent performs research, judgment, writing and subject-specific visual authoring. Helpers validate recorded evidence and files; they are not an unattended job-link service.

```text
Posting + authorized source material
  -> dated sources and claims
  -> requirements, objectives and curriculum
  -> parent manuscript and adapted lessons
  -> sentence beat sheet and authored visual worlds
  -> authorized measured narration and captions
  -> encoded videos, geometry/media checks and actual review
  -> allowlisted static player export
  -> supported hosting result and exact package identity
```

- `references/research/` maintains organization-first research, fictional reasoning and career boundaries.
- `references/video/` maintains visual planning, production and review methods.
- `scripts/workflow.py` manages nine checkpoints and invalidates later stages when relevant sources change.
- `scripts/design_checks.py` checks the narrative/visual evidence contract and local video prototypes, and rejects hard-coded colours and fonts in design-system worlds.
- `scripts/new_project.py` creates an empty authoring project; `--demo` explicitly selects the mechanical example and `--design-demo` the design-system example.
- `assets/starter/` supplies the editable renderer, the shared design system (`design.cjs`, `templates.cjs`, bundled OFL fonts), narration helper, local server and static player.
- `assets/design-demo/` holds the fictional design-system world, lesson, beat sheet and overlap rules copied by `--design-demo`.
- `scripts/validate_project.py` checks text/timing/captions and optionally full media decoding.
- `scripts/build_skill.py` builds only reviewed `skill-files.json` paths and can create a deterministic checksum ZIP outside the source tree.

Authored worlds fail for unsupported lessons. Static import discovery records supported local render dependencies without executing the world, but rendering still executes trusted code. Hashes bind identity; they do not prove source accuracy, actual hosting, speech quality or learning outcomes.

Working research snapshots, private source records, audio stems, review evidence and editable production code stay in the local course project. Hosted exports contain only allowed player/media fields and selected source links. Retained content still needs semantic privacy and rights review. Repository visibility and course audiences are independent.
