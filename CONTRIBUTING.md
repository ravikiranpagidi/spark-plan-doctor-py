# Contributing

Thanks for taking a look at `spark-plan-doctor-py`.

The project is intentionally small. A good contribution usually adds one rule, improves one parser path, or makes one output format easier to use.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m unittest discover -s tests
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m unittest discover -s tests
```

## Rule Guidelines

Rules should be:

- cheap to run
- explainable from the plan text
- conservative in wording
- backed by a small unit test
- written as a suggestion, not an automatic rewrite

Use stable rule IDs such as `SPD013`. Do not reuse an ID for a different behavior.

## Pull Request Checklist

- tests added or updated
- docs updated for user-facing behavior
- examples still read like a real engineer wrote them
- no secrets or customer-specific paths in fixtures
- no Spark action is introduced in the static inspection path
