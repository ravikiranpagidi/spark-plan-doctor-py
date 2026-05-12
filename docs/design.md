# Design Notes

`spark-plan-doctor-py` should stay small and predictable.

## Principles

- Static inspection first.
- No Spark action in the default path.
- Findings should include evidence.
- Recommendations should be safe and reviewable.
- Agent output should summarize facts, not pretend to know business intent.
- Delta output should be easy to query with SQL.

## Non-Goals

- automatic query rewrite
- replacing Spark UI
- full runtime profiling
- becoming a generic logger
- requiring an LLM key

## Extension Points

- add new rules in `rules.py`
- improve parsing in `parser.py`
- add new output sinks in `writers.py`
- add more SQL views in `ai_assets.py`
