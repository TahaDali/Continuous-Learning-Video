# Provenance and external components

Continuous-Learning-Video was created and is maintained by [TahaDali](https://github.com/TahaDali), with AI-assisted development. It combines the organization-first teaching method and continuous explanatory-video workflow developed in the earlier Learning Skills project. Existing contributor attribution and history are preserved.

The owner approved **Apache-2.0** for this release on October 20, 2026. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Earlier portions were offered under MIT; their [original notice and permission text](LICENSES/Legacy-MIT.txt) remain included, and prior grants are not revoked. The current license does not grant rights to third-party source material, names, trademarks, services or every generated course.

The current [teaching case](references/research/teaching-case.md) is a newly authored fictional example. It replaces the adapted employer-specific historical case in the release payload. On October 20, 2026, the owner confirmed that the earlier supplied teaching conversation was created in the owner's own AI chat. The retained compilation and production records also trace it from that conversation to the historical case and Axios course. This closes the previously unrecorded conversation-origin issue; it is not evidence of a third-party infringement. The original private transcript and personal details remain outside the public payload. See the [rights review](https://github.com/TahaDali/Continuous-Learning-Video/blob/main/docs/rights-review.md) in the repository for the evidence scope and separate public-demo audio question. The owner authorized public release after the audit and review of five private sample courses.

For the owner-created ChatGPT material, [OpenAI's Terms of Use](https://openai.com/policies/terms-of-use/) assign any OpenAI rights in output to the user, to the extent permitted by law. That assignment does not cover third-party output, guarantee originality or establish copyright protection for every AI-generated passage. Public-source facts, attributed references and fictional teaching scenarios are distinct from permission to reproduce someone else's protected expression. Existing public history and prior MIT notices are preserved.

## Separate historical course

The README links an owner-approved public Axios demonstration on the `gh-pages` branch. Its 25 videos and captions are not included in the installable skill ZIP. Company and product names identify the subjects; no affiliation or endorsement is implied. The source-notes page identifies public references and fictional scenarios rather than redistributing the original private reading document.

The historical narration is synthetic `en-US-AvaMultilingualNeural`, generated through the Edge speech service. No provider-specific grant for public redistribution of those recordings was verified in this review. This is an unresolved permission-evidence question, not a finding that Microsoft prohibits the use. Neither this repository's Apache-2.0 license nor the optional speech client's license establishes that grant. Do not treat the demo recordings as cleared Apache-2.0 media. Closing this separate question requires applicable provider permission or replacement recordings made under documented terms covering public distribution. Azure Speech terms do not retroactively license recordings generated through Edge.

External dependencies are installed separately; their code and binaries are not included in the skill ZIP:

| Component | Use | License and boundary |
| --- | --- | --- |
| `@napi-rs/canvas` | Procedural raster rendering | [MIT and incorporated-component notices](https://github.com/Brooooooklyn/canvas/blob/main/LICENSE). Preserve the installed distribution's complete notices if redistributing it. The committed lockfile records package identity. |
| `edge-tts` (optional) | Authorized Microsoft speech requests | [LGPLv3 for most files; MIT for the SRT composer](https://github.com/rany2/edge-tts/blob/master/LICENSE). Not vendored. The client license does not establish service entitlement or rights to every voice output. |
| FFmpeg / FFprobe | Encoding and media checks | [Build-dependent LGPL/GPL terms](https://ffmpeg.org/legal.html). No binary is bundled. |
| Python and Node.js | Local execution | Separately installed runtimes retain their own licenses. |
| Browsing, speech and hosting providers | Research, narration and delivery | Their own terms, availability, credentials and permissions apply. Installing this skill does not authorize a new data transfer or public course audience. |

## Bundled fonts

The design system bundles unmodified font files in `assets/starter/production-source/fonts/`, each beside its complete license text. They are licensed under the [SIL Open Font License 1.1](https://openfontlicense.org), not Apache-2.0. The OFL permits bundling and redistribution with software, provided the license text accompanies the fonts and the fonts are not sold by themselves. None of these fonts declares a Reserved Font Name.

| Font | Files | Version and source | License file |
| --- | --- | --- | --- |
| Inter | Regular, Medium, SemiBold, Bold, ExtraBold | 4.001, [rsms/inter v4.1](https://github.com/rsms/inter/releases/tag/v4.1) `extras/ttf` | `Inter-OFL.txt` |
| Instrument Serif | Regular, Italic | 1.000, [google/fonts](https://github.com/google/fonts/tree/main/ofl/instrumentserif) | `InstrumentSerif-OFL.txt` |
| JetBrains Mono | Regular, Bold | 2.304, [JetBrains/JetBrainsMono v2.304](https://github.com/JetBrains/JetBrainsMono/releases/tag/v2.304) | `JetBrainsMono-OFL.txt` |

Rendered course frames are not font software; the OFL places no restriction on videos or images made with these fonts. Keep the license files with the fonts when copying a project. A replacement font chosen for a course needs its own recorded license before it is bundled or published.

## Other material

No employer logo or proprietary design document is bundled. The mechanical `--demo` world draws with the system sans-serif font; design-system worlds use the bundled fonts above. Source links are references, not redistribution permission. Review the actual source rights and audience before exporting or publishing a course. No employer endorsement or learner-effectiveness certification is implied.
