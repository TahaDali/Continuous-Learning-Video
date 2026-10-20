# Provenance and external components

Continuous-Learning-Video was created and is maintained by [TahaDali](https://github.com/TahaDali), with AI-assisted development. It combines the organization-first teaching method and continuous explanatory-video workflow developed in the earlier Learning Skills project. Existing contributor attribution and history are preserved.

The owner approved **Apache-2.0** for this release on October 20, 2026. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Earlier portions were offered under MIT; their [original notice and permission text](LICENSES/Legacy-MIT.txt) remain included, and prior grants are not revoked. The current license does not grant rights to third-party source material, names, trademarks, services or every generated course.

The current [teaching case](references/research/teaching-case.md) is a newly authored fictional example. It replaces the adapted employer-specific historical case in the release payload. Earlier private development used a user-supplied teaching conversation; its full original source lineage was not independently established. That development history is retained in Git, without claiming legal clearance of all historical expression. No original transcript, personal biography, real job snapshot, private course or hosting identity is part of the current payload. The owner authorized public release after the audit and review of five private sample courses.

External dependencies are installed separately; their code and binaries are not included in the skill ZIP:

| Component | Use | License and boundary |
| --- | --- | --- |
| `@napi-rs/canvas` | Procedural raster rendering | [MIT and incorporated-component notices](https://github.com/Brooooooklyn/canvas/blob/main/LICENSE). Preserve the installed distribution's complete notices if redistributing it. The committed lockfile records package identity. |
| `edge-tts` (optional) | Authorized Microsoft speech requests | [LGPLv3 for most files; MIT for the SRT composer](https://github.com/rany2/edge-tts/blob/master/LICENSE). Not vendored. The client license does not establish service entitlement or rights to every voice output. |
| FFmpeg / FFprobe | Encoding and media checks | [Build-dependent LGPL/GPL terms](https://ffmpeg.org/legal.html). No binary is bundled. |
| Python and Node.js | Local execution | Separately installed runtimes retain their own licenses. |
| Browsing, speech and hosting providers | Research, narration and delivery | Their own terms, availability, credentials and permissions apply. Installing this skill does not authorize a new data transfer or public course audience. |

No font file, employer logo or proprietary design document is bundled. The renderer uses a system sans-serif font. Source links are references, not redistribution permission. Review the actual source rights and audience before exporting or publishing a course. No employer endorsement or learner-effectiveness certification is implied.
