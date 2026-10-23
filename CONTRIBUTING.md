# Contributing to La Citadelle

**English** | [Français](./CONTRIBUTING.fr.md)

## Prerequisites

- Python 3.10 or later.
- Git.
- About 3 GB of free disk space for the runtime and model.

## Clone and setup

```powershell
git clone https://github.com/Binwinwinw/lacitadelle.git
cd lacitadelle
python dev/tools/bootstrap.py
```

The bootstrap downloads and verifies the required assets. It places the runtime at `dist/llamafile.exe` on Windows and the Qwen3 GGUF model at `dev/tools/vendor/llamafile/`. See [BOOTSTRAP_CONTRACT.md](./dev/tools/BOOTSTRAP_CONTRACT.md) for validation, download, and repair behavior.

## Run tests

```powershell
python -m pytest
```

The test suite currently contains 73 tests. The focused HTTP helper checks can also be run with:

```powershell
python dev/tests/test_http_helpers.py
```

## Run in development

On Windows, run `lancer.bat` to start the model server and web proxy. The model server listens on port 8080; the authenticated web proxy listens on port 8081.

To start the proxy manually, first start the llamafile model server on `127.0.0.1:8080`, then run:

```powershell
python dev/tools/login_server.py
```

## Generate the distribution archive

```powershell
python -B dev/tools/creer_archive.py
```

This creates `lacitadelle-distribution.zip` in the repository root. The archive is published as an asset of a GitHub release.

## Repository structure

- `dev/tools/` — Python application and distribution tools.
- `dev/tests/` — pytest suite (73 tests).
- `dev/docs/` — architecture, contracts, product scope, and project journals.
- `.memory/` — project decisions and agent instructions.
- `AGENTS.md` — agent workflow and repository rules.
- `README.md` / `README.fr.md` — user guides.
- `CONTRIBUTING.md` / `CONTRIBUTING.fr.md` — contributor guides.

## Reference documentation

- [AGENTS.md](./AGENTS.md)
- [.memory/decisions.md](./.memory/decisions.md)
- [ARCHITECTURE.md](./dev/docs/ARCHITECTURE.md)
- [OBJECTIF.md](./dev/docs/OBJECTIF.md)

## Reporting bugs

Open a [GitHub issue](https://github.com/Binwinwinw/lacitadelle/issues) and include the application version, operating system, steps to reproduce, expected result, and observed result. Do not include passwords, session cookies, or other secrets.
