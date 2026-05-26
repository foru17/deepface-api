# Contributing to deepface-api

Thanks for your interest in contributing! This guide is intentionally
short — open an issue if anything below is unclear.

## Code of conduct

By participating you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md). Be excellent to each other.

## Ways to contribute

- 🐛 File a clear, reproducible **bug report** (use the issue template).
- 💡 Propose an **enhancement** (use the feature-request template).
- 📚 Improve the **docs** — typos, clarifications, new examples.
- 🧪 Add **tests** for an edge case that isn't covered yet.
- 🛠️ Submit a **pull request** that closes a tagged `help wanted` issue.

## Development setup

```bash
git clone https://github.com/foru17/deepface-api.git
cd deepface-api
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,test]"
pre-commit install
```

You can now run the service three ways:

```bash
deepface-api                 # installed console script
python -m deepface_api       # module-mode
uvicorn deepface_api.main:app --reload
```

## Running the test suite

```bash
pytest                        # fast: ~26 tests, mocks ML stack
pytest --cov=deepface_api     # with coverage
pytest -m integration         # heavy tests (require deepface/retinaface installed)
```

The default suite is intentionally mock-based and runs in seconds. CI
runs it on Python 3.10, 3.11, and 3.12.

## Linting and formatting

```bash
ruff check src tests
ruff format src tests        # or: black src tests
mypy src/deepface_api        # advisory
```

`pre-commit` will run these automatically on `git commit`. Run
`pre-commit run --all-files` to format the whole tree.

## Pull request checklist

1. **One focused change per PR.** Refactors should not include feature
   work and vice versa.
2. **Tests.** Bug fixes need a regression test. New features need
   coverage of the happy path and the obvious failure modes.
3. **Docs.** Update `README.md`, `docs/`, or `CHANGELOG.md` when
   behavior, configuration, or deployment changes.
4. **Conventional-ish commit messages.** Use a short imperative summary
   line, e.g.:
   - `fix: reject empty multipart uploads`
   - `feat(analyze): expose include_emotion query parameter`
   - `docs: clarify Kubernetes readiness probe`
5. **CI must be green** before review.

## Release process (maintainers)

1. Update `CHANGELOG.md` — move items from `Unreleased` to a new
   versioned section dated today.
2. Bump `src/deepface_api/_version.py`.
3. Tag the commit: `git tag -a v2.1.0 -m "v2.1.0" && git push --tags`.
4. The `release.yml` workflow builds wheels and creates the GitHub
   release; `docker.yml` builds and pushes multi-arch images to GHCR.

## Reporting security issues

**Do not** open public issues for security vulnerabilities. Use GitHub
Security Advisories per [`SECURITY.md`](SECURITY.md).
