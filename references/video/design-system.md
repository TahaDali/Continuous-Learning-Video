# Design system for explanatory motion

Use this when authoring any course world. It gives every course the same typographic hierarchy, colour meanings, motion grammar, camera language and transition logic, so a viewer can follow without effort. The subject's own mechanism, objects and evidence still have to be designed for each lesson; the system supplies how they are staged, not what they are.

Start by studying the worked example:

```bash
python3 scripts/new_project.py /absolute/path/design-demo --design-demo
```

It is a fictional lesson of about 72 seconds. It uses cue-driven reveals, a travelling camera with a reframing push, an iris, a wipe, a state code, spoken numbers, callouts, a ledger readout, a recurring cast member who speaks, fiction badge windows, a practice question with a picture, and documented intentional contacts. It renders and audits clean with estimated timing and after narration re-times it. Replace it for a subject course.

## Components

| File | Role |
| --- | --- |
| `production-source/design.cjs` | Meaning tokens, the course's state code, type roles with tier floors, easing, narration cues, spoken numbers, focus and camera helpers, and an auditable stage. The stage registers text and solids and enforces the type, edge and word checks below. |
| `production-source/templates.cjs` | Reusable teaching moves: `opener`, `partOpener`, `sectionHead`, `statement`, `carry`, `compare`, `lineStory`, `stepper`, `readout`, `stateKey`, `question`, `progressRail` and `fictionBadge`. |
| `production-source/illustrations.cjs` | People with faces (`figure`), a course-defined cast (`defineCast`, `cast`), and documents, browsers, phones, envelopes, buildings and clocks (`createIllustration`). |
| `production-source/fonts/` | Inter, Instrument Serif and JetBrains Mono under the SIL Open Font License, with their license texts. |
| `assets/design-demo/` | The example world, lesson, full beat sheet and scene-scoped overlap rules installed by `--design-demo`. |
| `scripts/review_frames.py` | Samples each narration sentence's end state into contact sheets for the [sentence-end review](review-and-delivery.md#sentence-end-review). |

A world opts in with literal imports: `require('./design.cjs')`, `require('./templates.cjs')` and, for people, `require('./illustrations.cjs')`. The renderer and audit then register the bundled fonts, and source discovery adds them to the render identity.

The stage keeps the starter's audit contract:

- Text and solid objects register bounds.
- Owners describe containment.
- Strokes, rules, hatching and annotations stay unregistered, like `edge()`.

`createIllustration(stage)` also works on a design stage, so its glyphs use the system type.

## Principles

1. **One idea per frame.** Hierarchy comes from type roles and scale, not from boxes. Remove a container unless it carries meaning. At most 24 content words are on screen at once.
2. **Text appears when it is said.** Every on-screen word that repeats narration reveals on its measured word, not on an earlier occurrence of the same word. Display-only text (kickers, axis labels, takeaways) uses a short stagger after the cue that introduces it.
3. **Each colour means one thing.** The highlighter (`signal`) marks only what is being spoken about now. Red (`wrong`) marks only what is wrong, blocked or rejected. Green (`good`) marks only what is correct or conserved. Violet (`fiction`) is only the fiction badge. The accent marks change and attention annotations. A quantity's condition is shown by the course's state code, never by a meaning colour.
4. **Focus by dimming, not deleting.** When attention moves, drop the previous element to about 30–40% opacity so context stays readable. Hand focus over: brighten the next element before dimming the last.
5. **One world, a travelling camera.** Lay related scenes out as regions of one large canvas.
   - Pan between adjacent ideas.
   - Drift across a scene with a slow push of at most 1.06. Template defaults leave room for a centred push of only 1.03; push further only with their content kept further inside or their labels faded first.
   - Reframe onto a detail with `fitCamera`, after fading whatever the push would carry off frame.
   - Never move the camera without a reason.
6. **Motivated transitions.** Choose the transition by the relationship between scenes:
   - **carry:** the same object continues.
   - **pan:** the next idea sits beside this one.
   - **iris:** the next idea grows from a specific point.
   - **wipe:** the viewer changes mode, for example into practice.

   Iris and wipe paint the full frame.
7. **Annotate like a teacher.** A scribble, underline, strike-through, arrow or highlighter marks the one thing to notice in a beat, timed to the word that names it. Never use more than one at a time. The highlighter retracts when the narration moves on.
8. **Numbers behave like spoken quantities.** A figure appears on its spoken word and never shows a value the narrator is not saying. Totals stay conserved through motion, and the audit checks displayed totals.
9. **Keep the viewer oriented.** The opener's agenda persists as a quiet progress rail in the top band. The fiction badge sits on the same line, on the right. Nothing else goes in the top band.
10. **Recurring things look the same everywhere.** A course defines its state code, its recurring people and its part openers once, and every lesson reuses them.

