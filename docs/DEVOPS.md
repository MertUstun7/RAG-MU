# CI/CD and operations

This repository uses GitHub Actions for continuous integration and continuous delivery.
The delivery target is GitHub Container Registry (GHCR), so no cloud-provider-specific
credentials are required. Runtime deployment remains provider-neutral.

## Pipelines

| Workflow | Trigger | Result |
| --- | --- | --- |
| `CI` | Pull requests and pushes to `main` | Ruff lint/format, Python compilation, Compose validation, and a PR container build/health smoke test |
| `CD - Publish Container` | Pushes to `main`, SemVer tags, or manual runs | Builds a `linux/amd64` image, attaches SBOM/provenance, and publishes it to GHCR |
| `CodeQL` | Pull requests, `main`, weekly schedule, or manual runs | Performs Python security analysis |
| Dependabot | Weekly | Proposes GitHub Actions, Python, and Docker dependency updates |

The container workflow publishes these tags:

- `edge` for the latest successful build from `main`
- `sha-<commit>` for immutable commit deployments
- `1.2.3` and `1.2` for a Git tag such as `v1.2.3`
- `latest` only for a versioned release tag

## Local validation

```powershell
python -m pip install --requirement requirements-dev.txt
ruff check .
ruff format --check .
python -m compileall -q -x '(chroma_db|temp_uploads)' .
docker compose --env-file .env.example config --quiet
docker build --check .
```

Run `ruff check --fix .` and `ruff format .` before opening a pull request when the
quality checks report fixable issues.

## Repository settings

1. In GitHub, keep Actions enabled with read access to repository contents and write access
   to packages. The CD workflow authenticates to GHCR with the built-in `GITHUB_TOKEN`.
2. Protect `main` and require `Quality`, `Container`, and `Analyze Python` before merging.
3. If the repository is private, ensure the target server can authenticate to GHCR with a
   token that has `read:packages` permission.

No application secrets are stored in GitHub for image publishing. Keep deployment values in
the target platform's secret store and never commit `.env`.

The application image runs as UID/GID `10001`. Existing named volumes created by the previous
root image may need a one-time ownership migration before the first upgrade:

```powershell
docker compose run --rm --no-deps --user root app sh -c "chown -R 10001:10001 /app/chroma_db /app/temp_uploads /home/ragmu/.cache/huggingface"
```

## Release

Create a SemVer tag to produce a release image:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

The published image will be `ghcr.io/mertustun7/rag-mu:1.0.0`.

## Deploy or roll back

On a Docker host containing this repository and a production `.env`, set `APP_IMAGE` to an
immutable release or commit tag. Then pull and start the services without rebuilding:

```powershell
$env:APP_IMAGE = "ghcr.io/mertustun7/rag-mu:1.0.0"
docker compose pull
docker compose up -d --no-build
docker compose ps
```

Roll back by repeating the same commands with the previous version tag. For Linux shells, use
`export APP_IMAGE=...` instead of the PowerShell assignment. The actual host rollout is not
automatic until a deployment target and its access policy are selected; the CD pipeline stops
at a deployable, versioned registry artifact.
