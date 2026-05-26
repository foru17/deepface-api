# Versioning policy

`deepface-api` distinguishes between **three independent version axes**.
They are aligned by convention but evolve at different cadences.

| Axis | Where it lives | Format | Bumped by |
|---|---|---|---|
| **Package version** | `src/deepface_api/_version.py` | `MAJOR.MINOR.PATCH` (SemVer) | Maintainers cutting a release |
| **HTTP API contract version** | URL prefix `/api/vN` + `X-API-Version` header + `API_VERSION` constant in `api/v1/__init__.py` | A single integer (`1`, `2`, …) | Only when introducing a breaking HTTP contract change |
| **Docker image tag** | `ghcr.io/lloydzhou/deepface-api` | Derived from package version (`{version}`, `{major}.{minor}`, `{major}`, `latest`, `sha-xxxxxxx`) | Automated by `.github/workflows/docker.yml` on tag push |

You can introspect the running build at any time:

```bash
curl http://127.0.0.1:8008/api/version
# {
#   "package_version": "2.0.0",
#   "api_version": "1",
#   "api_versions": ["1"],
#   "build_sha": "abc1234",
#   "build_time": "2026-05-26T12:00:00Z"
# }
```

Every API response also carries:

- `X-API-Version: 1` — the contract served by that route
- `X-Request-ID: <hex>` — correlator for logs and bug reports

## SemVer in practice

We follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
for both the Python package and the HTTP API. The "public surface" we
make these promises about is:

- **HTTP**: routes documented under `/openapi.json`, including request
  / response schemas, status codes, and headers.
- **Python**: the names exported from `deepface_api.__init__`,
  `deepface_api.schemas`, and `deepface_api.config.Settings`.

Internal modules (`deepface_api.services.*`, `deepface_api.middleware`,
`deepface_api.exceptions`) are considered implementation details and
may change in minor releases. Pin to a `~=X.Y` range if you depend on
them.

### What counts as breaking (→ MAJOR)

- Removing or renaming a documented endpoint, query/path parameter, or
  response field.
- Changing the semantics of an existing field (e.g. units, enum values,
  null behavior).
- Changing a 2xx status code to non-2xx (or moving an endpoint from
  sync to long-polling/streaming).
- Dropping a previously supported Python version.
- Removing or renaming a configuration env var without a deprecation
  alias.

### What counts as a feature (→ MINOR)

- Adding a new endpoint.
- Adding **optional** request parameters with a backwards-compatible
  default.
- Adding **new** fields to a response (clients must ignore unknown
  fields — Pydantic models default to this).
- Adding a new Python version to the support matrix.
- Adding a new env var with a sensible default.

### What counts as a patch (→ PATCH)

- Bug fixes that restore documented behavior.
- Performance improvements with no observable contract change.
- Dependency bumps that don't change the public surface.
- Documentation, test, and tooling changes.

## HTTP API version lifecycle

The URL-prefix version (`/api/v1`) is bumped only when a change can't
be made backwards-compatibly within v1. This is independent of the
package version: v1 is expected to stay stable across many `2.x.y`
releases.

When introducing `/api/v2`:

1. Add `src/deepface_api/api/v2/` with the new router. Reuse handlers
   from v1 wherever the contract is unchanged.
2. Mount it in `main.create_app()` at `/api/v2` (canonical).
3. Update `API_VERSION` if the new version becomes the **default**, and
   extend `_LEGACY_PATHS` if needed.
4. Update `meta.version()` so `api_versions` advertises both.
5. Mark v1 endpoints as deprecated in OpenAPI (`deprecated=True`) and
   note the removal milestone in `CHANGELOG.md`.
6. Keep v1 running for the **deprecation window** (below).

### Deprecation window

- Newly deprecated HTTP API versions remain available for **at least 6
  months and at least one MAJOR release**, whichever is longer.
- Deprecated Python imports follow the same window and emit a
  `DeprecationWarning`.
- Configuration env vars are aliased for at least one MINOR release
  before removal (we already do this for legacy unprefixed forms like
  `SERVER_PORT` → `DEEPFACE_SERVER_PORT`).

Removal is always documented in `CHANGELOG.md` under a `### Removed`
heading.

## Release workflow

1. **Update `CHANGELOG.md`**: move items from `## [Unreleased]` to a
   new versioned section dated today.
2. **Bump `src/deepface_api/_version.py`** to match.
3. **Tag the commit**: `git tag -a v2.1.0 -m "v2.1.0" && git push --tags`.
4. CI takes over:
   - `release.yml` builds wheel + sdist, attaches them to a GitHub
     Release with auto-generated notes.
   - `docker.yml` builds and publishes multi-arch images to GHCR with
     all the relevant tags (`2.1.0`, `2.1`, `2`, `latest`).

For pre-releases (`v2.1.0-rc.1`), the workflows still publish, but the
`latest` tag is **not** moved.

## Image tag policy

| Tag | Stability | When to use |
|---|---|---|
| `latest` | Tracks default branch | Local dev / quick demos |
| `2`, `2.1`, `2.1.0` | Immutable once published | Production — pin to at least `2.1` |
| `sha-abc1234` | Immutable, every commit | Reproducing a specific commit |
| `2.1.0-gpu`, `latest-gpu` | Same policy + `-gpu` suffix | GPU runtime variant |

Production deployments **should pin to at least `MAJOR.MINOR`** (e.g.
`ghcr.io/lloydzhou/deepface-api:2.1`) so they pick up patch updates
automatically but never silently consume breaking changes.

## Pinning Python dependents

```toml
# pyproject.toml of a downstream service
dependencies = [
    "deepface-api ~= 2.0",   # any 2.x — recommended
    # or
    "deepface-api == 2.0.*", # equivalent
    # or, tighter
    "deepface-api >= 2.0,<2.1",
]
```

Avoid `deepface-api >=2.0` without an upper bound — that allows the
next major release to break you silently.
