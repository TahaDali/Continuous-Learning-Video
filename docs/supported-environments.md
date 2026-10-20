# Supported environments

## Skill discovery

The single root skill is `continuous-learning-video`; the display/repository name is Continuous-Learning-Video. Current [official guidance](https://learn.chatgpt.com/docs/build-skills) lists `~/.agents/skills/` for user skills and `.agents/skills/` for repository skills. A managed or older Codex installation may use a different configured location. Verify the installed skill appears in the selector. Cross-host support is not claimed merely because another tool reads SKILL.md.

## Local tools

Python 3.10+, Node 20/22 and FFmpeg/FFprobe with libx264/AAC are required for the rendering path. The locked canvas dependency is 0.1.100. Run `npm ci --prefix production-source --ignore-scripts` in a generated project. `CANVAS_MODULE` can select a known reviewed compatible installation; it loads executable code.

The macOS audit used Python 3.14.3 and Node 20.20.2. Linux CI uses Python 3.12 and Node 22. Fresh isolated canvas installation and rendering were exercised. These checks do not establish a clean physical second machine or Windows support.

`workflow.py preflight --project /absolute/project` reports tool paths/versions, codecs and project canvas availability without speech requests. It does not prove provider availability or narration quality. The optional edge-tts helper requires a compatible WordBoundary interface; current local preflight found 7.2.8, while earlier development exercised 7.3.1. Verify the installed interface rather than assuming every version works.

## Services and player

Browsing and hosting are supplied by the current environment. The optional speech helper sends approved adapted narration to Microsoft's Edge speech service; it is not an Azure account integration. Service entitlement, text-transfer approval and voice selection are separate. Missing hosting leaves hosted delivery unfinished; preserve private access rather than widening an audience to make playback work.

Serve local players over HTTP. The bundled server uses loopback and byte ranges. Seeking fallback buffers only the active chapter when the host exposes no usable range; it is not an offline cache for an entire course. Large chapters can consume memory. Native media/caption controls differ by browser.

The reusable starter includes 44px authored controls, responsive wrapping, 16px transcript reading text, keyboard radio selection, modal focus containment, live feedback, and a transcript shortcut. Generated HTML beat sheets expose labelled keyboard-scrollable tables. Per-course review follows [the player accessibility guide](../references/video/player-accessibility.md).

Desktop browser smoke, viewport emulation and controlled player tests are bounded evidence. Physical mobile and screen-reader testing remain unverified. No universal accessibility, browser, codec, provider or learner-readiness guarantee is made.