Full sentences belong primarily in captions and transcripts. Use the kinetic `statement` for the one claim a lesson hangs on, not for every sentence.

## Colour

Colours come from `T`. Paper scenes use `paper`/`ink`. Practice and reflection scenes may use the `night` background (`createDesignStage(g, course, {background: 'night'})`) with `white` text; `S.night` is then true.

| Token | Meaning | Defaults that use it |
| --- | --- | --- |
| `ink`, `inkSoft`, `mute`, `rule` | Structure: type, outlines, secondary type, dimmed marks, hairlines | `strike()` (ink: replaced, not wrong) |
| `teal` | Secondary ink: kickers, decks and a stable reference such as a total | template kickers, `carry` arrival |
| `accent` / `accentSoft` | Change and attention annotations; the iris disc | `scribble()`, `underline()`, `iris()` |
| `signal` / `signalSoft` | **Only** what the narration is speaking about now: the highlighter | `marker()`, `markText()`, sentence marks, `callout({mark})` |
| `wrong` / `wrongSoft` | **Only** wrong, blocked or rejected | the strike over a wrong `question` option |
| `good` / `goodSoft` | **Only** correct or conserved | the conserved check in `compare` |
| `fiction` / `fictionInk` | **Only** the fiction badge (violet block, white type) | `fictionBadge` |
| `blue`, `blueSoft`, `goldInk` and other base tokens | Available for categories and for state colours | — |

Rules for using them:

- `signal` has the same value as the original `gold`, and `signalSoft` as `goldSoft`. Treat both gold tokens as the highlighter: never use them for a fill, a region, a state or a moving object.
- Pass `T.wrong` to `strike()` only when the struck thing is wrong. A replaced value keeps the ink strike.

To add a subject colour (a brand, a map legend, a second series), add it once in the project's copy of `design.cjs`, either in `T` or with `extendTheme({name: '#rrggbb'})`, and use `T.name`. `design_checks` rejects hex literals and font choices in every authored module, so a world never writes a colour literal.

## The course's state code

A course defines once what its quantities can *be*: a parcel planned, shipped or delivered; a book on the shelf, lent or overdue. Every lesson that moves one of them reuses that code. Call `defineStates` once, at module scope:

```js
const {T,defineStates,stateOf,STATES}=require('./design.cjs');
defineStates({held:{color:T.blue,soft:T.blueSoft,label:'Held'},transit:{color:T.goldInk,label:'In transit',treatment:'hatched'}},
  {aliases:{moving:'transit'}});
```

What `defineStates(spec, {aliases})` does:

- Each state becomes the tokens `T[name]` and `T[name+'Soft']`. A missing `soft` is derived as an 85% mix toward white.
- `treatment` is `'solid'` (the default) or `'hatched'`. Hatched means possible, planned or not yet: hatching inside a dashed outline, never a solid fill.
- `label` defaults to the capitalised name. `meaning` is optional text.
- It throws, before writing anything, on any of these:
  - a redefined state or alias;
  - a name that is already a token;
  - a name that does not match `/^[a-z][A-Za-z0-9]*$/`;
  - a colour that is not `#rrggbb`;
  - a colour or soft colour equal to `signal`, `wrong`, `good` or `fiction` (or their soft colours);
  - two states with the same colour and the same treatment, which a viewer could not tell apart (a hatched and a solid state may share a colour).
- Because worlds cannot contain hex literals, a world passes existing tokens. `T.gold` is refused because it equals `signal`.
- `STATES` is the live registry: worlds read it, and only `defineStates` writes it.
- `stateOf(name)` resolves an alias and throws for an unknown state.

Drawing a state:

| Call | Draws |
| --- | --- |
| `S.stateBox(id, state, x, y, w, h, {p, owner, register, outline, weight, gap, dash, alpha})` | A box in the state's treatment. `p` fills it left to right while the outline stays whole. The outline is ink on paper and white on night. `register: false` (or no id) draws it as decor. |
| `S.swatch(id, state, x, y, {size: 26, owner, register, p})` | A legend square. `(x, y)` is its left edge and vertical centre. |
| `S.hatch(x, y, w, h, {color, gap: 9, width: 1.6, alpha})` | Unregistered diagonal hatching. Use it, for example, inside a travelling token in a hatched state. |
| `tpl.stateKey(S, t, {items: [{state, label, at}]})` | Teaches the code where each state first appears. |

