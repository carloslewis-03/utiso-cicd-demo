# Secure CI/CD Pipeline Demo

A small Python (Flask) JSON API that exists to demonstrate a **secure CI/CD
pipeline built with GitHub Actions**. The application is deliberately minimal —
the value of this repository is the pipeline that tests, scans, builds, and
publishes it.

---

## What the application is

A two-endpoint API served by Gunicorn:

| Endpoint    | Purpose                                          |
|-------------|--------------------------------------------------|
| `GET /`     | Returns a small JSON status payload              |
| `GET /healthz` | Health probe used by the container `HEALTHCHECK` |

Source lives in `app/`, tests in `tests/`, and the container definition in
`Dockerfile`.

---

## How the pipeline works

There are two workflows in `.github/workflows/`.

### 1. `ci-cd.yml` — the main pipeline

It runs on every push and pull request to `main`, in three stages:

1. **Lint & Test** — installs dependencies, lints with `ruff`, and runs the
   `pytest` unit tests. If the code is broken, nothing downstream runs.
2. **Security Scans** (runs in parallel with the tests)
   - **Gitleaks** scans the code and full git history for committed secrets.
   - **pip-audit** audits Python dependencies for known vulnerabilities (CVEs).
3. **Build, Scan & Publish** — only starts if **both** stages above pass:
   - Builds the container image.
   - **Trivy** scans the built image for OS and library vulnerabilities. Results
     are uploaded to the **Security** tab, and a second Trivy step **fails the
     build if any fixable `CRITICAL` vulnerability is found** — so a vulnerable
     image cannot be published.
   - On a push to `main`, logs in to the GitHub Container Registry (GHCR) and
     **publishes the image** (tagged with both the commit SHA and `latest`).
     This publish step is the "deploy."

### 2. `codeql.yml` — static analysis (SAST)

GitHub **CodeQL** reads the source code and reports security issues and bug
patterns under **Security → Code scanning**. It runs on push, on pull requests,
and weekly on a schedule.

```
push / PR to main
      │
      ├── Lint & Test ─────────────┐
      │                            ├──► Build → Trivy image scan → (gate) → Publish to GHCR
      ├── Security Scans ──────────┘
      │
      └── CodeQL (separate workflow) ──► Security tab
```

---

## Where the published image lives

After a successful run on `main`, the image is available at:

```
ghcr.io/<your-github-username>/utiso-cicd-demo:latest
```

Pull and run it locally (Docker required only if you want to run it yourself —
the pipeline builds it for you in the cloud):

```bash
docker pull ghcr.io/<your-github-username>/utiso-cicd-demo:latest
docker run --rm -p 8080:8080 ghcr.io/<your-github-username>/utiso-cicd-demo:latest
# then visit http://localhost:8080/  and  http://localhost:8080/healthz
```

---

## How to reproduce / run the tests locally (optional)

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
pytest -q
python app/main.py        # serves on http://localhost:8080
```

---

## Security choices and why

| Control | Where | Why |
|---|---|---|
| **Least-privilege `GITHUB_TOKEN`** | both workflows | Each workflow defaults to `contents: read`; write scopes (`packages`, `security-events`) are granted only to the one job that needs them. Limits blast radius if a step is compromised. |
| **Secret scanning (Gitleaks)** | `ci-cd.yml` | Catches credentials accidentally committed to code or history — a common, high-impact mistake. |
| **Dependency audit (pip-audit)** | `ci-cd.yml` | Flags known-vulnerable Python packages (software composition analysis). |
| **Container image scan (Trivy)** | `ci-cd.yml` | The image inherits OS/library packages from its base; Trivy finds known CVEs and **gates publishing** on critical ones. |
| **SAST (CodeQL)** | `codeql.yml` | Finds vulnerabilities in the code we wrote, not just in dependencies. |
| **Non-root container user** | `Dockerfile` | If the app is compromised, the attacker isn't root inside the container. |
| **Slim, official base image** | `Dockerfile` | Fewer packages = smaller attack surface and fewer CVEs to patch. |
| **Deploy gated on tests + scans** | `ci-cd.yml` (`needs:`) | Nothing is published unless quality and security checks pass first. |

### Hardening I would add next

- **Pin every action to a full commit SHA** (not a moving tag like `@v4` or
  `@master`) and keep them current with **Dependabot**, to defend against a
  compromised or retagged third-party action.
- **Enable branch protection** on `main` (require PRs, require these checks to
  pass, require review) so the pipeline can't be bypassed.
- **Turn on GitHub's native secret scanning + push protection** and
  **Dependabot alerts/updates** in repository settings.
- **Sign and attest the image** (e.g. Cosign / build provenance) so consumers
  can verify what was published.
- **Promote pip-audit and the full Trivy result set from "report" to "blocking"**
  once a triage/exception process exists.

---

## Repository layout

```
.
├── app/                      # Flask application
│   ├── __init__.py
│   └── main.py
├── tests/                    # pytest unit tests
│   └── test_main.py
├── .github/workflows/
│   ├── ci-cd.yml             # test + security + build/scan/publish
│   └── codeql.yml            # CodeQL SAST
├── Dockerfile                # hardened container build
├── requirements.txt          # runtime dependencies
├── requirements-dev.txt      # test/lint dependencies
└── pyproject.toml            # pytest + ruff config
```
