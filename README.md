# py-MuSiC

Python reconstruction of a **subset** of MuSiC, following the discovery, preregistration and reference-validation workflow in [omicverse-rebuildr](https://github.com/omicverse/omicverse-rebuildr).

Reference construction and default weighted-NNLS music_prop path. No ct.cov=TRUE, centered/normalized variants, recursive tree decomposition or MuSiC2.

## Install and test

Version **0.1.0** is available on [PyPI](https://pypi.org/project/py-music-omicverse/0.1.0/):

```bash
python -m pip install "py-music-omicverse==0.1.0"
```

For development and source-checkout tests:

```bash
python -m pip install ".[test]"
python -m pytest -q
```

## Usage and function map

See [the executed tutorial](examples/tutorial_fixture.ipynb), [R-to-Python parameter dictionary](examples/function_by_function_R_parity.ipynb), and [complete upstream export audit](AUDIT.md).
Inputs, orientations and unsupported modes are documented in function docstrings. No R process is used at runtime.

## Reproduce the R oracle

```bash
git clone https://github.com/xuranw/MuSiC.git ../MuSiC-ref
git -C ../MuSiC-ref checkout f21fe67f5670d5e9fca0ad7550abaae3423eb59c
Rscript tests/reference.R ../MuSiC-ref
python -m pytest -q
```

The runner sources the pinned upstream functions, not a rewritten R approximation. RUVSeq S4 registration is intercepted to execute only matrix methods. SPARK sparse sum/mean helpers are supplied by Matrix, with unchanged statistical functions. MuSiC and muscat functions are sourced with their R dependencies loaded. muscat's source declares R >=4.6; this selected function subset was executed on R 4.5.2, not installed as the full package.

muscat's public fixture additionally uses `Rscript tests/public_reference.R ../muscat-ref`.
All other primary fixtures are synthetic and do not establish biological accuracy. Numerical gates were committed before implementation and have not been widened.

## Validation and limitations

4 focused tests passed locally without skips. See [reconstruction report](RECONSTRUCTION_REPORT.md) for scope and remaining release checks. This is fixture-level equivalence, not full-domain or full-package equivalence. Runtime objects and failure messages are Python-native.

## Citation and license

Upstream [MuSiC](https://github.com/xuranw/MuSiC) at `f21fe67f5670d5e9fca0ad7550abaae3423eb59c`; see ATTRIBUTION.md for upstream authors and package citation context, and LICENSE for terms.

## Release validation

The PyPI distribution is `py-music-omicverse`; the import remains `pymusic_deconv`. On 2026-11-14, the actual PyPI 0.1.0 package was installed in a new Python 3.12 environment and validated against the reference fixtures from its published source archive: **4 passed, no skips**. Tests ran outside the source checkout and imports came from site-packages. See [release workflow](RELEASE.md) for installed-wheel validation and manual Trusted Publishing.
