# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| `main` branch and the latest `2.x` release | ✅ |
| `1.x` | security fixes only, best-effort |
| Anything older | ❌ |

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Use [GitHub Security Advisories](https://github.com/lloydzhou/deepface-api/security/advisories/new)
to report privately. Include:

- Affected endpoint(s) or component(s)
- Reproduction steps (with the smallest payload that triggers the issue)
- Impact assessment (confidentiality / integrity / availability)
- Suggested remediation, if any

Maintainers will acknowledge valid reports within **5 business days**
and provide status updates during triage and remediation. We follow a
**coordinated disclosure** model: please give us a reasonable window
(typically 30–90 days) to ship a fix before public disclosure.

## Security model and best practices for deployments

`deepface-api` is intended to run behind a reverse proxy or API
gateway. The defaults are designed for a trusted internal network; if
you expose it to the public internet, consider:

- **Authentication and authorization** at the proxy layer
  (`Authorization: Bearer …`, OIDC, mTLS, etc.).
- **Rate limiting** — face inference is CPU/GPU-bound; an unauthenticated
  endpoint is trivially DOS-able.
- **Upload size limits** beyond `DEEPFACE_MAX_UPLOAD_SIZE_MB` (e.g. an
  NGINX `client_max_body_size`).
- **Request timeouts** to bound model execution time.
- **TLS termination** at the proxy.
- **Tight CORS origins** — set `DEEPFACE_CORS_ORIGINS` to the explicit
  list of domains you allow; do not leave it as `*` in production.
- **Logging hygiene** — do not log raw image bytes or PII.
- **Keep dependencies patched**, especially TensorFlow, OpenCV, and
  FastAPI. Dependabot PRs land weekly; review and merge them.
- **Run as non-root** — the official Docker image does this already
  (`appuser` / uid 10001).
- **Disable docs in production** if the endpoints are not meant to be
  publicly browsable: `DEEPFACE_ENABLE_DOCS=false`.

## Supply chain

- Docker images are built reproducibly in GitHub Actions and pushed to
  GHCR with SBOM and SLSA build provenance attestations.
- Python releases are built via the `release.yml` workflow from a
  signed tag and uploaded to the GitHub release assets.

## Out of scope

- Vulnerabilities in unreleased branches or experimental features.
- Issues that require physical access to the host.
- Issues in third-party services that integrate with this project
  unless the integration code itself is at fault.