Text keeps its role colours. Put a swatch beside a key instead of colouring the words.

## Type tiers and roles

You pick a role and the system owns the face and tracking. Every role belongs to a tier with a floor (`FLOOR`):

- **content: 28 px.** Anything that carries meaning.
- **tertiary: 24 px.** Units, axis ticks, kickers and glyph-internal IDs.
- **chrome: 18 px.** The progress rail and the fiction badge only.

`role(name, over)` never returns a size below its tier's floor: a smaller `over.size` is raised to the floor. `floorOf(role)` gives the floor.

| Role | Face | Size | Tier | Use |
| --- | --- | --- | --- | --- |
| `chrome` | Inter Bold, tracked capitals | 18 | chrome | Rail and badge text only |
| `kicker` | Inter Bold, tracked capitals | 24 | tertiary | Section or column label above a heading |
| `small` | Inter Medium | 24 | tertiary | Units, axis ticks, sub-lines |
| `monoSm` | JetBrains Mono | 24 | tertiary | Small identifiers inside glyphs |
| `label` | Inter SemiBold | 28 | content | Object labels, chips, names |
| `key` | Inter Bold | 28 | content | The key of a callout |
| `mono` | JetBrains Mono | 28 | content | Code, identifiers and computed details |
| `accent` / `accentMd` / `accentSm` | Instrument Serif Italic | 70 / 38 / 28 | content | The qualifying phrase, takeaways and handwritten notes |
| `body` | Inter SemiBold | 30 | content | Short supporting line |
| `title` | Inter SemiBold | 32 | content | Row names, step titles, equations |
| `headline` | Inter Bold | 44 (statement 56) | content | Scene title, kinetic claim, question prompt |
| `numeral` / `numeralSm` | Inter ExtraBold / Bold | 58 / 30 | content | Balances, totals and answers |
| `display` | Inter ExtraBold | 88 | content | Lesson opener title only (`partOpener` fits 88 down to 56) |

Notes on sizes and tiers:

- Override `size` when layout requires it, but never below the floor. Do not change faces or tracking per scene.
- Mark text `tier: 'tertiary'` only for units, ticks and glyph-internal IDs.
- The motion-compatible `S.label(id, str, x, y, {size: 28, color, owner, align, weight, tier})` defaults to 28 px and accepts `tier: 'tertiary'` or `'chrome'`. Only the rail and the badge use `'chrome'`.
- To adopt a user's reference style, edit `T`, `FACES` and `TYPE` in `design.cjs` once for the project. Declare and license any replacement font, keep the floors, and keep the grammar below.

## What the stage checks

Every label goes through the same guard, whether it is drawn by a world, a template or an illustration. Failures reach the frame audit through `S.check`, which reports them as `mechanism-invariant` problems.

| Check | Fails when |
| --- | --- |
| `type-<id>` | A fully visible label (alpha ≥ 0.9) is smaller on screen than its tier's floor. On-screen size is the role size × the current transform's scale, so a zoomed-out camera, a scaled group or a pop below full size can fail it. |
| `edge-<id>` | A visible label's screen box comes within `EDGE` = 12 px of the safe area (40–1240 × 88–587 at 1280×720). The edge guard fades such a label to zero at the edge, so text is never sliced, and outside transition frames a fade it had to apply fails the check. Content text drawn in the top band or the caption band is hidden and fails with "chrome role for text outside the content area". |
| `words` | More than `WORD_BUDGET` = 24 content words are visible in one frame. Only labels above 0.5 alpha are counted; chrome is not. |
| `fit-<template>` | A template given its scene `end` has a spoken span shorter than its `MIN_SPAN`. |
| `rail-fit` | The progress rail runs past x 1240. |
| `rail-badge` | In a frame where both show, the rail ends less than 20 px before the fiction badge. |

How the checks apply:

- **Transition frames.** Frames that call `S.transition(...)` skip the type and edge checks and the word budget.
- **`S.decor(...)`.** Text drawn inside decor is not registered, but it still meets its floor, the edge guard and the word budget.
- **Chrome.** Chrome-tier text is exempt from the edge guard and the word budget, but not from its own 18 px floor. Only the rail and the badge in `templates.cjs` use it: `design_checks` rejects `role: 'chrome'`, `tier: 'chrome'` and `chrome: true` in authored worlds.

`S.finish()` adds the `words` check and returns `{items, safe, viewport, invariants, transition, words}`.

