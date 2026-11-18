# Two-Pass Cleanup Record

Review date: 2026-10-25

## Pass 1 — Candidate inventory

| Candidate | Purpose / tracking / references | Data or regeneration | Proposed action |
|---|---|---|---|
| `.env` | Ignored local connection/configuration; no source archive references | Contains private settings; not regenerable without operator values | Retain locally; exclude from archive |
| `.venv/`, `venv/` | Ignored Python environments; no application runtime dependency on their contents | Re-creatable, but currently useful local environments | Retain locally; exclude from archive |
| `instance/grand_haven_hotel.db`, `.backup` | Ignored local database and backup; not referenced by current normal MySQL configuration | Potentially valuable records | Retain locally; exclude from archive |
| `.git/` | Git metadata; contains uncommitted work context | Valuable local history/state | Retain; exclude from archive |
| `__pycache__/`, `.pytest_cache/` | Ignored Python/test-generated caches; no source/docs dependency | Fully regenerable | Remove after final tests where permitted; exclude from archive |
| `tests/_.code-search` | Untracked text output beginning with a query/results report; no references in source/docs | Regenerable search output | Remove after second-pass reference check |
| `tests/import uuid.py` | Untracked file with 272 lines; verified line-for-line duplicate of `app/services/reservation_service.py`; no source imports or docs references | Canonical implementation remains in app/services | Remove after second-pass reference check |
| `app/__init.py.phase4-backup` | Untracked application factory backup; contains prior CSRF exemption; no runtime references | Preserve as local recovery copy | Retain locally; exclude from archive |
| `tests/test_api_csrf.py` | Untracked canonical regression tests for CSRF behavior; collected by pytest | Required test source | Retain and include |

## Pass 2 — Independent reference and safety recheck

- Searched application, tests, SQL, and docs for the two scratch-file names; there are no references.
- Confirmed `tests/import uuid.py` has normalized line similarity `1.0` with the canonical reservation service. Removing the duplicate does not remove unique logic.
- Confirmed `.env`, virtual environments, database files/backups, Git metadata, and the app factory backup are retained locally, not deleted.
- Confirmed cache paths are ignored and have no imports or runtime role.
- Confirmed the CSRF test is useful, collected, and must ship.
- The final archive source list includes project source, canonical tests, SQL, docs, manifests, `.env.example`, and audit records; it will exclude credentials, local DBs/backups, Git metadata, virtual environments, caches, and recovery/scratch duplicates.

## Execution results

- Removed `__pycache__` directories, `tests/_.code-search`, and `tests/import uuid.py` after the second-pass checks.
- Attempted to remove `.pytest_cache`, but Windows denied access. The directory remains in the workspace and is excluded from the archive.
- Retained `.env`, `.venv/`, `venv/`, `instance/grand_haven_hotel.db`, `instance/grand_haven_hotel.db.backup`, `.git/`, and `app/__init.py.phase4-backup`.
- Post-cleanup verification: `26 passed, 627 warnings in 10.32s`; Python syntax parse passed for 41 files.
- Final ZIP archive creation and content inspection: pending.

## Follow-up cleanup review — 2026-10-25

### Pass 1 — Technical candidate review

| Candidate | Tracking / references / value | Decision |
|---|---|---|
| `.env` | Ignored local MySQL/secret configuration; needed only for local operator use; private values | Retain locally; exclude from archive |
| `.venv/`, `venv/` | Ignored Python environments; useful existing environments; not needed in source package | Retain locally; exclude from archive |
| `instance/grand_haven_hotel.db` and `.backup` | Ignored local SQLite files with potential user data; not the runtime MySQL store | Retain; exclude from archive |
| `.git/` and staged/unstaged work | Unborn repo with preexisting staged additions and unstaged edits | Preserve; exclude from archive |
| `.codex/environments/environment.toml` | Untracked local setup configuration; no submission runtime reference | Preserve locally; exclude from archive |
| `app/__init.py.phase4-backup` | Untracked recovery copy; no active import; valuable recovery content | Retain locally; exclude from archive |
| Existing `GrandHavenHotel_submission.zip` | Preexisting 98-entry archive; must not be overwritten | Retain; exclude from new archive |
| `__pycache__/` and `.pyc` | Generated, ignored bytecode; imports do not depend on them | Safe to remove after pass 2; regenerable |
| `.pytest_cache/` | Generated, ignored test cache; pytest works with `-p no:cacheprovider`; prior deletion was denied by Windows | Retain if access remains denied; exclude from archive |

### Pass 2 — Independent safety recheck

- Rechecked source/test/config/docs references: runtime imports use `.py` source; no project code reads `__pycache__` or `.pyc` files.
- Git ignore rules confirm caches, environments, local database, and `.env` are excluded from tracking. The local DB files and secret config contain potentially valuable/private information and will not be opened or deleted during cleanup.
- Reconfirmed project code, templates, static files, SQL scripts, tests, documentation, dependency manifest, `.env.example`, and `.gitignore` are required or useful to run, test, install, or understand the package.
- The new archive will use an explicit source allowlist and distinct filename to exclude all local/private and recovery artifacts. The prior archive and separate backup are not targets of cleanup.

### Follow-up execution

- Removed 8 generated `__pycache__` directories from the project source/test tree. A recursive listing encountered the already-known access-denied `.pytest_cache`; that cache remains and was excluded from the archive. No force/permission changes were attempted.
- Extracted-package test initially found that `TestingConfig` inherited its `SECRET_KEY` from the developer `.env`; that secret is properly excluded from the package. Fixed the test-only configuration, added an assertion, rebuilt the final archive, and verified the extracted suite: **29 passed, zero warnings**.
- Removed the obsolete interim archive `GrandHavenHotel_submission_20261025_verified.zip` after verifying it was generated during this audit, contained no unique user data, and was superseded by the final archive. The original `GrandHavenHotel_submission.zip` was retained.
- Final archive inspection after all documentation updates: `GrandHavenHotel_submission_20261025_final.zip`, 102 entries, CRC passed; required files present; `.env`, `.git`, `.venv`, `venv`, `instance`, `.codex`, DB files, and bytecode absent. The extracted package test passed 29 tests with zero warnings.
- `.pytest_cache` and local environments/databases remain retained. No separate backup folder was accessed or modified.
