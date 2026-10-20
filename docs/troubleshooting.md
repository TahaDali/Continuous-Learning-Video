# Troubleshooting

| Symptom | Check and safe next step |
| --- | --- |
| Skill is not in the selector | Confirm the complete `continuous-learning-video` folder is under the active user or repository skills location. Check frontmatter and avoid duplicate old installations. Restart Codex if needed. |
| Missing canvas/native binary | Run locked `npm ci --prefix production-source --ignore-scripts` in the project; verify the OS/CPU is supported and rerun preflight. Do not substitute an unreviewed module path. |
| Missing FFmpeg codec | Preflight must find FFmpeg/FFprobe and libx264/AAC. Install a suitable build from a trusted distribution and review its licensing if redistributing binaries. |
| New project refuses to render | Expected until its actual world is authored. Use `--demo` only for a disposable mechanical tooling example. |
| Posting cannot be retrieved | Verify exact employer/vacancy through a supported route or supply dated text. General company research may continue; do not silently substitute a different job. |
| Speech interface/provider fails | Verify WordBoundary support and current provider availability. Preserve cached blocks and bounded retries; do not change provider or upload new text without applicable authorization. |
| Stage becomes stale | Use `workflow.py status`; update/review affected work and record from the changed stage. Do not edit fingerprints to bypass checks. |
| Prototype or caption validation fails | Repair the actual media/source/timing difference, rerender the affected lesson and refresh downstream evidence. Metadata alone cannot certify a prototype. |
| Player fails under file:// | Serve the actual export over HTTP with `production-source/serve.py --directory /absolute/export`. Preserve the intended hosting audience. |
| Transcript seek is slow | The player may need the active chapter in memory on a host without range support. Large chapters need more memory; MP4 download remains a fallback. A later manual pause should remain respected. |
| Hosting is unavailable | Supply the validated local export and state that hosted delivery is unfinished. Never invent a URL or broaden access silently. |
| Builder rejects an output | Choose a new location outside the repository and installed source. Review an existing installation before replacement. |
| Security issue or private data found | Follow SECURITY.md; keep details out of public issues and revoke any real exposed credential at its issuer. |
