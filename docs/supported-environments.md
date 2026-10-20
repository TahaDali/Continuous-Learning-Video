# Supported workflow and setup

This is an agent-driven Codex skill. After setup, one job URL requests the whole research-to-private-course workflow. It is not a background job-link service or a universal animation compiler. The agent authors each course's narrative and graphics and reports meaningful progress during production.

## Local execution

The helpers target Python 3.10+, Node.js and FFmpeg/FFprobe with H.264/AAC support. Canvas is installed inside the new project's `production-source` directory with `npm install --prefix production-source`; `CANVAS_MODULE` can select an existing compatible installation. Run `workflow.py preflight` first. Initialization/preflight make no speech requests. They do not test an external provider endpoint.

The private test machine used macOS, Python 3.14, Node 20 and FFmpeg. Linux CI uses Python 3.12 and Node 22 and installs the declared canvas dependency. These versions describe actual coverage, not a claim that every OS/browser combination works. A fresh isolated canvas install was tested separately from the preexisting runtime. Windows and a clean physical second machine remain untested.

## Services

Use available supported browsing and hosting capabilities. Public pages can fail in one route and succeed through an official public job API. Verify the exact employer, vacancy and current text; never substitute another vacancy or assume a fetch failure means it closed. Supplied posting text can support recovery with visible provenance. Without the actual role requirements, a verified job-specific course remains unfinished.

The optional speech helper was exercised with `edge-tts` 7.3.1 exposing `boundary='WordBoundary'`. Older incompatible interfaces fail explicitly. Verify the installed interface and current endpoint; the version is test evidence, not a permanent service guarantee. The helper sends only adapted narration authorized for that provider, uses bounded retries, preserves cached completed blocks and does not switch providers automatically. Voice selection and text-transfer authorization are distinct. No provider credentials belong in a course JSON or bundle.

Hosting requires a supported provider and actual successful deployment. If Sites is available, use its installed workflow and native owner-private operation. Sites tooling is not bundled in this skill. If hosting is unavailable, the validated local HTTP player/export remains useful, but the agent must identify hosted delivery as unfinished. Never change an audience to solve playback.

## Player and review

Serve local exports over HTTP; a direct `file://` page has browser-dependent fetch/caption restrictions. The bundled loopback server supports ranges. The player has transcripts, captions, glossary support, part navigation, practice feedback and bounded seeking recovery. It downloads only the active chapter when the browser/host exposes no usable seek range; it is not a full offline course cache. Native media controls vary by browser. Detailed diagrams benefit from full screen on small displays.

Mechanical tests verify their specified boundaries. Real-browser responsive/keyboard checks and the ongoing five-case evaluation add evidence, but no blanket WCAG, pronunciation, human-voice realism or learner-readiness certification is claimed. Each delivered course keeps its actual review coverage and limitations visible.
