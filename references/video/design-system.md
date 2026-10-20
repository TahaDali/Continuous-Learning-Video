# Design system for explanatory motion

Use this when authoring any course world. It gives every course the same typographic hierarchy, motion grammar, camera language and transition logic, so a viewer can follow without effort. The subject's own mechanism, objects and evidence still have to be designed for each lesson; the system supplies how they are staged, not what they are.

Start by studying the worked example:

```bash
python3 scripts/new_project.py /absolute/path/design-demo --design-demo
```

It is a fictional 70-second lesson that uses every template, cue-driven reveals, a travelling camera, an iris, a wipe and documented intentional contacts. It renders and audits clean with estimated timing and after narration re-times it. Replace it for a subject course.

## Components

| File | Role |
| --- | --- |
| `production-source/design.cjs` | Tokens, type roles, easing, narration cues, camera keyframes and an auditable stage with text, sentences, cards, chips, counters, annotations and transitions |
| `production-source/templates.cjs` | Reusable teaching moves: `opener`, `statement`, `carry`, `compare`, `lineStory`, `stepper`, `question`, `progressRail` |
| `production-source/fonts/` | Inter, Instrument Serif and JetBrains Mono under the SIL Open Font License, with their license texts |
| `assets/design-demo/` | The example world, lesson, full beat sheet and scene-scoped overlap rules installed by `--design-demo` |

A world opts in with literal imports, `require('./design.cjs')` and `require('./templates.cjs')`. The renderer and audit then register the bundled fonts, and source discovery adds them to the render identity. The stage keeps the starter's audit contract: text and solid objects register bounds, owners describe containment, and strokes and annotations stay unregistered like `edge()`. `createIllustration(stage)` from `illustrations.cjs` also works on a design stage, so its people, documents and buildings use the system type.

## Principles

1. **One idea per frame.** Hierarchy comes from type roles and scale, not from boxes. Remove a container unless it carries meaning.
2. **Text appears when it is said.** Every on-screen word that repeats narration reveals on its measured word. Display-only text (kickers, axis labels, takeaways) uses a short stagger after the cue that introduces it.
3. **Colour means something.** Ink is structure. Teal is the stable or conserved thing. The accent marks change, attention and corrections. Gold is the moving quantity, the hero object and emphasis. Use one accent per scene.
4. **Focus by dimming, not deleting.** When attention moves, drop the previous element to about 38% opacity so context stays readable. Hand focus over: brighten the next element before dimming the last.
5. **One world, a travelling camera.** Lay related scenes out as regions of one large canvas. Pan between adjacent ideas, push in by no more than 6% for emphasis, and never move the camera without a reason.
6. **Motivated transitions.** Choose the transition by the relationship between scenes:
   - **carry:** the same object continues.
   - **pan:** the next idea sits beside this one.
   - **iris:** the next idea grows from a specific point.
   - **wipe:** the viewer changes mode, for example into practice.
7. **Annotate like a teacher.** A scribble, underline, strike-through or arrow marks the one thing to notice in a beat, timed to the word that names it. Never use more than one at a time.
8. **Numbers behave like quantities.** Values roll through digits and totals stay conserved through motion. The audit checks displayed totals.
9. **Keep the viewer oriented.** The opener's agenda persists as a quiet progress rail in the top band.

Full sentences belong primarily in captions and transcripts. Use the kinetic `statement` for the one claim a lesson hangs on, not for every sentence.

## Tokens and type roles

Colours come from `T`. To add a subject colour (a brand, a map legend, a second series), call `extendTheme({name: '#rrggbb'})` once and use `T.name`. Never write hex literals in a world. Paper scenes use `paper`/`ink`; practice and reflection scenes may use the `night` background with `white` text.

| Role | Face | Size | Use |
| --- | --- | --- | --- |
| `kicker` | Inter Bold, tracked capitals | 15 | Section or column label above a heading |
| `display` | Inter ExtraBold | 88 | Lesson opener title only |
| `headline` | Inter Bold | 44 (statement 56) | Scene title, kinetic claim, question prompt |
| `title` | Inter SemiBold | 32 | Row names, step titles, equations |
| `body` | Inter SemiBold | 30 | Short supporting line |
| `label` | Inter SemiBold | 21 | Object labels, chips |
| `small` | Inter Medium | 17 | Chrome such as the progress rail |
| `accent` / `accentMd` / `accentSm` | Instrument Serif Italic | 70 / 38 / 27 | The qualifying phrase, takeaways and handwritten notes |
| `numeral` / `numeralSm` | Inter ExtraBold / Bold | 58 / 30 | Balances, totals and answers |
| `mono` | JetBrains Mono | 17 | Code, identifiers and computed details |

