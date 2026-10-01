# Open Source Health Report

This report maps Sèo Trum / Auto_social against the common "Points of FAIL" style checks for free and open-source software projects.

Lower risk means the project is easier to build, review, fork, contribute to, and release.

## Snapshot

- Repository: `ROYCE-8425/Auto_social`
- License: MIT
- Upstream foundation: Javis OS, attributed in `NOTICE.md`
- Source control: Git with GitHub web viewer, issue templates, pull request template, and CI workflows
- Current tracked source size observed locally: about 32 MiB
- Local ignored demo archive observed: `demo_pack.tar.gz` is ignored and should not be released

## Score Summary

| Area | Status | Risk |
| --- | --- | --- |
| Source size | Tracked source is under 100 MiB. Avoid committing build artifacts or demo archives. | Low |
| Source control | Public GitHub-style workflow with web viewer, issue templates, PR template, CODEOWNERS, and CI. | Low |
| Build from source | Docker Compose, Python requirements, Ops `package.json`, GitHub Actions, and top-level `Makefile`. | Low |
| Bundling | Runtime dependencies are declared through package managers. Keep vendored browser assets/fonts documented. | Low |
| Libraries | Not a system library project; Python/Node dependencies are explicit. | Low |
| System install | `make install`, Docker Compose, and local setup scripts are available. No forced `/opt` or `/usr/local` install. | Low |
| Code oddities | `.gitattributes` normalizes line endings. Windows helper scripts are present but not required for Linux/Docker builds. | Low |
| Communication | GitHub Issues, issue templates, PR template, `SUPPORT.md`, `SECURITY.md`. | Low |
| Releases | `VERSION`, `CHANGELOG.md`, Docker publish workflow, and release process are present. | Low |
| History | Project is derived from Javis OS and discloses that relationship. | Known/acceptable |
| Licensing | Full MIT license is included; upstream attribution is in `NOTICE.md`. | Low |
| Documentation | README, Quickstart, docs folder, contribution, security, support, release, and checklist docs exist. | Low |

## Remaining Watch Items

These are not blockers, but they should be checked before every public submission:

1. Keep `NOTICE.md` accurate when code from Javis OS or third-party assets change.
2. Do not commit local runtime data, SQLite state, tokens, customer messages, phone numbers, or provider credentials.
3. Do not release ignored archives such as `demo_pack.tar.gz`.
4. Keep unfinished product features marked as `Coming soon` or `Needs config`; do not present placeholders as live provider behavior.
5. Prefer GitHub Releases and Docker images over manually attached archives.
6. Re-run the release checklist before tagging.

## Reviewer Evidence

Useful files for reviewers:

- [`README.md`](../README.md)
- [`README.en.md`](../README.en.md)
- [`LICENSE`](../LICENSE)
- [`NOTICE.md`](../NOTICE.md)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`SECURITY.md`](../SECURITY.md)
- [`SUPPORT.md`](../SUPPORT.md)
- [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md)
- [`CHANGELOG.md`](../CHANGELOG.md)
- [`docs/OPEN_SOURCE_CHECKLIST.md`](OPEN_SOURCE_CHECKLIST.md)
- [`docs/RELEASE_PROCESS.md`](RELEASE_PROCESS.md)
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## Practical Assessment

The project is not a "vaporware" repository: it has source code, build instructions, CI, licensing, attribution, contribution process, security policy, and release hygiene. The main open-source risk is not missing paperwork; it is accidentally shipping private runtime data or overstating unfinished provider integrations. Treat those as release gates.