To keep a label clear of the edge guard during a camera move, fade it before the move starts:

- `beforePush(t, [a, b])` for a label you place by hand;
- `S.onScreen(box, {margin: 20})`, which gives the 0..1 visibility of a world box under the current camera, for anything computed from geometry.

## Stage primitives

The stage keeps all of its earlier members:

- **Drawing:** `text`, `label`, `layout`, `sentence`, `card`, `chip`, `marker`, `counter`.
- **Annotation:** `partial`, `arrow`, `scribble`, `underline`, `strike`, `dotGrid`.
- **Frame control:** `iris`, `wipe`, `view`, `fade`, `actor`, `decor`, `transition`, `check`, `fits`, `unclipped`.

New members:

- **`S.callout(id, key, value, x, y, {layout, keyRole, valueRole, keyOver, valueOver, keyColor, valueColor, align, mark, markColor, colon, gap, owner, keyP, valueP, state, swatchP})`**
  - Sets a bold key, then its value: "Shelf: 12".
  - It is the replacement for quantity pills.
  - `layout` is `'inline'` (the default, which adds a colon) or `'stack'` (the key above the value).
  - `keyP` and `valueP` stage the reveal: the key lands first, and the value lands on its spoken word.
  - `mark` (0..1) sweeps the highlighter behind the value.
  - `state` puts a swatch before the key.
  - Returns `{x, y, w, h, value: {x, y, w, size}}`.
  - Ids: `<id>-k`, `<id>-v`, `<id>-mk`, `<id>-sw`.
- **`S.markText(id, str, x, y, {role: 'label', over, align, p, color, inkColor, markColor, owner, pad: 12})`**
  - The highlighter sweeps behind the words, and the type turns ink exactly under the sweep, so white text on night stays readable on the band.
  - Returns the band box plus `text: {x, w}`.
- **`S.sentence(...)` highlighter runs.** Marks (`styles[i].mark`) on consecutive words of one line join into one band with id `<id>-mark<first>`. The band owns its words, and marked words hold still. The `'slide'` reveal moves words in sideways only, for text that sits close above other content.
- **`S.stateBox`, `S.swatch`, `S.hatch`:** see the state code above.
- **`S.rule(x1, x2, y, p, {weight, color})` and `S.vrule(x, y1, y2, p, {weight, color})`.** Unregistered rules drawn with `p`. Heavy rules (5–6 px) open a section, and hairlines divide.
- **`S.onScreen(box, {margin})` and `S.night`:** see above.

Defaults changed by the meaning colours:

- `marker()` uses `T.signal`.
- `strike()` uses `T.ink`.
- `scribble()` and `underline()` keep the accent.

## Motion grammar

| Movement | Duration and easing |
| --- | --- |
| Word reveal (`rise`, `slide`, `blur`, `ghost`) | 0.35–0.6 s, `E.out` / `E.outExpo` |
| Chip or badge pop | 0.55 s, linear progress through `E.outBack`; the fade reaches full only once the pop is past full size (`clamp(p*2.3)`), so popping type never reads below its floor |
| Focus dim or brighten | 0.4–0.6 s, `E.inOut`, to about 30–40% |
| Sentence exit before a carry | 0.35 s, `E.out` |
| Carry of a hero object | 0.8–1.2 s, `E.inOut`; the word holds in its slot (`hold`, at most 0.3 s) while the context clears, then changes role and colour at the midpoint |
| Highlighter sweep | 0.45–0.55 s, `E.inOut`, on the spoken word; it retracts when the narration moves on |
| Camera pan between regions | 1.0 s, `E.inOut`, with motion blur proportional to speed |
| Slow push across a scene | the scene's span, at most 1.06 zoom; at most 1.03 over template defaults unless their labels fade first |
| Reframing push | 0.7–1.0 s with `fitCamera`, after the labels it would carry off frame have faded |
| Iris or wipe | 1.0 s, full frame; the iris fills with the accent, then opens the next region |
| Transition window | `[next.start - 0.3, next.start + 0.7]`, inside the closing pause (`win()` from `planner`) |

## Camera

Draw a continuous world through `world(S, t, keys, draw, {pans})`:

- It eases between keyframes with `cameraAt` and blurs in proportion to speed.
- Frames inside a `pans` window are reported as transition frames.
- It returns the camera.
- Start the destination's content when the pan starts, so a pan never arrives on a blank page.
- Keep keyframes ordered with `orderKeys(keys)`; it nudges each key at least 0.05 s after the previous one when narration compresses a scene.