Override `size` when layout requires it, but do not change faces or tracking per scene. To adopt a user's reference style, edit `T`, `FACES` and `TYPE` in `design.cjs` once for the project. Declare and license any replacement font, and keep the grammar below.

## Motion grammar

| Movement | Duration and easing |
| --- | --- |
| Word reveal (`rise`, `blur`, `ghost`) | 0.35–0.6 s, `E.out` / `E.outExpo` |
| Chip or badge pop | 0.55 s, linear progress through `E.outBack` |
| Focus dim or brighten | 0.5–0.6 s, `E.inOut`, to about 38% |
| Sentence exit before a carry | 0.35 s, `E.out` |
| Carry of a hero object | 0.8–1.2 s, `E.inOut`, changing role and colour at the midpoint |
| Camera pan between regions | 1.0 s, `E.inOut`, motion blur proportional to speed |
| Push-in across a scene | the scene's span, at most 1.06 zoom |
| Iris or wipe | 1.0 s; the iris fills with the accent, then opens the next region |
| Transition window | `[next.start - 0.3, next.start + 0.7]`, inside the closing pause |

## Templates

| Template | Teaching move | Drive it with | Minimum spoken span |
| --- | --- | --- | --- |
| `opener` | Promise and agenda | title, accent and agenda cues | 4.5 s |
| `statement` | The one claim, ghosted, filled as spoken, emphasis highlighted | `cue.phrase` for every word, `exitAt` | 3 s |
| `carry` | Move the emphasised word or number into the next scene | emphasis position from `statement` | — |
| `compare` | Before/after or changed/conserved columns with strikes, arrows and a check | row cues, `focusAt`, takeaway phrase | 6 s |
| `lineStory` | Series that vary against an invariant line | series, invariant and focus cues | 6 s |
| `stepper` | A procedure with a travelling token | one cue per step | 5 s |
| `question` | Retrieval practice with options and a reasoned reveal | prompt phrase, reveal cue | 6 s |
| `progressRail` | Persistent orientation in the top band | scene starts | — |

The subject mechanism, such as a transfer, a gate, a migration or a correction path, is authored in the world with stage primitives. Templates frame it; they do not replace it.

## Cue-driven timing

`narrate.py` rewrites every scene's `start`, `end`, `speechStart`, `speechEnd` and `wordTimings`, so hard-coded seconds break as soon as real narration exists. Compute the timeline once per lesson from scenes and cues:

```js
const cue=createCues(lesson);            // cached per lesson object
cue('transfer','leave');                 // onset of the first "leave" in scene "transfer"
cue('transfer','account',2);             // second occurrence
cue.phrase('check','Moving units changes balances, not the total.',{after:cue('check','still')});
cue.method('claim');                     // 'measured' or 'estimated'
```

Before narration, onsets are estimated across the scene's speech span; afterwards they are the measured word boundaries, with no world change. A missing word throws instead of drifting. Derive camera keyframes, mechanism windows and transitions from scene spans and cues. Keep keyframes ordered when narration compresses a scene. Pass each template its scene `start` and `end`: if the spoken span is shorter than the template's minimum, the frame audit reports a `fit-<template>` invariant failure. Lengthen the narration rather than squeezing the choreography.

Write narration that leaves room for the picture:

- Give a mechanism an establishing sentence before the change.
- Name the change with a distinct verb the world can cue on, such as "leave", "arrive" or "blocked".
- End a scene with a short closing beat so its last reveal can be read before the transition.

Record the template, region, incoming transition, emphasis, focus and trigger words in each beat's `design` object in the beat sheet.

## Audit honesty

- Register every text and solid object. Use `owner` only for true containment.
- Wrap only full-frame transition frames in `S.transition(...)`; the audit reports `transitionFrames` per lesson. Use `S.decor(...)` for chrome, trails, rings and grids that carry no label or solid object. Never use either to hide a collision in a held frame.
- A deliberate contact, such as a quantity crossing a container wall, goes in `intentional-overlaps.json` with a reason. Scope it to a `scene` instead of absolute seconds so it follows re-timed narration.
- Model invariants go through `S.check(id, passed, actual, expected)` or `finish({totalUnits, expectedTotal})`.
- `design_checks.visuals` rejects hex colours and font choices in authored modules of a design-system world. It is a guardrail for literals, not a style review.

## Before bulk rendering

Render the silent preview and audit. Then inspect encoded frames at these moments:

- the opener;
- each statement's highlight;
- the middle of every mechanism;
- the midpoint of each pan, iris and wipe;
- the final frame of every scene.

Check that each reveal lands on its spoken word, that focus moves where the narration points, and that transitions start after the last reveal can be read. Compare against the user's reference if one exists. A clean audit establishes registered geometry and timing fit, not design quality or comprehension.
