# PyPI Release

Build locally:

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

Upload to TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
```

Then upload to PyPI:

```bash
python -m twine upload dist/*
```

Before release:

- run tests
- update `CHANGELOG.md`
- confirm README examples still match the API
- tag the release in GitHub
