# Release checklist

The maintainer approves the exact release commit and its artifact before publication.

- [ ] One root SKILL.md, correct name, complete references and UI metadata.
- [ ] Reviewed payload manifest, explicit version and consistent ownership/license notices.
- [ ] Supplied expression and public examples have a recorded origin, rights basis and required attribution. Narration has a service-specific distribution basis; code licenses are not treated as audio permission. Review all served branches and old releases, not only the skill ZIP.
- [ ] No original transcripts, private source documents, course media, hosting IDs or credentials in source or ZIP.
- [ ] History/current tree/final archive secret scans pass; prior sensitive reports stay private.
- [ ] Fresh locked dependency installation, resource check, render/audit/full decode, Python regressions and player contracts pass.
- [ ] Final ZIP integrity, per-file checksums and reproducible bytes verified from an isolated committed snapshot.
- [ ] Owner acceptance is recorded accurately; unsupported perceptual/platform/learning claims are absent.
- [ ] PR and CI gates, force-push/deletion controls, dependency alerts, secret protection and private reporting are configured and read back.
- [ ] Main, version tag, changelog, release notes and payload identify the same reviewed source.
- [ ] Public repository permission is explicitly authorized. Course audiences remain a separate decision.

Keep private review artifacts outside the public repository. Do not rewrite history, forge author/reviewer evidence or silently expand access to meet this checklist.