There are two kinds of push:

- **Slow push.** A hand-written zoom of at most 1.06 across a scene, for emphasis. It frames nothing new. Template default positions leave room for a centred slow push of at most 1.03. Beyond that, keep the template's content further inside the safe area, or fade its labels first with `S.onScreen` or `beforePush`, or the edge guard fails them.
- **Reframing push.**
  - `fitCamera(box, {top: 196, bottom: 574, left: 54, right: 1226, maxZoom: 1.6, minZoom: 1})` returns a key `{x, y, zoom}` that frames a world box inside the content band, below a section head and above the captions. Use it as `{t, ...fitCamera(box)}`; never hand-tune a reframing push.
  - Before the push, fade whatever it would carry to the edge: `beforePush(t, [a, b], {d: .3})` is 1 outside the move window and 0 inside it, with ramps that end before the move starts and begin after it ends. Use `S.onScreen(box)` for geometry-derived fades.
  - A push must not cut a group the narration is counting (sixteen shown as eight). Fit the whole group or fade it as one.

## Transitions

- **`S.iris(cx, cy, p, fn, {mode, color})` and `S.wipe(p, fn, {mode, slant})`.** These paint the full frame, including the top band and the caption band. Only `fn()`, the next scene, is clipped to the content viewport. Call them inside `S.transition(...)`, so the frame is reported, and at the top level of the frame. Inside `S.view`, `S.fade`, `S.actor` or a `world()` draw callback they throw, because leaving the content clip there would pop the camera or alpha instead. `S.unclipped` may be nested inside another `S.unclipped`, `S.transition` or `S.decor`.
- **Pans** are transitions through `world({pans})`.
- **A carry** is not a transition: the carried object is registered like any other.

## Templates

| Template | Teaching move | Drive it with | Minimum spoken span |
| --- | --- | --- | --- |
| `opener` | Promise and agenda | title, accent and agenda cues | 4.5 s |
| `partOpener` | A lesson's first frame in its part's layout and motif, with a hero object | title and accent cues, `hero(S, box, t)` | 4.5 s |
| `sectionHead` | Heavy rule and headline in screen space; one item at a time | `items: [{text, times, until, marks}]`, `deck` | 2 s |
| `statement` | The one claim, ghosted, filled as spoken, emphasis highlighted | `cue.phrase` for every word, `exitAt` | 3 s |
| `carry` | Move the emphasised word or number into the next scene | emphasis position from `statement`, `hold` | — |
| `compare` | Before/after or changed/conserved columns with ink strikes, arrows and a check in `good` | row cues, `focusAt`, takeaway phrase | 6 s |
| `lineStory` | Series that vary against an invariant line | series, invariant and focus cues | 6 s |
| `stepper` | A procedure with a travelling token (neutral ink, or a course state through `state`) | one cue per step | 5 s |
| `readout` | Lane-aligned key/value rows beside a diagram, with state swatches | `rows: [{key, value, sub, state, y, at, valueAt, mark}]`, `cursor` | 3 s |
| `stateKey` | A legend row that teaches the state code | `items: [{state, label, at}]` | 2 s |
| `question` | Retrieval practice on night, options visible before the reveal | prompt phrase, `revealAt` on the answer word, `art`, `tags` | 6 s |
| `progressRail` | Persistent orientation in the top band | scene starts, `night` windows | — |
| `fictionBadge` | Marks invented people, companies and figures | `windows` | — |

Each template checks its spoken span with `S.fits` when it is given `end`. `MIN_SPAN` holds the minimums, and `PAGE` holds the shared screen positions:

- the top band line at y 50;
- the section rule at y 100;
- the headline at y 146;
- the content margins at x 80 and x 1200.

Signatures and details:

- **`partOpener(S, t, {part, lesson, kicker, title, accent, start, end, at, exitAt, markWords: 2, hero, motifAt, motifUntil, x, y})`**
  - Returns the part's layout, so the lesson can keep its hero after the title exits.
  - A course chooses once how each part opens: `defineParts({I: {name: 'Arrivals', layout: 'heroRight', motif: 'columns'}, II: {name: 'Sorting', layout: 'heroLeft', motif: 'ledger'}})`.
    - Layouts: `heroRight`, `heroLeft` and `heroBelow`.
    - Motifs, drawn in hairline rule ink: `columns`, `ledger`, `grid`, `form` and `calendar`.
  - `partKey` accepts a key or a lesson's `part` string such as `"Part II · Sorting"`.
  - `partLayout(part, {x, y})` gives the hero and title boxes for a region centred elsewhere.
  - The title is fitted from 88 down to 56 px. `heroBelow` wants a title that fits one line at 56 px (about 36 characters).
  - This is the only variation device: colour meanings, type roles and page furniture never vary.
