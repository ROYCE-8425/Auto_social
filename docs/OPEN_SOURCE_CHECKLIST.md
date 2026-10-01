# Open Source Release Checklist

Use this checklist before publishing, releasing, demoing, or submitting Sèo Trum / Auto_social to an open-source contest.

## Attribution and License

- [ ] `LICENSE` is present and keeps the MIT notice for both upstream Javis OS and Sèo Trum extensions.
- [ ] `NOTICE.md` clearly states that the project is built on Javis OS and lists the new Sèo Trum business layer.
- [ ] `README.md` links to `LICENSE`, `NOTICE.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md`.
- [ ] `README.md` links to `SUPPORT.md`, `docs/RELEASE_PROCESS.md`, and `docs/OPEN_SOURCE_HEALTH.md`.
- [ ] The project is not described as written fully from scratch if upstream Javis OS code is still present.

## Secrets and Private Data

- [ ] `git status --short` shows no accidental runtime files.
- [ ] `git ls-files` does not include `.env`, `page_tokens.json`, `settings.json`, `server/.secret_key`, `server/.hub_token`, `*.sqlite3`, `*.db`, `usage-events.jsonl`, or real inbox/customer data.
- [ ] Demo screenshots and videos hide tokens, page IDs if sensitive, phone numbers, customer names, and private messages.
- [ ] Sample Brand Kits and datasets are either synthetic, public, or approved for publication.

## Build and Test

- [ ] Backend tests relevant to the changed area have run.
- [ ] `ops` builds successfully when frontend files changed.
- [ ] Docker instructions still match the current compose files.
- [ ] `make install`, `make build`, and `make test` still match the documented local workflow.
- [ ] Public landing page, `/ops`, and `/app` responsibilities are described correctly.

## Community Hygiene

- [ ] Issue templates warn users not to paste secrets.
- [ ] Pull request template asks contributors to confirm secret checks.
- [ ] `SECURITY.md` explains private vulnerability reporting.
- [ ] `SUPPORT.md` explains where to ask questions, report bugs, request features, and avoid leaking secrets.
- [ ] `docs/RELEASE_PROCESS.md` describes versioning, tagging, and release artifacts.
- [ ] `CONTRIBUTING.md` explains the fork and PR workflow.
