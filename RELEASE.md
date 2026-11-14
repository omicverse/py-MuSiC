# Release workflow

Distribution: `py-music-omicverse`. Python import: `pymusic_deconv`. Released version: `0.1.0`.
These names intentionally differ. Version 0.1.0 was published on 2026-11-14 and verified by installing the actual PyPI package in a fresh environment: 4 reference tests passed with no skips.

The first-publication procedure below records the bootstrap setup. For a later release, first update and validate a new version; do not dispatch 0.1.0 again. PyPI release files are not overwritten.

## Validation

`python -m build` produces a source archive and builds the wheel from that archive.
The source archive includes reference fixtures, R runners, attribution and scope documentation.
CI installs the wheel and executes the existing reference tests outside the checkout:

```bash
python -m pip install build twine
python -m build
python -m twine check --strict dist/*
python -m pip install dist/*.whl pytest
python -m pip check
python -I scripts/test_installed.py --sdist dist/*.tar.gz --module pymusic_deconv --distribution py-music-omicverse
```

## First publication

1. Review and merge the implementation and release-preparation changes into `main`.
2. In the intended PyPI account, configure a pending Trusted Publisher:
   project `py-music-omicverse`, GitHub owner `omicverse`, repository `py-MuSiC`,
   workflow `publish.yml`, environment `pypi`.
3. Configure the corresponding GitHub `pypi` environment. GitHub repository
   access alone does not establish PyPI project ownership. Do not share tokens in issues.
4. Explicitly dispatch **Publish to PyPI** on `main`, with version `0.1.0`.
   Pushes, pull requests and tags do not trigger publication. The workflow checks
   the version, rebuilds and tests distributions before publishing via OIDC.
5. In a new environment, install `py-music-omicverse==0.1.0` from PyPI, verify the
   downloaded artifact and rerun the reference tests. Only then update OmicVerse
   installation hints and tested version pins.

A successful build is not a public release. No full-package R equivalence or
biological accuracy claim is added by these packaging checks.