- **`sectionHead(S, t, {id, x, y, width, ruleAt, until, items, deck, headRole, deckRole, deckColor, start, end})`**
  - Draws in screen space even inside `S.view`, so the camera moves the world beneath it. Keep world content below y 196 while a head is up.
  - An item lifts away before its successor's first word.
- **`readout(S, t, {id, x, width: 380, rows, cursor, keyRole: 'kicker', valueRole: 'numeralSm', valueOver, until, rule, guideAlpha, start, end})`**
  - Pass the value from `spoken()`: a `null` value draws nothing.
  - Its text is ink, so use it on paper. On night, use callouts.
- **`stateKey(S, t, {id, x, y, items, gap, labelRole, size: 26, start, end})`** returns the row's width. Like the readout, it is for paper stages.
- **`question(S, t, {x, y, start, end, kicker, prompt, options, correct, revealAt, reason, scene, at, art, tags, tagsAt, optionsAt, promptAfter})`** returns `{art, optionsY}`.
  - The kicker takes the highlighter (`markText`).
  - The options are visible before the reveal (`optionsAt`, default just after the prompt).
  - On `revealAt`, the narrator's answer word and never earlier:
    - the correct option takes the signal highlighter;
    - each wrong option dims under a strike in `T.wrong`;
    - from `tagsAt` (default `revealAt + 0.45`), `tags: [{text, state}]` say what each option is.
  - `art(S, box, t)` draws a picture of the situation between the prompt and the options. Use state boxes, callouts and the cast there; `S.night` is true.
  - `promptAfter` (0..1) dims the prompt once the answer is out, keeping the frame within the word budget.
- **`progressRail(S, t, {steps, at, from, until, night, states})`**
  - The rail is chrome on the band line.
  - The current section is inverted ink, an ink block that sweeps in with white type, never the signal colour. Done sections settle to `inkSoft`.
  - It is hidden on a night stage. `night: [[from, until]]` windows fade it out before a wipe into night and back after.
  - `states` puts a state swatch after each label.
  - Keep labels short: tracked capitals make the rail wide. `rail-fit` fails when it runs past x 1240 and `rail-badge` when it ends less than 20 px before the fiction badge.
  - It returns its box while it shows, or `null` while hidden.
- **`fictionBadge(S, t, {windows: [[from, until], ...], label: 'Fictional example'})`**
  - Also accepts `{from, until}`.
  - A violet chrome block, right-aligned on the rail's line, with a light keyline on night.
  - Returns its box, or `null` while it is off.

Call `progressRail` and `fictionBadge` at the top level of the frame, after the scene. They draw unclipped in screen space.

**Fiction badge rule.** Keep the badge on whenever invented people, companies or figures are on screen, including practice panels. Switch it off over purely real facts, and over general claims and methods that carry no invented figures. When a lesson alternates, split the windows around the real material; never leave one window on across it.

The subject mechanism, such as a transfer, a gate, a migration or a correction path, is authored in the world with stage primitives. Templates frame it; they do not replace it.

## People and the cast

`figure(S, id, x, y, opts)` from `illustrations.cjs` draws a full person with a face, on a design stage or a motion stage. `(x, y)` is the point between the feet. At `s: 1` a standing figure is about 300 px tall, a hero while it speaks. At `s: .8` it is about 245 px, plus about 80 px for two label lines.

Its options:

- **`pose`:** one of `POSES`: `stand`, `point`, `pointUp`, `present`, `raise`, `wave`, `hold`, `hips`, `shrug`, `think`, `cross`, `sit`, `lean`.
- **`arms`:** a pose name or `[[a1, a2], [a1, a2]]`. Use `blendArms(a, b, p)` to grow a gesture on its cue.
- **`facing`:** `1` or `-1`.
- **`speaking`:** 0..1, with `phase: t`. Pass `talking(t, from, to)`; the mouth moves and speech marks appear.
- **`prop`:** `laptop`, `tablet`, `paper`, `form`, `folder`, `phone` or `mug`.
- **`name` and `role`:** labels placed by `label` (`below`, `above`, `left`, `right` or `none`), as `<id>-name` and `<id>-role` at 28 px. They count toward the word budget.
- **Also:** `s` or `scale`, `alpha`, `owner`, `seat`, `lean`, `ground`.
- **Look fields:**
  - `skin`, `hair`, `topColor`, `inner` and `bottom` are names from `LOOK`, never hex.
  - `style` is from `HAIR_STYLES`, `top` from `TOPS`, and `lower` is `trousers` or `skirt`.
  - `glasses`, `beard` and `badge` complete the look.

