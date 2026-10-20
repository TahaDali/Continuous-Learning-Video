# Provenance and external components

The repository's original instructions, helpers, player and mechanical example are proposed for release under MIT. This choice is part of the private release candidate and awaits the owner's final approval. It does not grant rights to third-party source material, names, trademarks, services or generated courses. Repository visibility and course audience remain separate decisions.

The research method was distilled from a user-supplied teaching conversation. Its Axios reference is a condensed historical method example with fictional people and transactions, incomplete original source lineage and explicit factual limitations. The original conversation, personal biography, job snapshots, private courses and private hosting identity are excluded from the repository and release bundle. Employer facts need new verification in each course. No employer logos or proprietary design documents are bundled.

External dependencies are installed separately; their code and binaries are not included in this skill bundle:

| Component | Use | Upstream license/source |
| --- | --- | --- |
| `@napi-rs/canvas` | Procedural raster rendering | [Upstream license](https://github.com/Brooooooklyn/canvas/blob/main/LICENSE): MIT with additional notices for incorporated components. Preserve the installed package's notices when distributing it. The starter records the tested version. |
| `edge-tts` (optional) | Client for authorized Microsoft speech requests | [Upstream license](https://github.com/rany2/edge-tts/blob/master/LICENSE): LGPLv3 for most files, MIT for its SRT composer. It is not vendored here. Check the installed distribution's complete license and notices; the client license does not grant rights to Microsoft's service or voice output. |
| FFmpeg / FFprobe | Encoding and media checks | [Upstream licensing](https://ffmpeg.org/legal.html). Build configuration affects licensing. No encoder binary is bundled. |
| Python and Node.js | Local execution | Installed runtimes retain their own licenses and notices. |
| Browsing, speech and hosting providers | Research, narration and delivery | External services retain their own terms, availability, credentials and permissions. A skill installation is not service authorization. |

The canvas world requests a system sans-serif font; no font file is bundled. Research links identify sources rather than redistributing complete pages. A source's public availability does not establish permission to redistribute its text, assets or private details. Course authors must review the actual material and intended audience before export.
