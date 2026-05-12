# Rules

Rule IDs are stable. If a rule changes meaning, add a new ID instead of reusing the old one.

## SPD001 Large shuffle detected

Looks for multiple `Exchange` operators. Shuffles are normal in Spark, but several in one plan can indicate expensive joins or aggregations.

## SPD002 Cartesian or nested-loop join signal

Looks for `CartesianProduct` or `BroadcastNestedLoopJoin`. This can be legitimate, but it often means a join condition is missing or weak.

## SPD003 Sort-merge join worth reviewing

Looks for `SortMergeJoin` without a broadcast join signal. This is a conservative info-level check because broadcast is only safe when one side is genuinely small.

## SPD004 No partition-pruning signal found

Looks for empty `PartitionFilters`. If the table is partitioned, this may read more partitions than needed.

## SPD005 Python UDF in plan

Looks for `BatchEvalPython`, `ArrowEvalPython`, or `PythonUDF`. Native Spark SQL functions are often easier for Catalyst to optimize.

## SPD006 Repeated scan of the same relation

Looks for the same scanned relation appearing more than once in a plan.

## SPD007 Full scan signal

Looks for both empty partition filters and empty pushed filters.

## SPD008 Many sort stages

Looks for several `Sort` operators.

## SPD009 Adaptive Query Execution disabled

Uses Spark config when available.

## SPD010 Plan hash changed from baseline

Compares the current plan hash with a supplied baseline hash.

## SPD011 Many shuffle exchanges in one plan

A stronger follow-up for plans with a high number of exchanges.

## SPD012 Very wide projection

Looks for a `Project` node with many referenced columns.