It returns `{bounds, hands: {back, front}, head, mouth, top}`. The full extent, including sleeves, hair, props and speech marks, registers through `S.actor`.

A course defines its recurring people once, at module scope, and stages them with `cast`:

```js
const {defineCast,cast}=require('./illustrations.cjs');
defineCast({clerk:{name:'Mira',role:'Clerk',skin:'skin4',hair:'hairBlack',style:'bun',top:'cardigan',topColor:'sage',inner:'white',bottom:'navy',glasses:true}});
// in a scene: the speaker at full strength, earlier speakers dimmed
S.fade(focusOf(t,speakers,0),()=>cast(S,'clerk','clerk',x,feetY,{s:.8,pose:'present',speaking:talking(t,a,b),phase:t}));
```

Cast rules:

- A real or recurring person drawn differently across lessons reads as a different person, so a preset's look is fixed:
  - `cast()` throws for any look field in its options, and for unknown options.
  - `name` and `role` can be hidden with `false` but not renamed.
  - Two presets with an identical look throw.
  - Generic, unnamed people are presets with `name: null`.
  - The system ships no presets.
- `CAST` is the live registry: worlds read it, and only `defineCast` writes it.
- On night, outlines become a light keyline, so dark hair and clothes stay visible.
- A dimmed figure (for example under `focusOf`) is drawn opaque in colours mixed toward the background (`ground`), so it reads as one faded person rather than overlapping parts.
- Lettering inside glyphs (a document's title or revision, a phone's headline) is tertiary text. A lettered document needs `s ≥ 1.4` on a design stage; below that its title and revision collide, and the audit says so.
- `person()` and the other glyphs keep their signatures.

## Cue-driven timing

`narrate.py` rewrites every scene's `start`, `end`, `speechStart`, `speechEnd` and `wordTimings`, so hard-coded seconds break as soon as real narration exists. Compute the timeline once per lesson from scenes and cues:

```js
const cue=createCues(lesson);            // cached per lesson object
cue('transfer','leave');                 // onset of "leave", spoken once in scene "transfer"
cue('transfer','account',2);             // the second "account"
cue.count('transfer','holds');           // 2, so cue('transfer','holds') throws: pass nth
cue.end('check','total',1);              // when the first "total" ends
cue.phrase('check','Moving units changes balances, not the total.',{after:cue('check','still')});
cue.method('claim');                     // 'measured' or 'estimated'
```

How cues resolve:

- Before narration, onsets are estimated across the scene's speech span. Afterwards they are the measured word boundaries, with no world change.
- Scenes are addressed by id or by 1-based index.
- A missing word throws instead of drifting.
- **Ambiguity rule.** A word spoken more than once in the scene throws `Ambiguous narration cue` unless you pass `nth`, because the first occurrence is often seconds before the sentence the reveal belongs to. Passing `nth`, including 1, is always allowed. `cue.end` follows the same rule.
- `cue.phrase` matches its words in order after `after`, so give it `after` when a phrase's words occur earlier in the scene.
- A measured provider event that covers several words ("in 2015") is split, and later words are placed by character position.

`planner(build)` caches a plan per lesson object. `build` receives `{lesson, cue, sc, win}`: the cues, the scenes by id, and `win(scene)`, a transition window that begins in the closing pause before the scene. Derive camera keyframes, mechanism windows and transitions inside it:

```js
const planFor=planner(({cue,sc,win})=>{
  const push=[cue('transfer','while')-.3,cue('transfer','while')+.4];
  const keys=orderKeys([{t:0,x:640,y:340,zoom:1},{t:push[0],x:640,y:340,zoom:1},{t:push[1],...fitCamera(focusBox,{maxZoom:1.3})}]);
  return {push,keys,pans:[win(sc.contrast)]};
});
// draw(): const P=planFor(lesson); world(S,t,P.keys,drawRegions,{pans:P.pans});
```

Pass each template its scene `start` and `end`. If the spoken span is shorter than the template's minimum, the frame audit reports a `fit-<template>` failure. Lengthen the narration rather than squeezing the choreography.

Focus helpers take cue times:

