# Production and measured timing

## Local starter

The starter uses Python 3, Node.js, FFmpeg/FFprobe and `@napi-rs/canvas`. Use available bundled runtimes first. Otherwise install dependencies within the task workspace, not into unrelated global environments. `CANVAS_MODULE` may point to a known local canvas package. The package records a tested canvas version; check installed interfaces before changing versions.

`new_project.py` refuses to overwrite an existing directory. It creates:

```text
course.json                  Adapted narration and measured timing
visual-beat-sheet/beat-sheet.json
production-source/           Editable world, renderer, audio and geometry helpers
player/                      Generic course controls, videos, captions, posters
audio/                       Intermediate narration; exclude from hosting by default
transcripts/
review/                      Reports, flagged frames and silent previews
```

Run commands from the new project root:

```text
python3 <skill-dir>/scripts/validate_project.py /absolute/project
node production-source/render.cjs all --silent-preview
node production-source/render.cjs posters
node production-source/audit.cjs
```

Silent previews deliberately go to `review/silent/`, not final `player/videos/`. They are not final narrated deliverables. The example is 12 seconds for inexpensive mechanical testing; production lesson lengths follow the user's brief.

The renderer calls `world.draw(context, lesson, time, course)` at each actual frame timestamp. It uses backpressure while streaming pixels to FFmpeg and fails when an unsupported visual is requested. Extend the authored world with subject-specific functions; do not silently fall back to the sample for unimplemented lessons. `motion.cjs` provides camera transforms, object/label bounds and simple primitives. The stage includes `wrappedLabel` with measured font widths and explicit line spacing; its returned height helps choose an owner box before rendering. Extend those helpers when shapes, clipping or typography require it. The sample preserves objects across time and transfers a visible quantity between containers.

`illustrations.cjs` supplies original parameterized people, publications, browsers, phones, envelopes, buildings and clocks. Call `createIllustration(stage)` to register their glyphs and labels with the existing geometry audit. Include this helper and every other imported drawing file in the course's `renderSources`. These conventional forms are a starting vocabulary; author the real subject's missing objects and causal behavior. They do not constitute a complete lesson world, and glyph internals and connector paths still require visual inspection.

For layout, use explicit foreground/midground/background relationships. Connectors normally pass behind solid objects and labels. Draw a foreground mask at its intended depth rather than blindly moving every panel behind all content. For complex glyphs, register the complete visual extent, including strokes, arcs and moving attachments. Text bounds must use the rendered font and actual transform.

The starter geometry is conservative axis-aligned bounding boxes. Transparent enclosures, crossing connectors, glyph internals, partial occlusion and alpha blending may need better per-shape handling. It does not claim raster or perceptual completeness. The starter supports pan and zoom; rotate or skew only after extending the camera and audit together.

Inspect actual encoded frames even after a clean audit. Owner-contained labels are excluded from intersection findings, so a label can still cross an internal border such as a database cylinder's ellipse. Size the usable interior for the measured wrapped text and inspect the result at full resolution. A fresh audit archives previous flagged images with their report, so stale failures do not appear to be current findings.

## Narration

Reuse a selected voice and existing consent when applicable. Otherwise prepare two short samples of adapted narration representative of a question, an explanation and a discovery. Ask a focused preference question while proceeding with independent visual work. Do not upload original documents to sample a voice. The user's approval of a voice in one project is a preference, not permission to send new private material in another.

After Microsoft speech processing is authorized, the optional bundled helper uses `edge-tts` with word boundaries. Its locally tested interface is version 7.3.1; verify the current installed interface and provider availability instead of pinning an obsolete broken client indefinitely. This is a speech-service client, not an Azure account credential or a guarantee of service availability. If the endpoint fails, inspect the current supported client and retry within the helper's bounded attempts. Do not switch to another service, incur charges or send content to a new provider without the applicable authorization.

```text
python3 production-source/narrate.py --voice en-US-AvaMultilingualNeural --sample
python3 production-source/narrate.py --voice en-US-AvaMultilingualNeural
```

`--sample` sends only the first adapted narration block and writes a review MP3. Choose a different voice for a second sample. Full mode supports `--concurrency 1` through `4` (default `2`) and caches by text, voice and rate, aligns source character positions to returned word events, assembles block audio, and writes exact captions, sentence cues, transcripts and player data. It does not modify the creative fields of the beat sheet. The combined workflow regenerates the readable Markdown sheet when measured narration is checkpointed. For standalone use, run `python3 <skill-dir>/scripts/write_beat_sheet.py /absolute/project`.

The helper fails on word alignment or cue-coverage differences. Fix the text/cue mapping; do not replace measured timing with equal estimates just to make a run pass. Every cue carries an explicit exact narration span, so abbreviations and non-English punctuation do not need an automatic sentence splitter. Supply narration with explicit units and intelligible phrasing instead of phonetic brand misspellings in the displayed transcript. Do not alter meaning to appease speech recognition.

A provider may return a zero-duration word event after quoted dialogue. The helper retains its measured onset and uses the next measured onset as its caption end, preserving the raw endpoint and marking the inference in `wordTimings`. It does not claim that inferred endpoint is an acoustically measured word ending. A trailing zero-duration event still fails validation.

The service exposes limited prosody controls. Use natural syntax, purposeful block boundaries, modest rate variation and appropriate voice selection. A model name alone does not prove human realism or emotional intelligence. Listen before accepting its delivery.

With approved audio and final timings:

```text
node production-source/render.cjs all
node production-source/render.cjs posters
node production-source/audit.cjs
python3 <skill-dir>/scripts/validate_project.py /absolute/project --media
```

The output is 1280×720, 24 fps H.264/AAC with optional English captions in the sample. Configure aspect ratio, language, dimensions and rate deliberately when the brief differs, then update safe zones, captions and tests together. Timing changes invalidate affected renders and review evidence.

The bundled player has lesson navigation, playback speed, captions, completion progress, transcript jump points and downloads. A fresh project's progress key must be distinct. Playback may require an HTTP server; `python3 production-source/serve.py --port 0 --open` serves its player on loopback and supports video byte ranges. Add `--directory /absolute/path/export` to test the exact hosted export. Do not use this as a workaround for a browser-policy rejection. For hosting use the relevant available hosting skill.
