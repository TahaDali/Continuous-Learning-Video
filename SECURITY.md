# Security policy

## Supported versions

Security maintenance targets the latest 1.x release. Use a current release and its exact dependency lock. Support is best effort; no fixed response-time guarantee is made.

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/TahaDali/Continuous-Learning-Video/security/advisories/new). Include the affected version, impact and a minimal fictional reproduction. Do not open a public issue containing an exploit, secret, private source document or course identity. If GitHub does not offer the private form, open an issue requesting a private reporting channel without describing the vulnerability or sensitive material.

Never submit a real credential as a test. Revoke exposed credentials at their issuer; removing a file does not restore secrecy. The maintainer will coordinate any public advisory after assessing the issue.

## Trust boundaries

Skill instructions do not grant extra access or service consent. Research pages, supplied documents and project code are untrusted input. Review unfamiliar scripts and dependencies before execution, preferably in an isolated workspace without unnecessary credentials. Renderer source discovery and geometric/media validation are not a sandbox.

Release artifacts use an explicit payload manifest and per-file hashes. Verify their source and checksum; a checksum proves byte identity, not safety. Review exported text, URLs, media and rights before upload. Preserve the intended course audience independently of this public repository.