- `talking(t, from, to, {fade: .25})` is a speaking intensity for a person.
- `focusOf(t, speakers, i, {dim: .3, all, d: .4})` with `speakers[i] = {from, to}`:
  - 0 before speaker `i` first speaks;
  - 1 while they are the active speaker;
  - `dim` once the next speaker starts;
  - full again from `all`.

Write narration that leaves room for the picture:

- Give a mechanism an establishing sentence before the change.
- Name the change with a distinct verb the world can cue on, such as "leave", "arrive" or "blocked". A verb used once needs no `nth`.
- End a scene with a short closing beat, so its last reveal can be read before the transition.

Record the template, region, incoming transition, emphasis, focus and trigger words in each beat's `design` object in the beat sheet.

## Spoken numbers

A figure the narrator says is shown only as it is said. `spoken(t, value, times, {mode, step, from, lead})` takes the onsets of the number's spoken words (`cue.phrase(scene, 'twelve thousand')`) and returns the value to show, or `null` when nothing should be shown:

| Mode | Shows |
| --- | --- |
| `'word'` (default) | `null` before the first spoken word, then exactly `value` |
| `'count'` | Round multiples of `step` (default `niceStep(value - from)`) between the first and last spoken word, landing exactly on `value` at the last word. Use it only for something that genuinely fills while it is said. |
| `'land'` | `null` until the last spoken word, then exactly `value` |

Notes:

- `lead` lets `'word'` and `'count'` start slightly early.
- `stepValue(t, {value, start, end, step, from, ease})` is the underlying stepper. Use it for a figure that changes to a result, so it never passes through an unsaid value.
- While a value is `null`, draw nothing: pass `valueP: 0` to a callout, or `null` to a readout row.

## Audit honesty

- Register every text and solid object. Use `owner` only for true containment.
- Wrap only full-frame transition frames in `S.transition(...)`; the audit reports `transitionFrames` per lesson.
- Use `S.decor(...)` for trails, rings, grids and rules that carry no label or solid object. Never use either wrapper to hide a collision or an edge or type failure in a held frame.
- Use the chrome tier only for the rail and the badge. `design_checks` rejects chrome type in authored worlds, because it lowers the floor to 18 px and skips the edge guard and the word budget.
- A deliberate contact, such as a quantity crossing a container wall, goes in `intentional-overlaps.json` with a reason. Scope it to a `scene` instead of absolute seconds, so it follows re-timed narration.
- Report model invariants through `S.check(id, passed, actual, expected)` or `finish({totalUnits, expectedTotal})`.
- `design_checks.visuals` rejects hex colours, font choices and chrome type in authored modules of a design-system world. It is a guardrail for literals, not a style review.
- Never `drawImage` a canvas every frame. In @napi-rs/canvas 0.1.x each such draw leaks a full frame, and a long audit runs out of memory. Encode a cached layer once and draw the decoded `Image`, as the background grain does.

## Do and don't

**Do:**

- Put one highlighter on the spoken word or value, and retract it when the narration moves on.
- Give a repeated cue word its `nth`.
- Show quantities in the course's states, and put swatches beside keys.
- Use callouts (key, then value) for figures, with the value on its spoken word.
- Use people from the cast at hero size when they speak, and dim earlier speakers with `focusOf`.
- Fade labels before a reframing push, and fit pushes with `fitCamera`.
- Give the practice panel a picture, and show its options before the reveal.
- Keep the fiction badge on over invented material, and split its windows around real facts.

**Don't:**

- Use the signal, gold, red or green for a state, a region, a category or a persistent fill.
- Set text below its tier floor, or letter tiny glyph detail.
- Mark a world's own text chrome: it lowers the floor to 18 px and silences the edge and word checks.
- Scale a group below full size while it is fully opaque: fade it, as `chip()` does.
- Let a camera move carry text into the frame edge.
- Count up through values nobody says.
- Put more than 24 content words on screen.
- Leave a blank frame mid-pan, or a sparse beat longer than about 2 s.
- Hard-code colours or fonts in a world.
- Draw a recurring person with a different look.

## Before bulk rendering

Render the silent preview and audit. Then inspect encoded frames at these moments:

- the opener;
- each statement's highlight;
- the middle of every mechanism;
- the midpoint of each pan, iris, wipe and push;
- the final frame of every scene.

Check that each reveal lands on its spoken word, that focus moves where the narration points, and that transitions start after the last reveal can be read. Then run the [sentence-end review](review-and-delivery.md#sentence-end-review) on every lesson. Compare against the user's reference if one exists. A clean audit establishes registered geometry, type floors, edge clearance, word budget and timing fit, not design quality or comprehension.
