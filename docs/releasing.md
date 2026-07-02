# Installing and Releasing

## Install (users)

`idrac_ctl` is published to PyPI, so end users install it with pip:

```bash
pip install idrac_ctl
idrac_ctl --help
```

That pulls the package named `idrac_ctl` (defined in `setup.py`) and installs the
`idrac_ctl` console command (the `console_scripts` entry point in `setup.py`).

To try a checkout without publishing, install it from source:

```bash
git clone https://github.com/spyroot/idrac_ctl
cd idrac_ctl
pip install .
```

## Release (maintainers)

Releasing is: bump the version, build the distributions, and upload them to PyPI
with `twine`. The helper scripts in the repo root wrap this.

1. **Bump the version.** Edit `version=` in `setup.py` (single source of truth,
   e.g. `1.1.0`). Follow semver: patch for fixes, minor for new commands, major
   for breaking changes.

2. **Build the distributions** — source tarball + wheel:

   ```bash
   python setup.py sdist bdist_wheel
   ```

   `build_dist.sh` does this and also runs `check-manifest` (verifies the sdist
   includes everything tracked in git).

3. **Upload to PyPI** with twine (needs a PyPI API token in `~/.pypirc` or
   `TWINE_USERNAME`/`TWINE_PASSWORD`):

   ```bash
   twine upload dist/*
   ```

   `build_dist.sh` performs steps 2–3; `build_push.sh` is the dev shortcut
   (`rm dist/* && python setup.py sdist bdist_wheel && twine upload dist/*`).

4. **Tag the release** so the git history matches PyPI:

   ```bash
   git tag v$(python setup.py --version) && git push --tags
   ```

### Verify before uploading

Build and install into a throwaway env first (this is what `local_install.sh`
does) so a broken package never reaches PyPI:

```bash
conda create -n rel-test python=3.10 && conda activate rel-test
python setup.py sdist bdist_wheel && pip install dist/idrac_ctl-*.whl
idrac_ctl --help
```

`twine upload` is irreversible per version — a version number can't be reused on
PyPI. Verify locally, then upload.
