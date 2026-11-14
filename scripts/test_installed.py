"""Run reference tests against an installed wheel, outside the source tree."""
import argparse
import importlib
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--sdist', required=True, type=Path)
parser.add_argument('--module', required=True)
parser.add_argument('--distribution', required=True)
args = parser.parse_args()
module = importlib.import_module(args.module)
origin = Path(module.__file__).resolve()
prefix = Path(sys.prefix).resolve()
if not origin.is_relative_to(prefix):
    raise RuntimeError(f'Expected installed wheel under {prefix}, got {origin}')
print(f'{args.distribution} {importlib.metadata.version(args.distribution)}: {origin}', flush=True)
with tempfile.TemporaryDirectory(prefix='installed-wheel-') as tmp:
    root = Path(tmp).resolve()
    with tarfile.open(args.sdist) as archive:
        for item in archive.getmembers():
            target = (root / item.name).resolve()
            if not target.is_relative_to(root) or not (item.isfile() or item.isdir()):
                raise RuntimeError(f'Unsafe source archive member: {item.name}')
            if item.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(item) as source, target.open('wb') as dest:
                    shutil.copyfileobj(source, dest)
    projects = list(root.glob('*/pyproject.toml'))
    if len(projects) != 1:
        raise RuntimeError('Expected one source project')
    source = projects[0].parent
    tests = root / 'isolated-tests'
    shutil.copytree(source / 'tests', tests / 'tests')
    shutil.copytree(source / 'data', tests / 'data')
    # Only tests and fixtures are copied; the candidate package source is absent.
    result = subprocess.run([sys.executable, '-I', '-m', 'pytest',
                             str(tests / 'tests'), '--import-mode=importlib', '-q'],
                            cwd=tests, check=False)
    raise SystemExit(result.returncode)
