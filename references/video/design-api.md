# Design-system calls

Signatures for the stage, the templates, people and the timing helpers in `production-source/design.cjs`, `templates.cjs` and `illustrations.cjs`. [The design system](design-system.md) gives the rules these calls serve and what the audit checks; read it first. Open this file when writing a world.

## Drawing a state

| Call | Draws |
| --- | --- |
| `S.stateBox(id, state, x, y, w, h, {p, owner, register, outline, weight, gap, dash, alpha})` | A box in the state's treatment. `p` fills it left to right while the outline stays whole. The outline is ink on paper and white on night. `register: false` (or no id) draws it as decor. |
| `S.swatch(id, state, x, y, {size: 26, owner, register, p})` | A legend square. `(x, y)` is its left edge and vertical centre. |
| `S.hatch(x, y, w, h, {color, gap: 9, width: 1.6, alpha})` | Unregistered diagonal hatching. Use it, for example, inside a travelling token in a hatched state. |
| `tpl.stateKey(S, t, {items: [{state, label, at}]})` | Teaches the code where each state first appears. |

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

## Template signatures

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

## People: figure options

`figure(S, id, x, y, opts)` from `illustrations.cjs` draws a full person with a face. Its options:

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

## Cues, plans and focus

Compute the timeline once per lesson from scenes and cues:

```js
const cue=createCues(lesson);            // cached per lesson object
cue('transfer','leave');                 // onset of "leave", spoken once in scene "transfer"
cue('transfer','account',2);             // the second "account"
cue.count('transfer','holds');           // 2, so cue('transfer','holds') throws: pass nth
cue.end('check','total',1);              // when the first "total" ends
cue.phrase('check','Moving units changes balances, not the total.',{after:cue('check','still')});
cue.method('claim');                     // 'measured' or 'estimated'
```

`planner(build)` caches a plan per lesson object. `build` receives `{lesson, cue, sc, win}`: the cues, the scenes by id, and `win(scene)`, a transition window that begins in the closing pause before the scene. Derive camera keyframes, mechanism windows and transitions inside it:

```js
const planFor=planner(({cue,sc,win})=>{
  const push=[cue('transfer','while')-.3,cue('transfer','while')+.4];
  const keys=orderKeys([{t:0,x:640,y:340,zoom:1},{t:push[0],x:640,y:340,zoom:1},{t:push[1],...fitCamera(focusBox,{maxZoom:1.3})}]);
  return {push,keys,pans:[win(sc.contrast)]};
});
// draw(): const P=planFor(lesson); world(S,t,P.keys,drawRegions,{pans:P.pans});
```

Focus helpers take cue times:

- `talking(t, from, to, {fade: .25})` is a speaking intensity for a person.
- `focusOf(t, speakers, i, {dim: .3, all, d: .4})` with `speakers[i] = {from, to}`:
  - 0 before speaker `i` first speaks;
  - 1 while they are the active speaker;
  - `dim` once the next speaker starts;
  - full again from `all`.
